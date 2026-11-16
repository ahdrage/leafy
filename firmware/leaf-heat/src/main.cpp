#include "control.hpp"
#include "telemetry.hpp"
#if __has_include("settings.hpp")
#include "settings.hpp"
#else
#include "settings.example.hpp"
#endif
#include <atomic>
#include <cstdio>
#include <cstring>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "driver/twai.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_pm.h"
#include "esp_rom_sys.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "nvs_flash.h"
#ifndef LEAF_CAN_LISTEN_ONLY
#define LEAF_CAN_LISTEN_ONLY false
#endif
static_assert(!(LEAF_CAN_LISTEN_ONLY && LEAF_CAN_WRITE_ENABLED),
              "Receive-only diagnostics must not enable CAN writes");

#ifndef LEAF_TELEMETRY_ENABLED
#define LEAF_TELEMETRY_ENABLED true
#endif

static const char* TAG="leaf";
static constexpr gpio_num_t STB=GPIO_NUM_1, TX=GPIO_NUM_4, RX=GPIO_NUM_5;
static uint64_t now_ms(){return esp_timer_get_time()/1000;}
struct Request{bool on;uint64_t expires_ms;};
static QueueHandle_t requests;
static std::atomic<bool> busy{false},heat_requested{false},battery_ok{false};
static std::atomic<int> vpwr_mv{0},last_error{0},auto_off_seconds{-1};
static bool can_started=false;
static leaf::Retry retry;
static portMUX_TYPE retry_mux=portMUX_INITIALIZER_UNLOCKED;
static std::atomic<bool> online{false};
static esp_timer_handle_t reconnect_timer;
static adc_oneshot_unit_handle_t adc;
static adc_cali_handle_t calibration=nullptr;
#if LEAF_CAN_LISTEN_ONLY
static std::atomic<bool> listen_running{false};
static std::atomic<unsigned> listen_frames{0},listen_last_id{0},listen_bus_errors{0},listen_dropped{0};
static std::atomic<int> listen_error{0};
#endif

// One task owns both CAN modes. HTTP only reads the protected telemetry snapshot.
static leaf::BatteryTelemetry telemetry;
static portMUX_TYPE telemetry_mux=portMUX_INITIALIZER_UNLOCKED;
static std::atomic<int> telemetry_error{0};
#if LEAF_TELEMETRY_ENABLED && !LEAF_CAN_LISTEN_ONLY
static bool passive_started=false;
static uint64_t passive_due=0,passive_end=0;
static void passive_stop(){
 if(!passive_started)return;
 gpio_set_level(STB,1);twai_stop();twai_driver_uninstall();passive_started=false;
}
static void telemetry_drain(){
 twai_message_t m{};
 for(unsigned i=0;i<128;i++){
  const auto err=twai_receive(&m,0);
  if(err==ESP_ERR_TIMEOUT)break;
  if(err!=ESP_OK){telemetry_error=err;passive_stop();break;}
  const auto at=now_ms();
  portENTER_CRITICAL(&telemetry_mux);
  telemetry.receive(m.identifier,m.data,m.data_length_code,m.extd,m.rtr,at);
  portEXIT_CRITICAL(&telemetry_mux);
 }
}
static void passive_tick(){
 if(can_started)return;
 const auto now=now_ms();
 if(passive_started){
  if(now>=passive_end){passive_stop();return;}
  telemetry_drain();return;
 }
 if(now<passive_due)return;
 passive_due=now+60000; // Never wake the car to obtain a reading.
 gpio_set_level(STB,1);
 twai_general_config_t g=TWAI_GENERAL_CONFIG_DEFAULT(TX,RX,TWAI_MODE_LISTEN_ONLY);
 g.tx_queue_len=0;g.rx_queue_len=128;
 twai_timing_config_t timing=TWAI_TIMING_CONFIG_500KBITS();
 twai_filter_config_t filter=TWAI_FILTER_CONFIG_ACCEPT_ALL();
 auto err=twai_driver_install(&g,&timing,&filter);
 if(err!=ESP_OK){telemetry_error=err;return;}
 err=twai_start();
 if(err!=ESP_OK){twai_driver_uninstall();telemetry_error=err;return;}
 passive_started=true;passive_end=now+1500;telemetry_error=ESP_OK;
 gpio_set_level(STB,0);esp_rom_delay_us(100);
}
#endif

static void can_stop(){
 gpio_set_level(STB,1);
 if(can_started){twai_stop();twai_driver_uninstall();can_started=false;}
}
static bool can_send(const leaf::Frame& f){
 if(!LEAF_CAN_WRITE_ENABLED)return false;
#if LEAF_TELEMETRY_ENABLED && !LEAF_CAN_LISTEN_ONLY
 passive_stop(); // Commands preempt the non-transmitting sampling window.
#endif
 if(!can_started){
  twai_general_config_t g=TWAI_GENERAL_CONFIG_DEFAULT(TX,RX,TWAI_MODE_NORMAL);
  g.tx_queue_len=0;g.rx_queue_len=128;
  twai_timing_config_t t=TWAI_TIMING_CONFIG_500KBITS();twai_filter_config_t filter=TWAI_FILTER_CONFIG_ACCEPT_ALL();
  auto err=twai_driver_install(&g,&t,&filter);
  if(err!=ESP_OK){last_error=err;return false;}
  err=twai_start();
  if(err!=ESP_OK){twai_driver_uninstall();last_error=err;return false;}
  can_started=true;gpio_set_level(STB,0);
  // TCAN3404 standby-to-normal tMODE is at most 30 us. A tick delay can
  // round to zero; this 100 us wait also runs under the TWAI driver's PM lock.
  esp_rom_delay_us(100);
 }
 auto err=twai_reconfigure_alerts(TWAI_ALERT_TX_SUCCESS|TWAI_ALERT_TX_FAILED|TWAI_ALERT_BUS_OFF,nullptr);
 if(err!=ESP_OK){last_error=err;can_stop();return false;}
 uint32_t alerts=0;twai_read_alerts(&alerts,0);
 // Normal CAN retries handle arbitration loss. The 40 ms result wait below
 // bounds the retry window; stopping the driver cancels any pending frame.
 twai_message_t m{};m.identifier=f.id;m.data_length_code=f.size;m.ss=0;
 memcpy(m.data,f.data,f.size);
 err=twai_transmit(&m,0); // TX queue is disabled: submit directly or fail.
 if(err==ESP_OK){
  err=twai_read_alerts(&alerts,pdMS_TO_TICKS(40));
  if(err==ESP_OK&&(!(alerts&TWAI_ALERT_TX_SUCCESS)||
     (alerts&(TWAI_ALERT_TX_FAILED|TWAI_ALERT_BUS_OFF))))err=ESP_FAIL;
 }
 if(err!=ESP_OK){last_error=err;can_stop();return false;}
 return true;
}
static int read_vpwr(){
 if(!calibration)return 0;
 int total=0;
 for(int i=0;i<16;i++){
  int raw=0,mv=0;
  if(adc_oneshot_read(adc,ADC_CHANNEL_0,&raw)!=ESP_OK||adc_cali_raw_to_voltage(calibration,raw,&mv)!=ESP_OK)return 0;
  total+=mv;
 }
 return static_cast<int>((total/16.0f)*LEAF_ADC_SCALE*LEAF_ADC_CORRECTION);
}
#if LEAF_CAN_LISTEN_ONLY
static esp_err_t listen_start(){
 gpio_set_level(STB,1);
 twai_general_config_t g=TWAI_GENERAL_CONFIG_DEFAULT(TX,RX,TWAI_MODE_LISTEN_ONLY);
 g.tx_queue_len=0;g.rx_queue_len=128;
 twai_timing_config_t timing=TWAI_TIMING_CONFIG_500KBITS();
 twai_filter_config_t filter=TWAI_FILTER_CONFIG_ACCEPT_ALL();
 auto err=twai_driver_install(&g,&timing,&filter);
 if(err!=ESP_OK){listen_error=err;return err;}
 err=twai_start();
 if(err!=ESP_OK){twai_driver_uninstall();listen_error=err;return err;}
 // Controller is already in listen-only mode before enabling the transceiver.
 gpio_set_level(STB,0);esp_rom_delay_us(100);listen_running=true;
 return ESP_OK;
}
static void listen_poll(){
 if(!listen_running)return;
 twai_message_t message{};
 for(unsigned i=0;i<128;i++){
  auto err=twai_receive(&message,0);
  if(err==ESP_ERR_TIMEOUT)break;
  if(err!=ESP_OK){
   listen_error=err;gpio_set_level(STB,1);twai_stop();twai_driver_uninstall();
   listen_running=false;return;
  }
  ++listen_frames;listen_last_id=message.identifier;
#if LEAF_TELEMETRY_ENABLED
  const auto at=now_ms();
  portENTER_CRITICAL(&telemetry_mux);
  telemetry.receive(message.identifier,message.data,message.data_length_code,message.extd,message.rtr,at);
  portEXIT_CRITICAL(&telemetry_mux);
#endif
 }
 twai_status_info_t info{};
 auto err=twai_get_status_info(&info);
 if(err==ESP_OK){listen_bus_errors=info.bus_error_count;listen_dropped=info.rx_missed_count+info.rx_overrun_count;}
 else listen_error=err;
}
static void listen_task(void*){
 auto err=listen_start();
 ESP_LOGI(TAG,"CAN receive-only diagnostic: start=%d; 500 kbit/s; no TX/ACK/error frames",err);
 uint64_t sample_due=0,report_due=0;
 while(true){
  listen_poll();auto now=now_ms();
  if(now>=sample_due){sample_due=now+1000;vpwr_mv=read_vpwr();}
  if(now>=report_due){
   report_due=now+5000;
   ESP_LOGI(TAG,"CAN listen: running=%d frames=%u last_id=0x%03X bus_errors=%u dropped=%u error=%d VPWR=%.2f V",
    listen_running.load(),listen_frames.load(),listen_last_id.load(),listen_bus_errors.load(),listen_dropped.load(),listen_error.load(),vpwr_mv/1000.0);
  }
  vTaskDelay(1);
 }
}
#endif
[[maybe_unused]] static void control_task(void*){
 leaf::Control control(can_send);
 uint64_t sample_due=0,low_since=0;bool low_off_sent=false;
 while(true){
  auto now=now_ms();
  if(now>=sample_due){
   sample_due=now+1000;int mv=read_vpwr();vpwr_mv=mv;
   battery_ok=mv>=LEAF_MIN_HEAT_VPWR*1000;
   if(!battery_ok){
    if(!low_since)low_since=now;
    if(control.heating_requested()&&!low_off_sent&&now-low_since>=10000){
     control.request(false,now,LEAF_CAN_WRITE_ENABLED,false);low_off_sent=true;
    }
   }else if(mv>(LEAF_MIN_HEAT_VPWR+0.2f)*1000){low_since=0;low_off_sent=false;}
  }
  Request request;
  if(xQueueReceive(requests,&request,0)==pdTRUE){
   if(!request.on||now<=request.expires_ms){
    last_error=0;
    // Re-arm for every admitted On, even if its wake transmission then fails:
    // Control retains an uncertain heat request in that case. Rejected On
    // requests must not postpone the current session's low-battery shutdown.
    if(request.on&&LEAF_CAN_WRITE_ENABLED&&battery_ok&&!control.busy()){
     low_since=0;low_off_sent=false;
    }
    if(!control.request(request.on,now,LEAF_CAN_WRITE_ENABLED,battery_ok))last_error=ESP_ERR_INVALID_STATE;
   }else last_error=ESP_ERR_TIMEOUT;
  }
  control.tick(now_ms());busy=control.busy();heat_requested=control.heating_requested();
  auto_off_seconds=control.auto_off_seconds(now_ms());
  #if LEAF_TELEMETRY_ENABLED && !LEAF_CAN_LISTEN_ONLY
  if(!control.busy()){
   if(can_started)can_stop();
   passive_tick();
  }else if(can_started)telemetry_drain();
#else
  if(!control.busy())can_stop();
#endif
  vTaskDelay(pdMS_TO_TICKS(20));
 }
}
static void schedule_reconnect(){
 if(online)return;
 portENTER_CRITICAL(&retry_mux);auto delay=retry.next_ms();portEXIT_CRITICAL(&retry_mux);
 esp_timer_stop(reconnect_timer);
 esp_timer_start_once(reconnect_timer,static_cast<uint64_t>(delay)*1000);
}
static void reconnect(void*){if(!online&&esp_wifi_connect()!=ESP_OK)schedule_reconnect();}
static void wifi_event(void*,esp_event_base_t base,int32_t id,void* data){
 if(base==WIFI_EVENT&&id==WIFI_EVENT_STA_START)reconnect(nullptr);
 else if(base==WIFI_EVENT&&id==WIFI_EVENT_STA_DISCONNECTED){online=false;schedule_reconnect();}
 else if(base==IP_EVENT&&id==IP_EVENT_STA_GOT_IP){
  online=true;esp_timer_stop(reconnect_timer);
  portENTER_CRITICAL(&retry_mux);retry.connected();portEXIT_CRITICAL(&retry_mux);
  auto* e=static_cast<ip_event_got_ip_t*>(data);
  ESP_LOGI(TAG,"Open http://" IPSTR " (reserve this address in your router)",IP2STR(&e->ip_info.ip));
 }
}
static const char PAGE[]=R"HTML(<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Leafy</title><style>body{font:18px system-ui;max-width:34em;margin:3em auto;padding:1em}button,input{font:inherit;padding:.7em;margin:.3em}pre{white-space:pre-wrap}#result,#keyStatus{white-space:pre-wrap}small{display:block}</style><h1>Leafy</h1><p>Connected locally. Commands do not confirm the car's actual heater state.</p><label for="key">Control key</label><br><input id="key" type="password" placeholder="Control key" autocomplete="off" autocapitalize="none" spellcheck="false"><button id="saveKey" type="button">Save key for this tab</button><button id="forgetKey" type="button">Forget key</button><small>Stored in this browser tab's session, not permanently. Saving checks the key without controlling the heater.</small><p id="keyStatus" role="status"></p><p><button id="on" type="button">Heat on</button><button id="off" type="button">Heat off</button></p><p id="result" role="status"></p><pre id="status"></pre><script>
const KEY_STORAGE='leafy.controlKey';
const keyInput=document.getElementById('key');
const keyStatus=document.getElementById('keyStatus');
const result=document.getElementById('result');
try{const saved=sessionStorage.getItem(KEY_STORAGE);if(saved){keyInput.value=saved;keyStatus.textContent='Key restored for this tab. Use Save key to check it again.'}}catch(e){keyStatus.textContent='Session storage unavailable. You can still enter a key and use the buttons.'}
function clearSavedKey(){try{sessionStorage.removeItem(KEY_STORAGE)}catch(e){}}
function forgetKey(){clearSavedKey();keyInput.value='';keyStatus.textContent='Key forgotten.';result.textContent=''}
async function saveKey(){
 const key=keyInput.value.trim();keyInput.value=key;
 if(!key){keyStatus.textContent='Enter the control key first.';return}
 const button=document.getElementById('saveKey');button.disabled=true;keyStatus.textContent='Checking key...';
 try{
  const response=await fetch('/api/auth',{cache:'no-store',headers:{'X-Leaf-Key':key}});
  const message=await response.text();
  if(!response.ok){if(response.status===401)clearSavedKey();keyStatus.textContent='Key not saved (HTTP '+response.status+'): '+message;return}
  try{sessionStorage.setItem(KEY_STORAGE,key);keyStatus.textContent='Key verified and saved for this tab.'}
  catch(e){keyStatus.textContent='Key verified, but this browser cannot save it for the session. Keep this page open.'}
 }catch(e){keyStatus.textContent='Could not verify the key: connection failed. No heater command was sent.'}
 finally{button.disabled=false}
}
const pending={on:false,off:false};
async function command(action){
 if(action!=='on'&&action!=='off')return;
 if(pending[action])return;
 const key=keyInput.value.trim();
 if(!key){result.textContent='Enter your control key, then use Save key to verify it.';return}
 pending[action]=true;const button=document.getElementById(action);button.disabled=true;
 result.textContent='Sending Heat '+action+' request...';
 try{
  const response=await fetch('/api/'+action,{method:'POST',headers:{'X-Leaf-Key':key}});
  const message=await response.text();
  result.textContent=(response.ok?'Heat '+action+' request accepted':'Heat '+action+' request rejected')+' (HTTP '+response.status+'): '+message;
  if(response.status===401){clearSavedKey();keyStatus.textContent='Control key missing or incorrect. Verify it with Save key.'}
 }catch(e){result.textContent='Connection lost. Command outcome unknown; check the car. Do not repeatedly press Heat on.'}
 finally{pending[action]=false;button.disabled=false;refresh()}
}
let refreshing=false;
async function refresh(){
 if(refreshing)return;
 refreshing=true;
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),3000);
 try{
  const response=await fetch('/api/status',{cache:'no-store',signal:controller.signal});
  if(!response.ok)throw Error('status');
  document.getElementById('status').textContent=await response.text();
 }catch(e){document.getElementById('status').textContent='Device unreachable. Battery reading and timer unavailable. Retrying status only...'}
 finally{clearTimeout(timeout);refreshing=false}
}
// Bind listeners in script scope: inline handlers can shadow functions with
// native element properties such as HTMLButtonElement.command.
document.getElementById('saveKey').addEventListener('click',saveKey);
document.getElementById('forgetKey').addEventListener('click',forgetKey);
document.getElementById('on').addEventListener('click',()=>command('on'));
document.getElementById('off').addEventListener('click',()=>command('off'));
setInterval(refresh,5000);refresh();
</script></html>)HTML";
static esp_err_t home(httpd_req_t* r){httpd_resp_set_type(r,"text/html");httpd_resp_set_hdr(r,"Cache-Control","no-store");return httpd_resp_send(r,PAGE,HTTPD_RESP_USE_STRLEN);}
static esp_err_t status(httpd_req_t*r){
 // Keep the normal web page independent of the optional API bridge.
 portENTER_CRITICAL(&telemetry_mux);const auto snapshot=telemetry;portEXIT_CRITICAL(&telemetry_mux);
 const auto now=now_ms();
 char dashboard[192];
 if(!LEAF_TELEMETRY_ENABLED)snprintf(dashboard,sizeof(dashboard),"Main battery (dashboard): reader disabled");
 else if(!snapshot.dashboard_valid())snprintf(dashboard,sizeof(dashboard),"Main battery (dashboard): waiting for a CAN reading");
 else{
  const auto age=snapshot.dashboard_age(now);
  snprintf(dashboard,sizeof(dashboard),age>120000?
   "Main battery (dashboard): Last known %d%% - %llu seconds ago (stale)":
   "Main battery (dashboard): %d%% - updated %llu seconds ago",
   snapshot.dashboard_percent(),static_cast<unsigned long long>(age/1000));
 }
 char battery[192];
 if(!LEAF_TELEMETRY_ENABLED)snprintf(battery,sizeof(battery),"Main battery (BMS): reader disabled");
 else if(!snapshot.valid())snprintf(battery,sizeof(battery),"Main battery (BMS): waiting for a CAN reading");
 else{
  const auto age=snapshot.age(now);
  snprintf(battery,sizeof(battery),age>120000?
   "Main battery (BMS): Last known %.1f%% - %llu seconds ago (stale)":
   "Main battery (BMS): %.1f%% - updated %llu seconds ago",
   snapshot.tenths()/10.0,static_cast<unsigned long long>(age/1000));
 }
 char timer[128];const int remaining=auto_off_seconds.load();
 if(remaining<0)snprintf(timer,sizeof(timer),"Automatic Off request: no timer");
 else if(remaining==0)snprintf(timer,sizeof(timer),"Automatic Off request: timer elapsed; verify heater in car");
 else snprintf(timer,sizeof(timer),"Automatic Off request: in %02d:%02d (local timer)",remaining/60,remaining%60);
 char out[1024];snprintf(out,sizeof(out),"%s\n%s\nBMS percentage may differ from the dashboard.\nBattery reader error: %d\n\nCAN controls: %s\nProtected supply: %.2f V (after input diode)\nRequest sequence: %s\nLocal heat request / timer: %s\n%s\nLast command error: %d\nActual heater state: unverified",
  dashboard,battery,telemetry_error.load(),LEAF_CAN_WRITE_ENABLED?"enabled":"locked for commissioning",vpwr_mv/1000.0,busy?"running":"idle",heat_requested?"active or outcome uncertain":"none",timer,last_error.load());
#if LEAF_CAN_LISTEN_ONLY
 snprintf(out,sizeof(out),"CAN controls: locked; RECEIVE-ONLY diagnostic\nProtected supply: %.2f V (after input diode)\nListener: %s\nReceived frames: %u\nLast CAN ID: 0x%03X\nBus errors: %u\nDropped frames: %u\nListener error: %d\nNo transmitted frames, ACKs or error frames.\nActual heater state: unverified",
  vpwr_mv/1000.0,listen_running?"running":"stopped",listen_frames.load(),listen_last_id.load(),listen_bus_errors.load(),listen_dropped.load(),listen_error.load());
#endif
 httpd_resp_set_hdr(r,"Cache-Control","no-store");return httpd_resp_send(r,out,HTTPD_RESP_USE_STRLEN);
}
static bool valid_control_key(httpd_req_t*r){
 char key[129]{};
 auto len=httpd_req_get_hdr_value_len(r,"X-Leaf-Key");
 return len>0&&len<sizeof(key)&&httpd_req_get_hdr_value_str(r,"X-Leaf-Key",key,sizeof(key))==ESP_OK&&leaf::authorized(key,LEAF_CONTROL_KEY);
}
static esp_err_t auth_check(httpd_req_t*r){
 httpd_resp_set_hdr(r,"Cache-Control","no-store");
 if(!valid_control_key(r)){
  httpd_resp_set_status(r,"401 Unauthorized");
  return httpd_resp_sendstr(r,"Control key missing or incorrect.");
 }
 return httpd_resp_sendstr(r,"Control key accepted. No heater command sent.");
}
static esp_err_t command(httpd_req_t*r){
 httpd_resp_set_hdr(r,"Cache-Control","no-store");
 if(!valid_control_key(r)){
  httpd_resp_set_status(r,"401 Unauthorized");return httpd_resp_sendstr(r,"Control key missing or incorrect.");
 }
 if(r->content_len!=0)return httpd_resp_send_err(r,HTTPD_400_BAD_REQUEST,"Request body must be empty.");
 if(!LEAF_CAN_WRITE_ENABLED)return httpd_resp_send_err(r,HTTPD_403_FORBIDDEN,"CAN is locked until commissioning checks pass.");
 bool on=strcmp(r->uri,"/api/on")==0;
 if(on&&(!battery_ok||busy)){httpd_resp_set_status(r,"409 Conflict");return httpd_resp_sendstr(r,"Low/unknown battery voltage or a command is running.");}
 Request q{on,now_ms()+1000};
 // A length-one queue lets Off replace a not-yet-executed On. Never queue On behind Off.
 if(on){if(xQueueSend(requests,&q,0)!=pdTRUE){httpd_resp_set_status(r,"409 Conflict");return httpd_resp_sendstr(r,"A command is pending.");}}
 else xQueueOverwrite(requests,&q);
 httpd_resp_set_status(r,"202 Accepted");return httpd_resp_sendstr(r,"Request submitted. Verify the heater in the car.");
}
static esp_err_t json_status(httpd_req_t*r){
 httpd_resp_set_hdr(r,"Cache-Control","no-store");
 if(!valid_control_key(r)){httpd_resp_set_status(r,"401 Unauthorized");return httpd_resp_sendstr(r,"Control key missing or incorrect.");}
 const auto now=now_ms();
 portENTER_CRITICAL(&telemetry_mux);const auto snapshot=telemetry;portEXIT_CRITICAL(&telemetry_mux);
 char soc[16]="null",age[32]="null";
 if(snapshot.valid()){
  snprintf(soc,sizeof(soc),"%d",snapshot.tenths());
  snprintf(age,sizeof(age),"%llu",static_cast<unsigned long long>(snapshot.age(now)));
 }
 char out[512];
 snprintf(out,sizeof(out),"{\"schemaVersion\":1,\"uptimeMs\":%llu,\"canWriteEnabled\":%s,\"protectedSupplyMv\":%d,\"requestBusy\":%s,\"heatRequested\":%s,\"lastCommandError\":%d,\"socTenths\":%s,\"socAgeMs\":%s,\"telemetryEnabled\":%s,\"telemetryError\":%d}",
  static_cast<unsigned long long>(now),LEAF_CAN_WRITE_ENABLED?"true":"false",vpwr_mv.load(),busy?"true":"false",heat_requested?"true":"false",last_error.load(),soc,age,LEAF_TELEMETRY_ENABLED?"true":"false",telemetry_error.load());
 httpd_resp_set_type(r,"application/json");return httpd_resp_send(r,out,HTTPD_RESP_USE_STRLEN);
}
extern "C" void app_main(){
 // Standby before any network or ADC initialization. External R10 also holds standby at reset.
 gpio_set_level(STB,1);gpio_set_direction(STB,GPIO_MODE_OUTPUT);
 auto err=nvs_flash_init();
 if(err==ESP_ERR_NVS_NO_FREE_PAGES||err==ESP_ERR_NVS_NEW_VERSION_FOUND){ESP_ERROR_CHECK(nvs_flash_erase());err=nvs_flash_init();}
 ESP_ERROR_CHECK(err);
 esp_pm_config_t pm{};pm.max_freq_mhz=80;pm.min_freq_mhz=40;pm.light_sleep_enable=true;
 ESP_ERROR_CHECK(esp_pm_configure(&pm));
 adc_oneshot_unit_init_cfg_t unit{};unit.unit_id=ADC_UNIT_1;
 ESP_ERROR_CHECK(adc_oneshot_new_unit(&unit,&adc));
 adc_oneshot_chan_cfg_t ch{};ch.atten=ADC_ATTEN_DB_6;ch.bitwidth=ADC_BITWIDTH_DEFAULT;
 ESP_ERROR_CHECK(adc_oneshot_config_channel(adc,ADC_CHANNEL_0,&ch));
 adc_cali_curve_fitting_config_t cal{};cal.unit_id=ADC_UNIT_1;cal.chan=ADC_CHANNEL_0;cal.atten=ADC_ATTEN_DB_6;cal.bitwidth=ADC_BITWIDTH_DEFAULT;
 if(adc_cali_create_scheme_curve_fitting(&cal,&calibration)!=ESP_OK){calibration=nullptr;ESP_LOGE(TAG,"ADC calibration unavailable: Heat on remains blocked");}
 requests=xQueueCreate(1,sizeof(Request));assert(requests);
#if LEAF_CAN_LISTEN_ONLY
 ESP_ERROR_CHECK(xTaskCreate(listen_task,"leaf_listen",4096,nullptr,5,nullptr)==pdPASS?ESP_OK:ESP_ERR_NO_MEM);
#else
 xTaskCreate(control_task,"leaf_control",4096,nullptr,5,nullptr);
#endif
 ESP_ERROR_CHECK(esp_netif_init());ESP_ERROR_CHECK(esp_event_loop_create_default());
 auto* sta=esp_netif_create_default_wifi_sta();ESP_ERROR_CHECK(esp_netif_set_hostname(sta,"leaf-heat"));
 esp_timer_create_args_t timer{};timer.callback=reconnect;timer.name="wifi_retry";ESP_ERROR_CHECK(esp_timer_create(&timer,&reconnect_timer));
 ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT,ESP_EVENT_ANY_ID,wifi_event,nullptr));
 ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT,IP_EVENT_STA_GOT_IP,wifi_event,nullptr));
 wifi_init_config_t init=WIFI_INIT_CONFIG_DEFAULT();ESP_ERROR_CHECK(esp_wifi_init(&init));
 ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
 wifi_config_t cfg{};
 static_assert(sizeof(LEAF_WIFI_SSID)<=sizeof(cfg.sta.ssid),"SSID too long");
 static_assert(sizeof(LEAF_WIFI_PASSWORD)<=sizeof(cfg.sta.password),"Wi-Fi password too long");
 strncpy(reinterpret_cast<char*>(cfg.sta.ssid),LEAF_WIFI_SSID,sizeof(cfg.sta.ssid));
 strncpy(reinterpret_cast<char*>(cfg.sta.password),LEAF_WIFI_PASSWORD,sizeof(cfg.sta.password));
 cfg.sta.threshold.authmode=WIFI_AUTH_WPA2_PSK;
 ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA,&cfg));
 ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_MIN_MODEM));
 if(strlen(LEAF_WIFI_SSID)>0)ESP_ERROR_CHECK(esp_wifi_start());
 else ESP_LOGW(TAG,"Build with local settings.hpp to join home Wi-Fi; CAN is locked by default");
 httpd_config_t http=HTTPD_DEFAULT_CONFIG();http.lru_purge_enable=true;httpd_handle_t server;
 ESP_ERROR_CHECK(httpd_start(&server,&http));
 httpd_uri_t routes[]={{"/",HTTP_GET,home,nullptr},{"/api/status",HTTP_GET,status,nullptr},{"/api/v1/status",HTTP_GET,json_status,nullptr},{"/api/auth",HTTP_GET,auth_check,nullptr},{"/api/on",HTTP_POST,command,nullptr},{"/api/off",HTTP_POST,command,nullptr}};
 for(auto& route:routes)ESP_ERROR_CHECK(httpd_register_uri_handler(server,&route));
}

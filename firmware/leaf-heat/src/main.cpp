#include "control.hpp"
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

static const char* TAG="leaf";
static constexpr gpio_num_t STB=GPIO_NUM_1, TX=GPIO_NUM_4, RX=GPIO_NUM_5;
static uint64_t now_ms(){return esp_timer_get_time()/1000;}
struct Request{bool on;uint64_t expires_ms;};
static QueueHandle_t requests;
static std::atomic<bool> busy{false},heat_requested{false},battery_ok{false};
static std::atomic<int> vpwr_mv{0},last_error{0};
static bool can_started=false;
static leaf::Retry retry;
static portMUX_TYPE retry_mux=portMUX_INITIALIZER_UNLOCKED;
static std::atomic<bool> online{false};
static esp_timer_handle_t reconnect_timer;
static adc_oneshot_unit_handle_t adc;
static adc_cali_handle_t calibration=nullptr;

static void can_stop(){
 gpio_set_level(STB,1);
 if(can_started){twai_stop();twai_driver_uninstall();can_started=false;}
}
static bool can_send(const leaf::Frame& f){
 if(!LEAF_CAN_WRITE_ENABLED)return false;
 if(!can_started){
  twai_general_config_t g=TWAI_GENERAL_CONFIG_DEFAULT(TX,RX,TWAI_MODE_NORMAL);
  g.tx_queue_len=0;g.rx_queue_len=1;
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
static void control_task(void*){
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
  if(!control.busy())can_stop();
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
static const char PAGE[]=R"HTML(<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Leaf heat</title><style>body{font:18px system-ui;max-width:34em;margin:3em auto;padding:1em}button,input{font:inherit;padding:.7em;margin:.3em}pre{white-space:pre-wrap}</style><h1>Leaf heat</h1><p>Connected locally. Commands do not confirm the car's actual heater state.</p><input id="key" type="password" placeholder="Control key" autocomplete="off"><p><button onclick="command('on')">Heat on</button><button onclick="command('off')">Heat off</button></p><p id="result"></p><pre id="status"></pre><script>
async function command(action){try{let r=await fetch('/api/'+action,{method:'POST',headers:{'X-Leaf-Key':document.getElementById('key').value}});document.getElementById('result').textContent=await r.text()}catch(e){document.getElementById('result').textContent='Connection lost. Command outcome unknown; check the car.'}}
async function refresh(){try{let r=await fetch('/api/status',{cache:'no-store'});document.getElementById('status').textContent=await r.text()}catch(e){document.getElementById('status').textContent='Device unreachable. Retrying…'}}setInterval(refresh,5000);refresh();
</script></html>)HTML";
static esp_err_t home(httpd_req_t* r){httpd_resp_set_type(r,"text/html");httpd_resp_set_hdr(r,"Cache-Control","no-store");return httpd_resp_send(r,PAGE,HTTPD_RESP_USE_STRLEN);}
static esp_err_t status(httpd_req_t*r){
 char out[360];snprintf(out,sizeof(out),"CAN controls: %s\nProtected supply: %.2f V (after input diode)\nRequest sequence: %s\nLocal heat request / timer: %s\nLast command error: %d\nActual heater state: unverified",LEAF_CAN_WRITE_ENABLED?"enabled":"locked for commissioning",vpwr_mv/1000.0,busy?"running":"idle",heat_requested?"active or outcome uncertain":"none",last_error.load());
 httpd_resp_set_hdr(r,"Cache-Control","no-store");return httpd_resp_send(r,out,HTTPD_RESP_USE_STRLEN);
}
static esp_err_t command(httpd_req_t*r){
 char key[129]{};
 auto len=httpd_req_get_hdr_value_len(r,"X-Leaf-Key");
 if(len==0||len>=sizeof(key)||httpd_req_get_hdr_value_str(r,"X-Leaf-Key",key,sizeof(key))!=ESP_OK||!leaf::authorized(key,LEAF_CONTROL_KEY)){
  httpd_resp_set_status(r,"401 Unauthorized");return httpd_resp_sendstr(r,"Control key required.");
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
 xTaskCreate(control_task,"leaf_control",4096,nullptr,5,nullptr);
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
 httpd_uri_t routes[]={{"/",HTTP_GET,home,nullptr},{"/api/status",HTTP_GET,status,nullptr},{"/api/on",HTTP_POST,command,nullptr},{"/api/off",HTTP_POST,command,nullptr}};
 for(auto& route:routes)ESP_ERROR_CHECK(httpd_register_uri_handler(server,&route));
}

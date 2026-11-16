#include "telemetry.hpp"
#include <atomic>
#include <cassert>
#include <iostream>
#include <vector>
using esp_err_t=int;
constexpr int ESP_OK=0,ESP_FAIL=-1,ESP_ERR_TIMEOUT=0x107,STB=1,TX=4,RX=5,TWAI_MODE_LISTEN_ONLY=3;
struct twai_general_config_t{int mode,tx,rx,tx_queue_len=5,rx_queue_len=5;};
struct twai_timing_config_t{};struct twai_filter_config_t{};
struct twai_message_t{uint32_t identifier=0x55b;uint8_t data_length_code=8,data[8]={0x7d,0};bool extd=false,rtr=false;};
#define TWAI_GENERAL_CONFIG_DEFAULT(tx,rx,mode) twai_general_config_t{mode,tx,rx}
#define TWAI_TIMING_CONFIG_500KBITS() twai_timing_config_t{}
#define TWAI_FILTER_CONFIG_ACCEPT_ALL() twai_filter_config_t{}
#define portENTER_CRITICAL(x) ((void)(x))
#define portEXIT_CRITICAL(x) ((void)(x))
static int telemetry_mux;
static leaf::BatteryTelemetry telemetry;
static bool passive_started=false,can_started=false,installed=false,running=false,fail_start=false;
static uint64_t passive_due=0,passive_end=0,clock_ms=0;
static std::atomic<int> telemetry_error{0};
static int standby=1,starts=0;
static std::vector<twai_message_t> frames;
static uint64_t now_ms(){return clock_ms;}
static void gpio_set_level(int,int level){standby=level;}
static void esp_rom_delay_us(int us){assert(us>=30);}
static int twai_driver_install(const twai_general_config_t*g,const twai_timing_config_t*,const twai_filter_config_t*){assert(!installed);assert(!can_started);assert(g->mode==TWAI_MODE_LISTEN_ONLY);assert(g->tx_queue_len==0);installed=true;return ESP_OK;}
static int twai_start(){if(fail_start)return ESP_FAIL;running=true;++starts;return ESP_OK;}
static int twai_stop(){running=false;return ESP_OK;}
static int twai_driver_uninstall(){installed=false;return ESP_OK;}
static int twai_receive(twai_message_t*m,int){if(frames.empty())return ESP_ERR_TIMEOUT;*m=frames.back();frames.pop_back();return ESP_OK;}
#include "passive_can.inc"
int main(){
 passive_tick();assert(passive_started&&running&&standby==0&&starts==1);
 frames.push_back({});clock_ms=20;passive_tick();assert(telemetry.valid()&&telemetry.tenths()==500);
 clock_ms=1500;passive_tick();assert(!passive_started&&!installed&&standby==1);
 clock_ms=59000;passive_tick();assert(starts==1);
 clock_ms=60000;passive_tick();assert(starts==2);
 passive_stop();assert(!installed&&!running&&standby==1); // Command can now acquire driver.
 can_started=true;clock_ms=120000;passive_tick();assert(starts==2);can_started=false;
 fail_start=true;passive_tick();assert(!installed&&!passive_started&&standby==1&&telemetry_error==ESP_FAIL);
 fail_start=false;clock_ms=120020;passive_tick();assert(starts==2); // No busy retry loop.
 clock_ms=180000;passive_tick();assert(starts==3&&telemetry_error==ESP_OK);
 passive_stop();
 std::cout<<"PASS passive mode, sample update, bounded window, interval, command ownership and error cleanup\n";
}

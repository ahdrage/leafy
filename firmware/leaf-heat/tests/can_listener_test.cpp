#include <atomic>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
#define CHECK(x) do { if (!(x)) throw std::runtime_error(#x); } while(0)
using esp_err_t=int;
constexpr int ESP_OK=0, ESP_FAIL=-1, ESP_ERR_TIMEOUT=0x107;
constexpr int STB=1, TX=4, RX=5, TWAI_MODE_LISTEN_ONLY=2;
struct twai_general_config_t {int tx,rx,mode,tx_queue_len=5,rx_queue_len=5;};
struct twai_timing_config_t {int bitrate;};
struct twai_filter_config_t {bool all;};
struct twai_message_t {uint32_t identifier=0;};
struct twai_status_info_t {uint32_t bus_error_count=0,rx_missed_count=0,rx_overrun_count=0;};
#define TWAI_GENERAL_CONFIG_DEFAULT(tx,rx,mode) twai_general_config_t{tx,rx,mode}
#define TWAI_TIMING_CONFIG_500KBITS() twai_timing_config_t{500000}
#define TWAI_FILTER_CONFIG_ACCEPT_ALL() twai_filter_config_t{true}
static bool installed=false,running=false,fail_install=false,fail_start=false;
static int standby=1,delay_us=0;
static std::vector<twai_message_t> incoming;
static std::atomic<bool> listen_running{false};
static std::atomic<unsigned> listen_frames{0},listen_last_id{0},listen_bus_errors{0},listen_dropped{0};
static std::atomic<int> listen_error{0};
static int gpio_set_level(int pin,int level){CHECK(pin==STB);if(!level)CHECK(running);standby=level;return ESP_OK;}
static void esp_rom_delay_us(int us){delay_us+=us;}
static int twai_driver_install(const twai_general_config_t*g,const twai_timing_config_t*t,const twai_filter_config_t*f){
 CHECK(standby==1);CHECK(g->mode==TWAI_MODE_LISTEN_ONLY);CHECK(g->tx_queue_len==0);
 CHECK(g->rx_queue_len>=64);CHECK(g->tx==TX&&g->rx==RX);CHECK(t->bitrate==500000&&f->all);
 if(fail_install)return ESP_FAIL;installed=true;return ESP_OK;
}
static int twai_start(){CHECK(installed);if(fail_start)return ESP_FAIL;running=true;return ESP_OK;}
static int twai_stop(){running=false;return ESP_OK;}
static int twai_driver_uninstall(){installed=false;return ESP_OK;}
static int twai_receive(twai_message_t*m,int){CHECK(running&&standby==0);if(incoming.empty())return ESP_ERR_TIMEOUT;*m=incoming.back();incoming.pop_back();return ESP_OK;}
static int twai_get_status_info(twai_status_info_t*s){s->bus_error_count=3;s->rx_missed_count=4;s->rx_overrun_count=2;return ESP_OK;}
// No transmit function is provided: any call to it fails this test's compilation.
#include "can_listener.inc"
static void reset(){installed=running=fail_install=fail_start=false;standby=1;delay_us=0;
 listen_running=false;listen_frames=listen_last_id=listen_bus_errors=listen_dropped=0;listen_error=0;incoming.clear();}
int main(){try{
 reset();CHECK(listen_start()==ESP_OK);CHECK(listen_running&&running&&standby==0&&delay_us>=30);
 std::cout<<"PASS listen-only startup, no TX queue, 500 kbit/s and standby sequencing\n";
 incoming={{0x123},{0x456}};listen_poll();CHECK(listen_frames==2&&listen_last_id==0x123);CHECK(listen_bus_errors==3&&listen_dropped==6);
 std::cout<<"PASS received frame counting and controller error reporting\n";
 listen_poll();CHECK(listen_frames==2);std::cout<<"PASS idle bus does not invent frames\n";
 incoming.resize(300);listen_poll();CHECK(!incoming.empty());std::cout<<"PASS bounded drain yields under sustained traffic\n";
 reset();fail_install=true;CHECK(listen_start()!=ESP_OK);CHECK(!installed&&!running&&!listen_running&&standby==1);
 listen_poll();CHECK(listen_frames==0);std::cout<<"PASS install failure stays in standby\n";
 reset();fail_start=true;CHECK(listen_start()!=ESP_OK);CHECK(!installed&&!running&&!listen_running&&standby==1);
 std::cout<<"PASS start failure releases driver and stays in standby\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}

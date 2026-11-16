#include "telemetry.hpp"
#include <atomic>
#include <cstdio>
#include <string>
#include <cassert>
#include <iostream>
using esp_err_t=int;
constexpr int HTTPD_RESP_USE_STRLEN=-1;
#define LEAF_CAN_WRITE_ENABLED true
#define LEAF_TELEMETRY_ENABLED true
#define LEAF_CAN_LISTEN_ONLY false
#define portENTER_CRITICAL(x) ((void)(x))
#define portEXIT_CRITICAL(x) ((void)(x))
static leaf::BatteryTelemetry telemetry;
[[maybe_unused]] static int telemetry_mux;
static std::atomic<int> vpwr_mv{12180},last_error{0},telemetry_error{0},auto_off_seconds{-1};
static std::atomic<bool> busy{false},heat_requested{false};
static uint64_t clock_ms=5000;
[[maybe_unused]] static uint64_t now_ms(){return clock_ms;}
struct httpd_req_t{std::string body;};
static void httpd_resp_set_hdr(httpd_req_t*,const char*,const char*){}
static int httpd_resp_send(httpd_req_t*r,const char*s,int){r->body=s;return 0;}
#include "website_status.inc"
int main(){
 httpd_req_t r;status(&r);
 assert(r.body.find("Main battery (BMS): waiting for a CAN reading")!=std::string::npos);
 assert(r.body.find("Main battery (dashboard): waiting for a CAN reading")!=std::string::npos);
 assert(r.body.find("Automatic Off request: no timer")!=std::string::npos);
 const uint8_t half[]={0x7d,0,0,0,0,0,0,0};telemetry.receive(0x55b,half,8,false,false,1000);
 uint8_t dash[8]={};dash[4]=0xe1;telemetry.receive(0x1db,dash,8,false,false,3000);
 heat_requested=true;auto_off_seconds=899;status(&r);
 assert(r.body.find("Main battery (dashboard): 97% - updated 2 seconds ago")!=std::string::npos);
 assert(r.body.find("Main battery (dashboard)")<r.body.find("Main battery (BMS)"));
 assert(r.body.find("50.0% - updated 4 seconds ago")!=std::string::npos);
 assert(r.body.find("Automatic Off request: in 14:59")!=std::string::npos);
 clock_ms=121001;status(&r);assert(r.body.find("Last known 50.0%")!=std::string::npos);
 assert(r.body.find("97% - updated 118 seconds ago")!=std::string::npos);
 assert(r.body.find("120 seconds ago")!=std::string::npos);
 assert(r.body.find("Actual heater state: unverified")!=std::string::npos);
 auto_off_seconds=0;status(&r);assert(r.body.find("timer elapsed; verify heater in car")!=std::string::npos);
 telemetry_error=5;status(&r);assert(r.body.find("Battery reader error: 5")!=std::string::npos);
 assert(r.body.find("Protected supply: 12.18 V (after input diode)")!=std::string::npos);
 clock_ms=130001;dash[4]=127;assert(!telemetry.receive(0x1db,dash,8,false,false,clock_ms));status(&r);
 assert(r.body.find("Last known 97% - 127 seconds ago (stale)")!=std::string::npos);
 telemetry.receive(0x55b,half,8,false,false,clock_ms);status(&r);
 assert(r.body.find("Last known 97% - 127 seconds ago (stale)")!=std::string::npos);
 assert(r.body.find("50.0% - updated 0 seconds ago")!=std::string::npos);
 telemetry={};dash[4]=0;telemetry.receive(0x1db,dash,8,false,false,clock_ms);status(&r);
 assert(r.body.find("Main battery (dashboard): 0% - updated 0 seconds ago")!=std::string::npos);
 assert(r.body.find("Main battery (BMS): waiting for a CAN reading")!=std::string::npos);
 dash[4]=100;telemetry.receive(0x1db,dash,8,false,false,clock_ms);status(&r);
 assert(r.body.find("Main battery (dashboard): 100% - updated 0 seconds ago")!=std::string::npos);
 std::cout<<"PASS website status: independent dashboard/BMS ages, invalid/zero/full readings, countdown and errors\n";
}

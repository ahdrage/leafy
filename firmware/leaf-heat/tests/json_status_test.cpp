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
#define portENTER_CRITICAL(x) ((void)(x))
#define portEXIT_CRITICAL(x) ((void)(x))
static leaf::BatteryTelemetry telemetry;
static int telemetry_mux;
static std::atomic<int> vpwr_mv{12180},last_error{0},telemetry_error{0};
static std::atomic<bool> busy{false},heat_requested{false};
static uint64_t now_ms(){return 5000;}
struct httpd_req_t{bool auth=true;std::string status="200",body,type;};
static bool valid_control_key(httpd_req_t*r){return r->auth;}
static void httpd_resp_set_hdr(httpd_req_t*,const char*,const char*){}
static void httpd_resp_set_status(httpd_req_t*r,const char*s){r->status=s;}
static int httpd_resp_sendstr(httpd_req_t*r,const char*s){r->body=s;return 0;}
static void httpd_resp_set_type(httpd_req_t*r,const char*s){r->type=s;}
static int httpd_resp_send(httpd_req_t*r,const char*s,int){r->body=s;return 0;}
#include "json_status.inc"
int main(){
 httpd_req_t r;r.auth=false;json_status(&r);assert(r.status=="401 Unauthorized");assert(r.body.find("protectedSupplyMv")==std::string::npos);
 r={};json_status(&r);assert(r.type=="application/json");assert(r.body.find("\"socTenths\":null")!=std::string::npos);assert(r.body.find("\"protectedSupplyMv\":12180")!=std::string::npos);
 const uint8_t half[]={0x7d,0,0,0,0,0,0,0};telemetry.receive(0x55b,half,8,false,false,1000);json_status(&r);
 assert(r.body.find("\"socTenths\":500")!=std::string::npos);assert(r.body.find("\"socAgeMs\":4000")!=std::string::npos);
 std::cout<<"PASS authenticated JSON status, unknown battery and timed SOC snapshot\n";
}

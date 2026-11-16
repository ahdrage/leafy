#include "control.hpp"
#include <cstring>
#include <iostream>
#include <stdexcept>
#define CHECK(x) do { if(!(x))throw std::runtime_error(#x); } while(0)
#define LEAF_CONTROL_KEY "host-test-key-123456"
using esp_err_t=int;
constexpr int ESP_OK=0, ESP_FAIL=-1;
struct httpd_req_t {std::string key,status="200 OK",body;bool fail_read=false,no_store=false;};
static size_t httpd_req_get_hdr_value_len(httpd_req_t*r,const char*){return r->key.size();}
static int httpd_req_get_hdr_value_str(httpd_req_t*r,const char*,char*out,size_t size){if(r->fail_read)return ESP_FAIL;std::strncpy(out,r->key.c_str(),size);return ESP_OK;}
static int httpd_resp_set_status(httpd_req_t*r,const char*s){r->status=s;return ESP_OK;}
static int httpd_resp_set_hdr(httpd_req_t*r,const char*k,const char*v){CHECK(std::string(k)=="Cache-Control"&&std::string(v)=="no-store");r->no_store=true;return ESP_OK;}
static int httpd_resp_sendstr(httpd_req_t*r,const char*s){r->body=s;return ESP_OK;}
// Auth code has no CAN/queue functions available: it must only validate the key.
#include "http_auth.inc"
int main(){try{
 httpd_req_t r;r.key=LEAF_CONTROL_KEY;CHECK(auth_check(&r)==ESP_OK);CHECK(r.status=="200 OK"&&r.no_store);CHECK(r.body.find(LEAF_CONTROL_KEY)==std::string::npos);
 std::cout<<"PASS valid key is accepted without echoing credentials\n";
 for(const auto& key:{std::string(),std::string("wrong"),std::string(LEAF_CONTROL_KEY)+"suffix",std::string(129,'x')}){
  r=httpd_req_t{};r.key=key;CHECK(auth_check(&r)==ESP_OK);CHECK(r.status=="401 Unauthorized"&&r.no_store);
 }
 std::cout<<"PASS missing, wrong, extended and oversized keys are rejected\n";
 r=httpd_req_t{};r.key=LEAF_CONTROL_KEY;r.fail_read=true;auth_check(&r);CHECK(r.status=="401 Unauthorized");
 std::cout<<"PASS header read failure fails closed\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}

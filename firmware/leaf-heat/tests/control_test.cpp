#include "control.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>
#define CHECK(x) do {if(!(x)) throw std::runtime_error(#x);} while(0)
int main(){int failures=0,count=0;
auto test=[&](const char*name,auto fn){++count;try{fn();std::cout<<"PASS "<<name<<'\n';}catch(const std::exception&e){++failures;std::cout<<"FAIL "<<name<<": "<<e.what()<<'\n';}};
test("retry forever with bounded delay",[]{leaf::Retry r;for(auto n:{1000u,2000u,4000u,8000u,16000u,30000u})CHECK(r.next_ms()==n);for(int i=0;i<100000;i++)CHECK(r.next_ms()==30000);r.connected();CHECK(r.next_ms()==1000);});
test("no idle CAN or boot heat replay",[]{int n=0;leaf::Control c([&](const leaf::Frame&){++n;return true;});c.tick(0);c.tick(9999999);CHECK(n==0);CHECK(!c.heating_requested());});
test("locked commissioning rejects transmission",[]{int n=0;leaf::Control c([&](const leaf::Frame&){++n;return true;});CHECK(!c.request(true,0,false,true));CHECK(!c.request(false,0,false,true));CHECK(n==0);});
test("2013-2015 on sequence and delayed completion",[]{std::vector<leaf::Frame> v;leaf::Control c([&](const leaf::Frame&f){v.push_back(f);return true;});CHECK(c.request(true,0,true,true));CHECK(v.size()==2);CHECK(v[0].id==0x679&&v[0].size==1&&v[0].data[0]==0);CHECK(v[1].id==0x5c0&&v[1].size==8);c.tick(99);CHECK(v.size()==2);for(int i=1;i<=24;i++)c.tick(i*100);CHECK(v.size()==26);for(int i=2;i<26;i++)CHECK(v[i].id==0x56e&&v[i].size==1&&v[i].data[0]==0x4e);c.tick(3299);CHECK(v.size()==26);c.tick(3300);CHECK(v.size()==27&&v.back().data[0]==0x46);CHECK(!c.busy());CHECK(c.heating_requested());});
test("off cancels all outstanding on frames",[]{std::vector<leaf::Frame> v;leaf::Control c([&](const leaf::Frame&f){v.push_back(f);return true;});CHECK(c.request(true,0,true,true));c.tick(100);CHECK(!c.request(true,150,true,true));CHECK(c.request(false,150,true,false));size_t first=v.size();for(int t=250;t<=4000;t+=100)c.tick(t);CHECK(v.size()==first+24);for(size_t i=first;i<v.size();i++)CHECK(v[i].data[0]==0x56);CHECK(!c.heating_requested());});
test("local heat timeout works without any Wi-Fi callback",[]{std::vector<leaf::Frame>v;leaf::Control c([&](const leaf::Frame&f){v.push_back(f);return true;});CHECK(c.request(true,0,true,true));for(int i=1;i<=24;i++)c.tick(i*100);c.tick(3300);size_t n=v.size();c.tick(899999);CHECK(v.size()==n);c.tick(900000);CHECK(v.size()==n+2);for(int i=1;i<=24;i++)c.tick(900000+i*100);CHECK(v.back().data[0]==0x56);CHECK(!c.heating_requested());});
test("low battery blocks on but permits off",[]{leaf::Control c([](const leaf::Frame&){return true;});CHECK(!c.request(true,0,true,false));CHECK(c.request(false,0,true,false));});
test("TX failure aborts sequence without replays",[]{int n=0;leaf::Control c([&](const leaf::Frame&){return ++n<3;});CHECK(c.request(true,0,true,true));c.tick(100);CHECK(!c.busy());c.tick(200);CHECK(n==3);CHECK(c.heating_requested());});
test("late scheduler never bursts missed heater requests",[]{std::vector<leaf::Frame>v;leaf::Control c([&](const leaf::Frame&f){v.push_back(f);return true;});CHECK(c.request(true,0,true,true));c.tick(2000);CHECK(v.size()==2);CHECK(!c.busy());});
test("authentication rejects empty or partial credentials",[]{CHECK(!leaf::authorized("",""));CHECK(!leaf::authorized("x","long-local-key"));CHECK(leaf::authorized("long-local-key","long-local-key"));});
std::cout<<count<<" tests, "<<failures<<" failures\n";return failures?1:0;}

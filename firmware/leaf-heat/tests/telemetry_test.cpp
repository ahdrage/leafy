#include "telemetry.hpp"
#include <cassert>
#include <iostream>
int main(){
 leaf::BatteryTelemetry t;
 assert(!t.valid());
 const uint8_t half[]={0x7d,0,0,0,0,0,0,0}; // 500 tenths
 assert(!t.receive(0x55b,half,1,false,false,100));
 assert(!t.receive(0x123,half,8,false,false,100));
 assert(!t.receive(0x55b,half,8,true,false,100));
 assert(!t.receive(0x55b,half,8,false,true,100));
 assert(t.receive(0x55b,half,8,false,false,100));assert(t.tenths()==500);assert(t.age(5100)==5000);
 const uint8_t invalid[]={0xff,0xc0,0,0,0,0,0,0};
 assert(!t.receive(0x55b,invalid,8,false,false,10000));assert(t.age(10100)==10000);
 const uint8_t outOfRange[]={0xfa,0x40,0,0,0,0,0,0};
 assert(!t.receive(0x55b,outOfRange,8,false,false,10000));
 const uint8_t zero[8]={};assert(t.receive(0x55b,zero,8,false,false,20000));assert(t.tenths()==0);
 const uint8_t max[]={0xfa,0,0,0,0,0,0,0};assert(t.receive(0x55b,max,8,false,false,30000));assert(t.tenths()==1000);
 assert(t.age(180000)==150000);
 uint8_t dash[8]={};dash[4]=0xe1; // bit 7 is unrelated; low seven bits are 97%.
 assert(t.receive(0x1db,dash,8,false,false,180000));
 assert(t.tenths()==1000 && t.age(180000)==150000); // Dashboard must not refresh BMS.
 assert(!t.receive(0x1db,dash,7,false,false,190000));
 assert(!t.receive(0x1db,dash,8,true,false,190000));
 assert(!t.receive(0x1db,dash,8,false,true,190000));
 for(unsigned v=101;v<=127;++v){dash[4]=v;assert(!t.receive(0x1db,dash,8,false,false,190000));}
 dash[4]=0;assert(t.receive(0x1db,dash,8,false,false,200000));
 dash[4]=100;assert(t.receive(0x1db,dash,8,false,false,210000));
 std::cout<<"PASS BMS/dashboard decoding, invalid frames, endpoints and independent samples\n";
}

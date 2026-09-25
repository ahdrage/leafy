// Leaf wake/climate protocol derived from OVMS revision 85074a0ae7a983b308c6e2e081185492527ee073.
// Original authors and MIT terms: ../OVMS-NOTICE.txt; project provenance: ../../../CREDITS.md.
#pragma once
#include <cstdint>
#include <functional>
#include <string>
namespace leaf {
struct Frame { uint32_t id; uint8_t size; uint8_t data[8]{}; };
class Retry {
 uint32_t delay_=1000;
 public:
 uint32_t next_ms(){auto result=delay_;delay_=delay_<16000?delay_*2:30000;return result;}
 void connected(){delay_=1000;}
};
// Single-owner command sequencer. A reboot creates an idle object, never an On queue.
class Control {
 std::function<bool(const Frame&)> send_;
 bool active_=false,on_=false,heat_=false,enabled_=false;
 int sent_=0;
 uint64_t due_=0,finish_=0,off_due_=0;
 bool frame(uint32_t id,uint8_t size,uint8_t byte=0){Frame f{id,size,{byte}};return send_(f);}
 public:
 explicit Control(std::function<bool(const Frame&)> send):send_(send){}
 bool request(bool on,uint64_t now,bool enabled,bool battery_ok){
  if(!enabled||(on&&(!battery_ok||active_)))return false;
  active_=false;on_=on;enabled_=enabled;sent_=0;finish_=0;
  // On may have reached the car even if a later TX fails: keep the local Off timer.
  if(on){heat_=true;off_due_=now+900000;}
  if(!frame(0x679,1)||!frame(0x5c0,8))return false;
  active_=true;due_=now+100;return true;
 }
 void tick(uint64_t now){
  if(heat_&&off_due_&&now>=off_due_){off_due_=0;request(false,now,enabled_,false);}
  if(!active_||now<due_)return;
  // Missing a timing deadline abandons the command, never catches up in a burst.
  if(now>due_+250){active_=false;return;}
  if(sent_<24){
   if(!frame(0x56e,1,on_?0x4e:0x56)){active_=false;return;}
   ++sent_;
   if(on_&&sent_==23)finish_=now+1000;
   if(sent_==24){
    if(!on_){active_=false;heat_=false;off_due_=0;}
    else due_=finish_;
   }else due_=now+100;
  }else{frame(0x56e,1,0x46);active_=false;}
 }
 bool busy() const{return active_;}
 bool heating_requested() const{return heat_;}
};
inline bool authorized(const std::string &provided,const std::string &expected){
 if(expected.size()<12||provided.size()!=expected.size())return false;
 unsigned diff=0;for(size_t i=0;i<expected.size();++i)diff|=provided[i]^expected[i];return diff==0;
}
}

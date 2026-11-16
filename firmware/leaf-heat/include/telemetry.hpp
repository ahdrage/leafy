// SOC extraction derived from OVMS 85074a0; see ../OVMS-NOTICE.txt.
#pragma once
#include <cstdint>
namespace leaf {
// Owned by the control task; readers must use the firmware's telemetry mutex.
class BatteryTelemetry {
 int tenths_=-1,dashboard_percent_=-1;
 uint64_t sampled_=0,dashboard_sampled_=0;
 public:
 bool receive(uint32_t id,const uint8_t* data,unsigned length,bool extended,bool remote,uint64_t now){
  if(length!=8||extended||remote)return false;
  // 2013–2017 Leaf instrument SOC on EV-CAN; ZE1 uses a different signal.
  if(id==0x1db){
   const unsigned value=data[4]&0x7f;
   if(value>100)return false; // Includes 0x7f unavailable; retain last valid age.
   dashboard_percent_=static_cast<int>(value);dashboard_sampled_=now;return true;
  }
  if(id!=0x55b)return false;
  const unsigned value=(static_cast<unsigned>(data[0])<<2)|(data[1]>>6);
  if(value>1000)return false; // Includes the 0x3ff unavailable sentinel.
  tenths_=static_cast<int>(value);sampled_=now;return true;
 }
 bool dashboard_valid() const{return dashboard_percent_>=0;}
 int dashboard_percent() const{return dashboard_percent_;}
 uint64_t dashboard_age(uint64_t now) const{return now>=dashboard_sampled_?now-dashboard_sampled_:0;}
 bool valid() const{return tenths_>=0;}
 int tenths() const{return tenths_;}
 uint64_t age(uint64_t now) const{return now>=sampled_?now-sampled_:0;}
};
}

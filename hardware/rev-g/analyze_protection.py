"""Independent engineering estimates, not a substitute for surge/EMC testing."""
from pathlib import Path
import math,itertools,json
H=Path(__file__).resolve().parent
# Precision resistors include 0.1% initial + 25 ppm/K * 65 K (-40 C to +85 C).
# General resistors include 1% initial + 100 ppm/K * 65 K.
p_tol=.001+.000025*65;g_tol=.01+.0001*65
cut=[];restart=[]
for rt,rb,rh,rp,vref,ih,il,vol,hys in itertools.product(
 [680e3*(1-p_tol),680e3*(1+p_tol)], [47e3*(1-p_tol),47e3*(1+p_tol)],
 [10e6*(1-g_tol),10e6*(1+g_tol)],[470e3*(1-g_tol),470e3*(1+g_tol)],
 [.792,.808],[-100e-9,100e-9],[-300e-9,300e-9],[0,.3],[.005,.035]):
 # Conservative interpretation: TI hysteresis accuracy ±1.5 percentage points.
 # RESET released: R24+R25 parallels R22; output leakage contributes via R24.
 re=1/(1/rt+1/(rh+rp))
 cut.append(vref*(1+re/rb)+re*(ih+il*rp/(rh+rp)))
 vr=vref*(1+hys)
 restart.append(vr*(1+rt/rb+rt/rh)-vol*rt/rh+ih*rt)
nom_cut=.8*(1+1/(1/680e3+1/10470e3)/47e3)
nom_restart=.816*(1+680e3/47e3+680e3/10e6)
# Compare the same cable/ceramic input with and without the RC damping branch.
# RK4 integrates i_L, V_input, V_bulk. Ideal conducting D1, no TVS, no active load.
# Cable R includes source/connector/D1 incremental resistance. No compliance claim.
def simulate(L,rs,ci,cb,rd,damped):
 dt=min(math.sqrt(L*ci)/70,rs*ci/10,L/(rs+rd)/20)
 end=max(20*math.sqrt(L*cb),8*(rs+rd)*cb)
 steps=int(end/dt)+1;dt=end/steps
 x=(0.,0.,0.);peak=power=energy=0.
 def f(z):
  i,v,b=z;j=(v-b)/rd if damped else 0
  return ((16-rs*i-v)/L,(i-j)/ci,j/cb)
 for _ in range(steps):
  a=f(x);b=f(tuple(x[j]+dt*a[j]/2 for j in range(3)));c=f(tuple(x[j]+dt*b[j]/2 for j in range(3)));d=f(tuple(x[j]+dt*c[j] for j in range(3)))
  x=tuple(x[j]+dt*(a[j]+2*b[j]+2*c[j]+d[j])/6 for j in range(3))
  peak=max(peak,x[1]);p=((x[1]-x[2])/rd)**2 if damped else 0
  power=max(power,p);energy+=p*dt
 return peak,power,energy
results=[]
for L,rs,ci,esr in itertools.product([.5e-6,3e-6,10e-6],[.1,1.0],[.5e-6,2.42e-6],[.21,2.]):
 cb=47e-6*.8
 d=simulate(L,rs,ci,cb,1+esr,True);u=simulate(L,rs,ci,cb,1+esr,False)
 results.append(dict(L_uH=L*1e6,source_R_ohm=rs,ceramic_uF=ci*1e6,bulk_ESR_ohm=esr,with_RC_peak_V=d[0],without_RC_peak_V=u[0],R21_peak_W=d[1],R21_energy_J=d[2]))
# 4–11 uF effective assumed delay-cap envelope, not a measured KEMET bias curve.
r={'nominal_cutoff_VPWR_V':nom_cut,'nominal_recovery_VPWR_V':nom_restart,
 'conservative_cutoff_VPWR_range': [min(cut),max(cut)],'conservative_recovery_VPWR_range':[min(restart),max(restart)],
 'delay_nominal_seconds':{'cutoff':-math.log(.28)*100e3*10e-6,'recovery':-math.log(.28)*1e6*10e-6},
 'delay_assumed_cap_envelope_seconds':{'cutoff':[-math.log(.31)*88e3*4e-6,-math.log(.25)*122e3*11e-6], 'recovery':[-math.log(.31)*877e3*4e-6,-math.log(.25)*1147e3*11e-6]},
 'adc_multiplier_on':1+1e6/(1/(1/47e3+1/100e3)),
 'adc_isolator_input_at_65V_when_off':65*47/1047,'adc_worst_poweroff_V_at_2uA':2e-6*100e3,
 'C15_full_rated_voltage_leakage_limit_uA':.01*47*63,
 'model_assumptions':'16 V hot plug, uncharged bulk 37.6 uF, ideal conducting diode, no clamp, no regulator load. Cable/ESR ranges are assumptions, not measured vehicle limits.',
 'hotplug_cases':results,
 'hotplug_summary':{'max_with_RC_V':max(x['with_RC_peak_V'] for x in results),'max_without_RC_V':max(x['without_RC_peak_V'] for x in results),'max_R21_W':max(x['R21_peak_W'] for x in results),'max_R21_J':max(x['R21_energy_J'] for x in results)}}
assert r['adc_isolator_input_at_65V_when_off']<3.6
assert r['conservative_cutoff_VPWR_range'][1]<r['conservative_recovery_VPWR_range'][0]
(H/'exports/protection-calculations.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k!='hotplug_cases'},indent=2))

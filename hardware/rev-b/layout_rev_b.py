"""Explicit Rev B critical layout. Reads preserved Rev A, never overwrites it."""
from pathlib import Path
import json, math, shutil
import pcbnew as p

H=Path(__file__).resolve().parent
SRC=H.parent
b=p.LoadBoard(str(SRC/'leaf-heat-v1.kicad_pcb'))
def v(xy): return p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
def xy(pt): return (p.ToMM(pt.x),p.ToMM(pt.y))
renames={'USB_CONN_DP':'USB_CONN_P','USB_CONN_DM':'USB_CONN_N','USB_DP':'USB_D_P','USB_DM':'USB_D_N'}
for n in b.GetNetInfo().NetsByNetcode().values():
 if n.GetNetname().lstrip('/') in renames:n.SetNetname('/'+renames[n.GetNetname().lstrip('/')])
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
for d in list(b.GetDrawings()):
 if isinstance(d,p.PCB_TEXT): b.RemoveNative(d)
b.SetCopperLayerCount(4)
b.SetLayerType(p.In1_Cu,p.LT_POWER);b.SetLayerType(p.In2_Cu,p.LT_POWER)
for fp in b.GetFootprints():
 for z in fp.Zones():
  if z.GetIsRuleArea():z.SetLayerSet(p.LSET.AllCuMask())
f={q.GetReference():q for q in b.GetFootprints()}
positions={
 'F1':(24,31.5,90),'D1':(24,24,270),'D3':(10,20,90),
 'C1':(10.5,12,90),'C2':(13.6,10.73,90),
 'C3':(25.2,13,0),'C4':(24,10.73,90),
 'R1':(21.9,17,90),'R2':(24.3,15.5,0),
 'U3':(15.7,28,270),'D4':(14.5,33.5,90),
 'C12':(15.065,22.5,90),'C13':(10.8,30.5,180),'R10':(20.5,29,0),
 'D2':(29,20.5,0), 'U4':(56.5,39,270), 'C14':(59.6,39.6,90),
 'R13':(59.8,11.5,180),'R14':(59.8,10,180),
 'R4':(59,5,90),'R8':(62,4.8,90),'C11':(61.7,7.6,0),
 'R11':(47.8,43,0),'R12':(62,37.5,0),
 'R15':(47.5,37,90),'R16':(47.5,40,90),
 'D5':(50.5,37,90),'R17':(52.6,37,90),
 'H3':(46,32,0),
}
for ref,(x,y,a) in positions.items():
 f[ref].SetPosition(v((x,y)));f[ref].SetOrientationDegrees(a)
def pad(ref,num): return next(q for q in f[ref].Pads() if q.GetNumber()==str(num))
def pt(ref,num): return xy(pad(ref,num).GetPosition())
def net(n): return next(q for q in b.GetNetInfo().NetsByNetcode().values() if q.GetNetname()=='/'+n)
def path(n,pts,w=.25,layer=p.F_Cu):
 for a,z in zip(pts,pts[1:]):
  if math.dist(a,z)<1e-6:continue
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(net(n));t.SetLocked(True);b.Add(t)
def via(n,at):
 q=p.PCB_VIA(b);q.SetPosition(v(at));q.SetWidth(p.FromMM(.65));q.SetDrill(p.FromMM(.3));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNet(net(n));q.SetLocked(True)
 q.SetFrontTentingMode(p.TENTING_MODE_TENTED);q.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(q)
def zone(n,layer,points,name,priority=1,clearance=.2):
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(net(n));z.SetLocalClearance(p.FromMM(clearance));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority)
 z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.15));z.SetMinIslandArea(2000000000000)
 z.SetZoneName(name);poly=z.Outline();poly.NewOutline()
 for x,y in points:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z);return z

# Local switching circuit: input bypass loop and quiet feedback are all on top.
path('VPWR',[pt('C2',1),(15.3,11.68),pt('U1',2)],.5)
path('VPWR',[pt('U1',2),pt('U1',3)],.5)
path('GND',[pt('C2',2),(15.5,9.78),pt('U1',1)],.5)
path('BUCK_SW',[pt('U1',8),(22.925,9.045),pt('L1',1)],.8)
path('BUCK_SW',[pt('U1',8),(23.86,10.095),pt('C4',2)],.5)
path('BUCK_BOOT',[pt('U1',7),(23.86,11.365),pt('C4',1)],.5)
path('BUCK_VCC',[pt('U1',6),(22.86,12.635),pt('C3',1)],.5)
path('BUCK_FB',[pt('U1',5),(21.875,15.5),pt('R2',1)],.25)
path('BUCK_FB',[(21.875,15.5),pt('R1',2)],.25)
# Kelvin output sense: route away from SW, from the final output capacitor.
path('3V3',[pt('C7',1),(29.3,14.225),(29.3,18.7),(22.775,18.7),pt('R1',1)],.25)
zone('3V3',p.F_Cu,[(26.3,4.4),(31.1,4.4),(31.1,14.6),(28.9,14.6),(28.9,7),(26.3,7)],'3V3 output capacitor bank',3)
zone('VPWR',p.F_Cu,[(9.4,12.9),(12.8,12.9),(13.6,11.1),(17.1,11.1),(17.1,13.25),(13.4,13.25),(12.1,14.5),(9.4,14.5)],'VIN local bypass copper',3)
zone('VPWR',p.B_Cu,[(7.5,12.8),(12,12.8),(12,19),(28.4,19),(28.4,25),(7.5,25)],'Protected input supply',3)
path('CAR_12V',[pt('J1',9),(24,41.84),(24,35.5)],1.0,p.B_Cu)
via('CAR_12V',(24,35.5));path('CAR_12V',[(24,35.5),pt('F1',1)],1.0)
path('CAR_FUSED',[pt('F1',2),pt('D1',2)],1.0)

# Internal power distribution. L2 is never used for signal or power tracks.
zone('3V3',p.In2_Cu,[(8,18),(20,18),(20,1.2),(61,1.2),(61,6.2),(51,6.2),(51,32),(8,32)],'3V3 distribution',5,.25)
zone('USB_5V',p.B_Cu,[(29.5,19.5),(32,19.5),(45,32.5),(45,35),(30,22),(29.5,22)],'USB bench supply feed',4)
zone('USB_5V',p.B_Cu,[(44,32),(60,32),(60,42.2),(44,42.2)],'USB bench supply local',6)

# USB: the short connector fanout and the main path are explicitly routed.
# U4 is rotated so its feed-through channels preserve the pair ordering.
DP='USB_CONN_P';DN='USB_CONN_N'
path(DP,[pt('J2','B6'),(56.75,42.15),(57.45,41.45),pt('U4',6)],.25)
path(DN,[pt('J2','A7'),(56.25,42.15),(55.55,41.45),pt('U4',4)],.25)
path(DP,[pt('U4',6),pt('U4',1)],.25)
path(DN,[pt('U4',4),pt('U4',3)],.25)
path(DP,[pt('U4',1),(57.45,35.2),(56.7,34.45)],.25)
path(DN,[pt('U4',3),(55.55,35.2),(56.3,34.45)],.25)
def offset_polyline(points,offset):
 lines=[]
 for a,c in zip(points,points[1:]):
  dx,dy=c[0]-a[0],c[1]-a[1];l=math.hypot(dx,dy);nx,ny=-dy/l,dx/l
  lines.append(((a[0]+offset*nx,a[1]+offset*ny),(c[0]+offset*nx,c[1]+offset*ny)))
 result=[lines[0][0]]
 for (a,z),(c,d) in zip(lines,lines[1:]):
  ax,ay=z[0]-a[0],z[1]-a[1];bx,by=d[0]-c[0],d[1]-c[1];det=ax*by-ay*bx
  if abs(det)<1e-9:result.append(z);continue
  k=((c[0]-a[0])*by-(c[1]-a[1])*bx)/det
  result.append((a[0]+k*ax,a[1]+k*ay))
 return result+[lines[-1][1]]
center=[(56.5,34.45),(56.5,33),(63.1,26.4),(63.1,12.5),(61.35,10.75),(61.1,10.75)]
pairp=offset_polyline(center,.2);pairn=offset_polyline(center,-.2)
path(DP,pairp,.25);path(DN,pairn,.25)
path(DP,[pairp[-1],pt('R14',1)],.25)
path(DN,[pairn[-1],pt('R13',1)],.25)
path('USB_D_P',[pt('U2',14),(56.975,8),pt('R14',2)],.25)
path('USB_D_N',[pt('U2',13),(56.975,9.5),pt('R13',2)],.25)

# USB-C duplicated contacts: only these short local bridges change layer.
# Both branches have equal total routed length; data's main route has no vias.
for n,refs,y in [(DP,['A6','B6'],45.8),(DN,['B7','A7'],46.6)]:
 for q in refs:
  a=pt('J2',q);xx=56+(a[0]-56)*1.4;z=(xx,y)
  path(n,[a,(a[0],44.3),(xx,44.3+abs(xx-a[0])),z],.2);via(n,z)
path(DN,[(54.95,46.6),(56.35,46.6)],.2,p.B_Cu)
leg=(1.6-.6*(math.sqrt(2)-1))/2
path(DP,[(55.65,45.8),(55.65,45.8-leg),(55.95,45.5-leg),(56.75,45.5-leg),(57.05,45.8-leg),(57.05,45.8)],.2,p.B_Cu)
for q in [(54,46.6),(55.75,47.7),(57.3,47.7),(58,45.8)]:via('GND',q)

# CAN enters through the protection device before reaching the transceiver.
path('CAN_L',[pt('U3',6),(15.065,31.2),(13.55,32.715),pt('D4',1),(13.55,38.78),pt('J1',2)],.25)
path('CAN_H',[pt('U3',7),(16.335,31.735),(15.45,32.62),pt('D4',2),(15.45,38.5),(15.155,38.795),pt('J1',7)],.25)

# Short decoupling / return connections and via drops into distribution planes.
# Candidates are outside the land pattern, not unfilled via-in-pad shortcuts.
def rect(q):
 r=q.GetBoundingBox();return (p.ToMM(r.GetLeft()),p.ToMM(r.GetTop()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))
def circle_rect_distance(c,r):return math.hypot(max(r[0]-c[0],0,c[0]-r[2]),max(r[1]-c[1],0,c[1]-r[3]))
def point_seg_distance(q,a,c):
 dx,dy=c[0]-a[0],c[1]-a[1];l=dx*dx+dy*dy
 if l==0:return math.dist(q,a)
 t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/l))
 return math.dist(q,(a[0]+t*dx,a[1]+t*dy))
def free_via(at,n):
 if not(.8<at[0]<64.2 and 1.3<at[1]<49.2):return False
 for fp in b.GetFootprints():
  for q in fp.Pads():
   if circle_rect_distance(at,rect(q))<.55:return False
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   if math.dist(at,xy(t.GetPosition()))<.83:return False
  elif t.GetNetname()!='/'+n and point_seg_distance(at,xy(t.GetStart()),xy(t.GetEnd()))<.325+p.ToMM(t.GetWidth())/2+.22:return False
 return True
def drop(ref,num,n):
 q=pad(ref,num);a=pt(ref,num);r=rect(q)
 assert q.GetNetname()=='/'+n,(ref,num,q.GetNetname(),n)
 candidates=[(r[0]-.6,a[1]),(r[2]+.6,a[1]),(a[0],r[1]-.6),(a[0],r[3]+.6)]
 for radius in [1.2,1.5,1.8,2.1]:
  for deg in range(0,360,45):candidates.append((a[0]+radius*math.cos(math.radians(deg)),a[1]+radius*math.sin(math.radians(deg))))
 def clear_path(z):
  for k in range(1,31):
   c=(a[0]+(z[0]-a[0])*k/30,a[1]+(z[1]-a[1])*k/30)
   for fp in b.GetFootprints():
    for other in fp.Pads():
     if other.GetNetname()!='/'+n and circle_rect_distance(c,rect(other))<.4:return False
   for t in b.GetTracks():
    if t.GetNetname()=='/'+n:continue
    if isinstance(t,p.PCB_VIA):
     if math.dist(c,xy(t.GetPosition()))<.2+.325+.2:return False
    elif t.GetLayer()==p.F_Cu and point_seg_distance(c,xy(t.GetStart()),xy(t.GetEnd()))<.2+p.ToMM(t.GetWidth())/2+.2:return False
  return True
 for z in candidates:
  if free_via(z,n) and clear_path(z):path(n,[a,z],.4);via(n,z);return z
 raise RuntimeError(('No close plane via',ref,num))
seen=set()
for ref,fp in f.items():
 for q in fp.Pads():
  n=q.GetNetname().lstrip('/');key=(ref,q.GetNumber())
  if key in seen:continue
  seen.add(key)
  if n=='GND' and q.GetAttribute()==p.PAD_ATTRIB_SMD and q.GetNumber() not in ['19','9','SH']:
   drop(ref,q.GetNumber(),n)
  if n=='3V3' and q.GetAttribute()==p.PAD_ATTRIB_SMD and ref not in ['L1','R1']:
   drop(ref,q.GetNumber(),n)
for ref in ['D1','D2','D3','C1']:
 num=next(q.GetNumber() for q in f[ref].Pads() if q.GetNetname()=='/VPWR');drop(ref,num,'VPWR')
for ref,num in [('D2',2),('U4',5),('C14',1),('D5',1),('R17',1),('R15',1),('J2','A4'),('J2','A9')]:drop(ref,num,'USB_5V')
# Extra vias on ESP32 supply and converter output reduce common impedance.
for q in [(28.3,5.5),(28.3,6.5),(37.8,2),(38,3),(38,14),(16.3,8.6),(17.3,8.6)]:
 n='3V3' if q[0]>25 and q[1]<8 else 'GND'
 if free_via(q,n):via(n,q)

outline=[(.3,.3),(64.7,.3),(64.7,49.7),(.3,49.7)]
for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
 zone('GND',layer,outline,'Solid GND reference - no routing' if layer==p.In1_Cu else 'GND '+b.GetLayerName(layer),0,.2)
# Ground stitching candidates, checked against pads, drills and existing routes.
for y in [2,7,17,22,27,32,37,47]:
 for x in [2,7,32,37,44,49,60,63]:
  if (34<x<62 and y<1.3):continue
  if free_via((x,y),'GND'):via('GND',(x,y))
for fp in b.GetFootprints():
 for q in fp.Pads():
  if q.GetNetname()=='/GND':q.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)

b.GetTitleBlock().SetRevision('B');b.GetTitleBlock().SetTitle('Leaf Heat Wi-Fi / CAN — Rev B')
b.BuildConnectivity();p.SaveBoard(str(H/'leaf-heat-v2.kicad_pcb'),b)
print('Rev B critical placement, routing, and four copper layers saved.')
print('Footprints:',len(f),'tracks/vias:',len(b.GetTracks()))
for ref in positions:print(ref,[(q.GetNumber(),q.GetNetname(),xy(q.GetPosition())) for q in f[ref].Pads() if q.GetNumber()])

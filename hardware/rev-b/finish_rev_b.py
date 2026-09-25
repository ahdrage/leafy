"""Finish control-routed snapshot; deterministic rebuild, preserves Rev A."""
from pathlib import Path
import pcbnew as p, math, json
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'exports/routed-backup.kicad_pcb'))
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q):return (p.ToMM(q.x),p.ToMM(q.y))
f={q.GetReference():q for q in b.GetFootprints()}
def pad(r,n):return next(q for q in f[r].Pads() if q.GetNumber()==str(n))
def path(n,points,w=.25,layer=p.F_Cu):
 for a,z in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);b.Add(t)
def via(n,q):
 t=p.PCB_VIA(b);t.SetPosition(v(q));t.SetWidth(p.FromMM(.65));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
# Clear the CAN entry and protection component courtyard.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/GND' and ((isinstance(t,p.PCB_VIA) and xy(t.GetPosition())==(14.5,33.9)) or (not isinstance(t,p.PCB_VIA) and xy(t.GetStart())==(14.5,32.5625))):b.RemoveNative(t)
f['D4'].SetPosition(v((14.5,34.2)))
path('GND',[xy(pad('D4',3).GetPosition()),(14.5,34.3)],.4);via('GND',(14.5,34.3))
# Short reset connection; only the slow control line uses a back-layer bridge.
path('ESP_EN',[(39.25,3.5),(40.4,3.5)],.25);via('ESP_EN',(40.4,3.5))
path('ESP_EN',[(40.4,3.5),(40.4,7.975),(36.825,7.975)],.25,p.B_Cu)
via('ESP_EN',(36.825,7.975));path('ESP_EN',[(36.825,7.975),(36.825,6.8)],.25)
# 0.23/0.17 mm is the starting geometry for the nominal 0.1855 mm prepreg.
# Manufacturer must confirm 90-ohm impedance with actual finished stackup/mask.
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in ['/USB_CONN_P','/USB_CONN_N','/USB_D_P','/USB_D_N'] and p.ToMM(t.GetWidth())==.25:t.SetWidth(p.FromMM(.23))
# Normalize small fine-pitch escapes from the router to a declared width.
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetWidth())<.2:t.SetWidth(p.FromMM(.2))
# Match the shorter USB leg with one broad, gentle offset at the ESD fanout.
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/USB_CONN_N' and xy(t.GetStart())==(55.55,37.8625) and xy(t.GetEnd())==(55.55,35.2):b.RemoveNative(t)
path('USB_CONN_N',[(55.55,37.8625),(55.55,37.3),(54.75,36.5),(54.75,36.0),(55.55,35.2)],.23)
# Keep same-layer pours away from the long coupled pair; L2 remains solid GND.
# Polygon is offset 0.95 mm each side of the pair center, following bends.
def offset_polyline(points,offset):
 lines=[]
 for a,c in zip(points,points[1:]):
  dx,dy=c[0]-a[0],c[1]-a[1];l=math.hypot(dx,dy);nx,ny=-dy/l,dx/l
  lines.append(((a[0]+offset*nx,a[1]+offset*ny),(c[0]+offset*nx,c[1]+offset*ny)))
 result=[lines[0][0]]
 for (a,z),(c,d) in zip(lines,lines[1:]):
  ax,ay=z[0]-a[0],z[1]-a[1];bx,by=d[0]-c[0],d[1]-c[1];det=ax*by-ay*bx
  k=((c[0]-a[0])*by-(c[1]-a[1])*bx)/det
  result.append((a[0]+k*ax,a[1]+k*ay))
 return result+[lines[-1][1]]
center=[(56.5,34.45),(56.5,33),(63.1,26.4),(63.1,12.5),(61.35,10.75),(61.1,10.75)]
z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayer(p.F_Cu);z.SetZoneName('USB pair copper clearance corridor')
z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False);z.SetDoNotAllowZoneFills(True)
poly=z.Outline();poly.NewOutline()
for q in offset_polyline(center,.95)+list(reversed(offset_polyline(center,-.95))):poly.Append(v(q))
b.Add(z)
# Clear, consistent and legible silkscreen.
for d in list(b.GetDrawings()):
 if isinstance(d,p.PCB_TEXT):b.RemoveNative(d)
def label(s,q,size=1,layer=p.F_SilkS):
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(q));t.SetTextSize(v((size,size)));t.SetTextThickness(p.FromMM(.13));t.SetLayer(layer)
 if layer==p.B_SilkS:t.SetMirrored(True)
 b.Add(t)
label('LEAF HEAT',(12,2),1.1)
label('RESET',(31,30.5),.85);label('BOOT',(42,30.5),.85)
label('REV B / 4 LAYERS',(32.5,16),1.8,p.B_SilkS)
label('ENGINEERING PROTOTYPE',(32.5,20),1.1,p.B_SilkS)
label('Nissan ZE0 cable only',(32.5,25),1,p.B_SilkS)
label('12V:9  GND:3  H:7  L:2',(32.5,28),1,p.B_SilkS)
label('NO CAN TERMINATION',(32.5,35),1,p.B_SilkS)
def rect(item,padding=0):
 r=item.GetBoundingBox();return [p.ToMM(r.GetX())-padding,p.ToMM(r.GetY())-padding,p.ToMM(r.GetRight())+padding,p.ToMM(r.GetBottom())+padding]
def overlap(a,z):return a[0]<z[2] and a[2]>z[0] and a[1]<z[3] and a[3]>z[1]
blocks=[]
for fp in b.GetFootprints():
 for q in fp.Pads():blocks.append(rect(q,.24))
 for g in fp.GraphicalItems():
  if g.GetLayer()==p.F_SilkS:blocks.append(rect(g,.14))
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_SilkS:blocks.append(rect(d,.14))
for fp in sorted(b.GetFootprints(),key=lambda fp:fp.GetReference()):
 if fp.GetReference().startswith('H'):continue
 ref=fp.Reference();ref.SetVisible(True);ref.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));ref.SetTextSize(v((.8,.8)));ref.SetTextThickness(p.FromMM(.12))
 x,y=xy(fp.GetPosition());candidates=[(x,y-2),(x,y+2),(x-2.5,y),(x+2.5,y)]
 for radius in [2.5,3,3.5,4,4.5,5,6,7,8,10,12]:
  for dx,dy in [(0,-1),(0,1),(-1,0),(1,0),(-.7,-.7),(.7,-.7),(-.7,.7),(.7,.7)]:candidates.append((x+radius*dx,y+radius*dy))
 if fp.GetReference()=='U2':candidates.insert(0,(48,16.5))
 if fp.GetReference()=='J1':candidates.insert(0,(7,35))
 if fp.GetReference()=='J2':candidates.insert(0,(63,46))
 for q in candidates:
  ref.SetPosition(v(q));r=rect(ref,.15)
  if r[0]<.35 or r[1]<.35 or r[2]>64.65 or r[3]>49.65:continue
  if not any(overlap(r,z) for z in blocks):blocks.append(r);break
 else:raise RuntimeError('Cannot place '+fp.GetReference())
b.BuildConnectivity();p.SaveBoard(str(H/'leaf-heat-v2.kicad_pcb'),b)
# Loading a renamed snapshot may create a default project; restore explicit rules.
pro=json.loads((H.parent/'leaf-heat-v1.kicad_pro').read_text())
renames={'USB_CONN_DP':'USB_CONN_P','USB_CONN_DM':'USB_CONN_N','USB_DP':'USB_D_P','USB_DM':'USB_D_N'}
for n in pro['net_settings']['netclass_patterns']:
 for old,new in renames.items():
  if n['pattern']=='/'+old:n['pattern']='/'+new
for n in pro['net_settings']['classes']:
 if n['name']=='USB':n.update(clearance=.15,track_width=.23,diff_pair_width=.23,diff_pair_gap=.17,diff_pair_via_gap=.25)
ds=pro['board']['design_settings'];ds['diff_pair_dimensions']=[{'width':.23,'gap':.17,'via_gap':.25}]
ds['track_widths']=[0,.2,.23,.25,.4,.5,.8,1.0]
ds['rules']['min_track_width']=.2
assert not ds['drc_exclusions']
(H/'leaf-heat-v2.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
print('Finished Rev B. Run native DRC and the independent layout audit.')

"""Import local routing, finish copper planes/metadata and place legible labels."""
from pathlib import Path
import json, math
import pcbnew as p
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'leaf-heat-v1.kicad_pcb'))
assert p.ImportSpecctraSES(b,str(H/'exports'/'leaf-heat-v1.ses'))
def v(xy):return p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
def path(n,pts,w=.25,layer=p.F_Cu):
 for a,z in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));b.Add(t)
def via(n,xy):
 t=p.PCB_VIA(b);t.SetPosition(v(xy));t.SetWidth(p.FromMM(.65));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));b.Add(t)
# Fine-pitch escapes that the router's 0.6 mm power net cannot fit.
path('USB_5V',[(58.4,43.32),(58.4,41.1)],.2);via('USB_5V',(58.4,41.1))
path('USB_5V',[(56,37.8625),(56,36.7)],.3);via('USB_5V',(56,36.7))
path('USB_5V',[(58.4,41.1),(58.4,39.1),(56,36.7)],.4,p.B_Cu)
path('GND',[(56,40.1375),(56,40.95)],.25);via('GND',(56,40.95))

for layer in [p.F_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/GND'));z.SetLocalClearance(p.FromMM(.25));z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL if layer==p.F_Cu else p.ZONE_CONNECTION_FULL)
 outline=z.Outline();outline.NewOutline()
 for x,y in [(0.3,0.3),(64.7,0.3),(64.7,49.7),(.3,49.7)]:outline.Append(p.FromMM(x),p.FromMM(y))
 z.SetZoneName('Ground '+b.GetLayerName(layer));b.Add(z)
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)

parts={r['ref']:r for r in json.loads((H/'parts.json').read_text())}
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref in parts:
  part=parts[ref]
  for name,val in [('MPN',part['mpn']),('Manufacturer',part['manufacturer']),('Datasheet',part['datasheet'])]:
   f.SetField(name,val);f.GetField(name).SetVisible(False)
 else:
  f.SetBoardOnly(True);f.SetAttributes(f.GetAttributes()|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
for net in b.GetNetInfo().NetsByNetcode().values():
 name=net.GetNetname()
 if name.startswith('unconnected-') and '/' in name:net.SetNetname(name.replace('/','{slash}'))

# Preserve footprint outlines; replace only free board text and move reference fields.
for d in list(b.GetDrawings()):
 if isinstance(d,p.PCB_TEXT):b.Remove(d)
def text(s,xy,size=1,layer=p.F_SilkS):
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(v(xy));t.SetTextSize(v((size,size)));t.SetTextThickness(p.FromMM(.13));t.SetLayer(layer)
 if layer==p.B_SilkS:t.SetMirrored(True)
 b.Add(t);return t
text('LEAF HEAT',(12,2),1.1)
text('RESET',(31,30.5),.85);text('BOOT',(42,30.5),.85)
text('REV A / Wi-Fi + CAN',(32.5,20),1.8,p.B_SilkS)
text('ENGINEERING PROTOTYPE',(32.5,24),1.1,p.B_SilkS)
text('Nissan ZE0 cable only',(25,29),1,p.B_SilkS)
text('12V:9  GND:3  H:7  L:2',(25,32),1,p.B_SilkS)
text('NO CAN TERMINATION',(25,35),1,p.B_SilkS)
def rect(item,pad=0):
 r=item.GetBoundingBox();return [p.ToMM(r.GetX())-pad,p.ToMM(r.GetY())-pad,p.ToMM(r.GetRight())+pad,p.ToMM(r.GetBottom())+pad]
def overlap(a,z):return a[0]<z[2] and a[2]>z[0] and a[1]<z[3] and a[3]>z[1]
blocks=[]
for f in b.GetFootprints():
 for pad in f.Pads():blocks.append(rect(pad,.24))
 for g in f.GraphicalItems():
  if g.GetLayer()==p.F_SilkS:blocks.append(rect(g,.14))
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_SilkS:blocks.append(rect(d,.14))
for f in sorted(b.GetFootprints(),key=lambda f:f.GetReference()):
 if f.GetReference().startswith('H'):continue
 ref=f.Reference();ref.SetVisible(True);ref.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));ref.SetTextSize(v((.8,.8)));ref.SetTextThickness(p.FromMM(.12))
 x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)
 candidates=[(x,y-2),(x,y+2),(x-2.5,y),(x+2.5,y)]
 for radius in [2.5,3,3.5,4,4.5,5,6,7,8,10,12]:
  for dx,dy in [(0,-1),(0,1),(-1,0),(1,0),(-.7,-.7),(.7,-.7),(-.7,.7),(.7,.7)]:candidates.append((x+radius*dx,y+radius*dy))
 if f.GetReference()=='U2':candidates.insert(0,(48,16.5))
 if f.GetReference()=='J1':candidates.insert(0,(7,35))
 if f.GetReference()=='J2':candidates.insert(0,(63,46))
 chosen=False
 for xy in candidates:
  ref.SetPosition(v(xy));r=rect(ref,.15)
  if r[0]<.35 or r[1]<.35 or r[2]>64.65 or r[3]>49.65:continue
  if not any(overlap(r,z) for z in blocks):blocks.append(r);chosen=True;break
 if not chosen:print('Reference needs manual placement:',f.GetReference())
b.BuildConnectivity()
p.SaveBoard(str(H/'leaf-heat-v1.kicad_pcb'),b)
print('Finished board saved; run native DRC with zone refill next.')

"""Final hand-routed escapes and documented footprint finishing corrections."""
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'leaf-heat-v1.kicad_pcb'))
def v(xy):return p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
def path(n,pts,w=.25,layer=p.F_Cu):
 for a,z in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));b.Add(t)
def via(n,xy):
 t=p.PCB_VIA(b);t.SetPosition(v(xy));t.SetWidth(p.FromMM(.65));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/USB_5V':
  a,z=t.GetStart(),t.GetEnd()
  if (a.x,a.y,z.x,z.y)==tuple(p.FromMM(x) for x in [58.4,43.32,58.4,41.1]):b.RemoveNative(t)
path('USB_5V',[(58.4,43.32),(58.4,45.3)],.2);via('USB_5V',(58.4,45.3))
path('USB_5V',[(58.4,45.3),(58.4,41.1)],.4,p.B_Cu)
path('USB_5V',[(53.6,43.32),(53.6,43.85),(54.3,44.55),(54.3,46.2)],.2);via('USB_5V',(54.3,46.2))
path('USB_5V',[(54.3,46.2),(57.5,46.2),(58.4,45.3)],.4,p.B_Cu)
path('3V3',[(35.175,11.5),(35.175,14)],.3)
for f in list(b.GetFootprints()):
 if f.GetReference()=='J2':
  for pad in f.Pads():
   if pad.GetNetname()=='/GND':pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
 if f.GetReference()=='U2':
  for g in list(f.GraphicalItems()):
   if g.GetLayer()!=p.F_SilkS or not isinstance(g,p.PCB_SHAPE):continue
   a,z=g.GetStart(),g.GetEnd()
   if a.y<p.FromMM(.3) and z.y<p.FromMM(.3):f.RemoveNative(g)
   else:
    if a.y<p.FromMM(.3):g.SetStart(p.VECTOR2I(a.x,p.FromMM(.3)))
    if z.y<p.FromMM(.3):g.SetEnd(p.VECTOR2I(z.x,p.FromMM(.3)))
b.BuildConnectivity();p.SaveBoard(str(H/'leaf-heat-v1.kicad_pcb'),b)
print('Final connection corrections saved.')

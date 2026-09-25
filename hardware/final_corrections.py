"""Resolve DRC findings from fine-pitch USB escapes and a ground crossing."""
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
bad=[('/3V3',(35.175,11.5,35.175,14)),('/USB_5V',(58.4,43.32,58.4,45.3)),('/USB_5V',(58.4,45.3,58.4,41.1)),('/USB_5V',(58.4,41.1,58.4,41.1))]
for t in list(b.GetTracks()):
 a,z=t.GetStart(),t.GetEnd()
 for n,coords in bad:
  if t.GetNetname()==n and (a.x,a.y,z.x,z.y)==tuple(p.FromMM(x) for x in coords):b.RemoveNative(t);break
path('3V3',[(35.175,11.5),(34.4,11.5)],.3);via('3V3',(34.4,11.5))
path('3V3',[(35.175,14),(35.175,14.225),(34.6,14.8)],.3);via('3V3',(34.6,14.8))
path('3V3',[(34.4,11.5),(34.4,14.6),(34.6,14.8)],.3,p.B_Cu)
path('USB_5V',[(58.4,43.32),(58.4,43.85),(57.7,44.55),(57.7,45),(58,45.3),(58.4,45.3)],.2)
path('USB_5V',[(58.4,45.3),(57.9,44.8),(57.9,41.6),(58.4,41.1)],.4,p.B_Cu)
p.SaveBoard(str(H/'leaf-heat-v1.kicad_pcb'),b)
# Match the custom library's printed outline to the board-edge antenna overhang.
name='ESP32-C3-WROOM-02_0p3mm_Vias'
f=p.FootprintLoad(str(H/'Leaf.pretty'),name)
for g in list(f.GraphicalItems()):
 if g.GetLayer()!=p.F_SilkS or not isinstance(g,p.PCB_SHAPE):continue
 a,z=g.GetStart(),g.GetEnd();lim=p.FromMM(-7.7)
 if a.y<lim and z.y<lim:f.RemoveNative(g)
 else:
  if a.y<lim:g.SetStart(p.VECTOR2I(a.x,lim))
  if z.y<lim:g.SetEnd(p.VECTOR2I(z.x,lim))
p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP).FootprintSave(str(H/'Leaf.pretty'),f)
print('Final DRC corrections saved.')

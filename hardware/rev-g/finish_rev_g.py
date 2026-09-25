"""Fine-pitch supervisor escapes and local signal completion after SES import."""
from pathlib import Path
import math, pcbnew as p
H=Path(__file__).resolve().parent;B=H/'leaf-heat-v7.kicad_pcb';b=p.LoadBoard(str(B))
fps={f.GetReference():f for f in b.GetFootprints()}
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q):return p.ToMM(q.x),p.ToMM(q.y)
def pt(ref,num):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition())
def path(n,pts,w=.25,layer=p.F_Cu):
    for a,c in zip(pts,pts[1:]):
        if math.dist(a,c)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));b.Add(t)
def via(n,at):
    t=p.PCB_VIA(b);t.SetPosition(v(at));t.SetWidth(p.FromMM(.7));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
for t in list(b.GetTracks()):
    if t.GetNetname()=='/GND' and ((isinstance(t,p.PCB_VIA) and xy(t.GetPosition())==(20.7,44.5)) or (not isinstance(t,p.PCB_VIA) and {xy(t.GetStart()),xy(t.GetEnd())}=={(18.5,44.5),(20.7,44.5)})):b.RemoveNative(t)
path('GND',[pt('U5',8),(19,44.5),(19.8,45.3)]);via('GND',(19.8,45.3))
for n,num,at in [('UV_SENSE',3,(13.3,42.5)),('BUCK_EN',6,(13.3,44)),('UV_CTR',9,(20.7,44)),('UV_CTS',10,(20,43))]:
    points=[pt('U5',num),at] if n!='UV_CTS' else [pt('U5',num),(19.5,43.5),at]
    path(n,points);via(n,at)
# Delay capacitors are referenced to the same continuous inner ground plane.
via('UV_CTR',(14,53));path('UV_CTR',[pt('C19',1),(14,53)])
path('UV_CTR',[(20.7,44),(20.7,48.5),(21.5,49.3),(21.5,51),(18.3,54.2),(15.2,54.2),(14,53)],layer=p.B_Cu)
via('UV_CTS',(23.4375,47.4));path('UV_CTS',[pt('C18',1),(23.4375,47.4)])
path('UV_CTS',[(20,43),(22,43),(24.2,45.2),(24.2,46.6375),(23.4375,47.4)],layer=p.B_Cu)
# Resistive monitor paths are intentionally slow; use bottom-layer routing
# over ground instead of crossing the regulator switch node.
for ref,num,at in [('R22',2,(7.2,38.45)),('R23',1,(7.2,48.55)),('R24',2,(23,39.45))]:
    path('UV_SENSE',[pt(ref,num),at]);via('UV_SENSE',at)
path('UV_SENSE',[(13.3,42.5),(11.25,40.45),(9.2,38.45),(7.2,38.45)],layer=p.B_Cu)
path('UV_SENSE',[(7.2,38.45),(5.5,40.15),(5.5,46.85),(7.2,48.55)],layer=p.B_Cu)
path('UV_SENSE',[(13.3,42.5),(17.35,38.45),(22,38.45),(23,39.45)],layer=p.B_Cu)
via('BUCK_EN',(14.8,46.5))
path('BUCK_EN',[(13.3,44),(13.3,45),(14.8,46.5)],layer=p.B_Cu)
path('BUCK_EN',[(14.8,46.5),(22.2,46.5),(25,43.7),pt('R24',1)])
b.BuildConnectivity();p.SaveBoard(str(B),b)
print('Supervisor fine-pitch escapes completed.')

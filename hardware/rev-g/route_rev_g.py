"""Add deliberate plane connections; leave ordinary signals to the local router."""
from pathlib import Path
import math,json
import pcbnew as p
H=Path(__file__).resolve().parent;B=H/'leaf-heat-v7.kicad_pcb';b=p.LoadBoard(str(B))
fps={f.GetReference():f for f in b.GetFootprints()};W=HT=100
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q):return p.ToMM(q.x),p.ToMM(q.y)
def pt(ref,num):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition())
def path(n,pts,w=.3,layer=p.F_Cu):
    for a,c in zip(pts,pts[1:]):
        if math.dist(a,c)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);b.Add(t)
def via(n,at):
    t=p.PCB_VIA(b);t.SetPosition(v(at));t.SetWidth(p.FromMM(.7));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
# Reuse the geometrical clearance search, not the old board-generation actions.
src=(H.parent/'rev-e/build_rev_e.py').read_text();exec(src[src.index('def rect(q):'):src.index('seen=set()')])
path('3V3',[pt('C7',1),(39.5,30.9375),(39.4375,31),(18.65,31),pt('R1',1)],.3)
path('GND',[pt('C3',2),(31.5,24.4625)],.4);via('GND',(31.5,24.4625))
path('GND',[pt('R2',2),(27.7,27.55)],.4);via('GND',(27.7,27.55))
path('3V3',[pt('U6',14),pt('C20',1)],.3)
# Unused analog channels and their logic selects are grounded explicitly.
path('GND',[pt('U6',i) for i in range(4,8)],.25)
path('GND',[pt('U6',i) for i in range(8,14)],.25)
for num,at in [(8,(20.7,44.5)),(13,(20.7,42))]:
    path('GND',[pt('U5',num),at],.25);via('GND',at)
for ref,num,n in [('C16',1,'VPWR'),('C16',2,'GND'),('R22',1,'VPWR'),('R23',2,'GND'),('C17',2,'GND'),('C18',2,'GND'),('C19',2,'GND'),('U6',1,'3V3'),('C20',1,'3V3'),('C20',2,'GND'),('U6',7,'GND'),('U6',8,'GND'),('R26',2,'GND')]:drop(ref,num,n)
path('VPWR',[pt('R21',1),(7.95,22.5)],.6);via('VPWR',(7.95,22.5))
path('VPWR',[pt('R25',1),(23.05,37.5),(20,37.5)],.3);via('VPWR',(20,37.5))
# Supervisor bypass connection is short and separate from its SENSE node.
path('VPWR',[pt('C16',1),(13.8,36),(13.8,39.8),pt('U5',1)],.3)
b.BuildConnectivity();p.SaveBoard(str(B),b)
print('Rev G plane fanout and local bypasses added.')

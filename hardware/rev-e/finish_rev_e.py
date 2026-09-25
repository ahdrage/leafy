"""Finish connector silk and the 3.3 V connection across a supply-zone clearance."""
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent;B=H/'leaf-heat-v5.kicad_pcb'
b=p.LoadBoard(str(B));j=next(f for f in b.GetFootprints() if f.GetReference()=='J1')
name=str(j.GetFPID().GetLibItemName());lib=p.FootprintLoad(str(H/'Leaf.pretty'),name)
for f,maximum in [(j,99.7),(lib,8.7)]:
    for d in f.GraphicalItems():
        if d.GetLayer()!=p.F_SilkS:continue
        for getter,setter in [(d.GetStart,d.SetStart),(d.GetEnd,d.SetEnd)]:
            point=getter()
            if p.ToMM(point.y)>maximum:point.y=p.FromMM(maximum);setter(point)
p.FootprintSave(str(H/'Leaf.pretty'),lib)
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
# R6's original via falls inside the protected-input plane clearance. Bridge
# to a new 3.3 V via outside that region, clear of the CAN traces on the back.
if not any(isinstance(t,p.PCB_VIA) and t.GetPosition()==v((70.5,40)) for t in b.GetTracks()):
    net=b.FindNet('/3V3')
    for a,c in [((68.1,37),(68.1,37.6)),((68.1,37.6),(70.5,40))]:
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(.4));t.SetLayer(p.B_Cu);t.SetNet(net);t.SetLocked(True);b.Add(t)
    t=p.PCB_VIA(b);t.SetPosition(v((70.5,40)));t.SetWidth(p.FromMM(.7));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(net);t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
p.SaveBoard(str(B),b)
print('Connector silk and R6 supply connection finished.')

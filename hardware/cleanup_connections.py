from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'leaf-heat-v1.kicad_pcb'))
def xy(t):
 a,z=t.GetStart(),t.GetEnd();return tuple(round(p.ToMM(x),4) for x in [a.x,a.y,z.x,z.y])
rem=[(35.175,11.5,34.4,11.5),(35.175,14,35.175,14.225),(35.175,14.225,34.6,14.8),(34.4,11.5,34.4,14.6),(34.4,14.6,34.6,14.8),(34.4,11.5,34.4,11.5),(34.6,14.8,34.6,14.8)]
for t in list(b.GetTracks()):
 c=xy(t)
 if t.GetNetname()=='/3V3' and c in rem:b.RemoveNative(t)
 if t.GetNetname()=='/GND' and t.GetLayer()==p.F_Cu and c[:2]==(34.6949,13.199):b.RemoveNative(t)
 if t.GetNetname()=='/USB_5V' and t.GetLayer()==p.B_Cu and c[:2] in [(57.9,44.8),(57.9,41.6)]:t.SetWidth(p.FromMM(.2))
t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(35.175),p.FromMM(11.5)));t.SetEnd(p.VECTOR2I(p.FromMM(35.175),p.FromMM(14)));t.SetWidth(p.FromMM(.3));t.SetLayer(p.F_Cu);t.SetNet(b.FindNet('/3V3'));b.Add(t)
p.SaveBoard(str(H/'leaf-heat-v1.kicad_pcb'),b)

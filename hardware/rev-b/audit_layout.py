"""Independent geometric checks on the saved, filled Rev B PCB."""
from pathlib import Path
import pcbnew as p, collections, json, math
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'leaf-heat-v2.kicad_pcb'))
def xy(q):return (p.ToMM(q.x),p.ToMM(q.y))
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
gnd=[z for z in b.Zones() if z.GetNetname()=='/GND' and z.GetLayer()==p.In1_Cu and not z.GetIsRuleArea()]
assert len(gnd)==1
def on_ground(q,layer=p.In1_Cu):return any(z.HitTestFilledArea(layer,v(q)) for z in b.Zones() if z.GetNetname()=='/GND' and z.GetLayer()==layer and not z.GetIsRuleArea())
usb=['/USB_CONN_P','/USB_CONN_N','/USB_D_P','/USB_D_N']
reference=[];miss=[]
for t in tracks:
 if t.GetNetname() not in usb:continue
 # Every segment, including both edges and center, at <=0.05 mm intervals.
 a,c=xy(t.GetStart()),xy(t.GetEnd());L=math.dist(a,c);steps=max(1,math.ceil(L/.05));w=p.ToMM(t.GetWidth())
 nx,ny=(-(c[1]-a[1])/L,(c[0]-a[0])/L)
 layer=p.In1_Cu if t.GetLayer()==p.F_Cu else p.In2_Cu
 for i in range(steps+1):
  for offset in [-w/2,0,w/2]:
   q=(a[0]+(c[0]-a[0])*i/steps+nx*offset,a[1]+(c[1]-a[1])*i/steps+ny*offset)
   reference.append(q)
   if not on_ground(q,layer):miss.append({'net':t.GetNetname(),'reference':b.GetLayerName(layer),'point':q})
lengths={}
for n in usb:
 ts=[t for t in tracks if t.GetNetname()==n]
 lengths[n]={'main_mm':sum(p.ToMM(t.GetLength()) for t in ts if max(xy(t.GetStart())[1],xy(t.GetEnd())[1])<=43.32),'all_segments_mm':sum(p.ToMM(t.GetLength()) for t in ts),'vias':sum(t.GetNetname()==n for t in vias)}
# The bridge paths are short branches beneath USB-C, distinct from its main route.
P=lengths['/USB_CONN_P']['main_mm']+lengths['/USB_D_P']['main_mm']
N=lengths['/USB_CONN_N']['main_mm']+lengths['/USB_D_N']['main_mm']
inner=collections.Counter(b.GetLayerName(t.GetLayer()) for t in tracks if t.GetLayer() in [p.In1_Cu,p.In2_Cu])
antenna=[]
for y in [.35,.6,.85]:
 for x in range(35,62):
  for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
   if any(z.HitTestFilledArea(layer,v((x,y))) for z in b.Zones() if z.GetLayer()==layer and not z.GetIsRuleArea()):antenna.append((x,y,b.GetLayerName(layer)))
via_clearance_miss=[q for q in miss if any(math.dist(q['point'],xy(t.GetPosition())) <= p.ToMM(t.GetWidth(p.F_Cu))/2 + .201 for t in vias if t.GetNetname() in usb)]
unexplained_miss=[q for q in miss if q not in via_clearance_miss]
main_miss=[q for q in miss if q['point'][1]<43.32]
print('Main route ground failures',main_miss[:20], 'total',len(main_miss))
# Measure perpendicular spacing of the long, parallel sections from saved geometry.
pair_gaps=[]
for t in tracks:
 if t.GetNetname()!='/USB_CONN_P':continue
 a,c=xy(t.GetStart()),xy(t.GetEnd());L=math.dist(a,c)
 if L<2 or min(a[0],c[0])<56 or max(a[1],c[1])>34.45:continue
 ux,uy=(c[0]-a[0])/L,(c[1]-a[1])/L
 found=[]
 for n in tracks:
  if n.GetNetname()!='/USB_CONN_N':continue
  d,e=xy(n.GetStart()),xy(n.GetEnd());NL=math.dist(d,e)
  if abs(ux*(e[1]-d[1])-uy*(e[0]-d[0]))>1e-5:continue
  proj=sorted([(d[0]-a[0])*ux+(d[1]-a[1])*uy,(e[0]-a[0])*ux+(e[1]-a[1])*uy])
  overlap=min(L,proj[1])-max(0,proj[0])
  if overlap<1:continue
  gap=abs(ux*(d[1]-a[1])-uy*(d[0]-a[0]))-(p.ToMM(t.GetWidth())+p.ToMM(n.GetWidth()))/2
  if gap<1:found.append((gap,overlap))
 assert len(found)==1,(a,c,found)
 pair_gaps.append({'gap_mm':found[0][0],'parallel_overlap_mm':found[0][1]})
assert sum(q['parallel_overlap_mm'] for q in pair_gaps)>20
assert all(.149<q['gap_mm']<.151 for q in pair_gaps)
report={'long_parallel_sections':pair_gaps,'board':'leaf-heat-v2','copper_layers':b.GetCopperLayerCount(),'tracks_per_layer':dict(collections.Counter(b.GetLayerName(t.GetLayer()) for t in tracks)),'track_widths_mm':dict(collections.Counter(p.ToMM(t.GetWidth()) for t in tracks)),'ground_through_vias':sum(t.GetNetname()=='/GND' for t in vias),'all_through_vias':len(vias),'usb_lengths':lengths,'usb_main_total_P_mm':P,'usb_main_total_N_mm':N,'usb_main_skew_mm':abs(P-N),'usb_ground_reference_samples':len(reference),'usb_reference_missing_samples':len(miss),'usb_main_reference_missing_samples':len(main_miss),'usb_via_clearance_samples':len(via_clearance_miss),'usb_unexplained_reference_gaps':unexplained_miss,'usb_missing_sample_examples':miss[:20],'inner_layer_tracks':dict(inner),'antenna_keepout_copper_samples':antenna,'scope':'Geometry only. Excludes lengths inside the connector, ESD package, resistors and module. No signal-integrity, EMI, thermal or physical validation implied.'}
(H/'exports/layout-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert b.GetCopperLayerCount()==4 and not inner and not antenna
assert abs(P-N)<.1
assert not main_miss and not unexplained_miss,'Some USB samples lack adjacent GND. Inspect before claiming continuous reference.'

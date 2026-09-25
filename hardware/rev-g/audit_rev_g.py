"""Read-only cross-check against the schematic, BOM and Rev F baseline."""
from pathlib import Path
import json,hashlib,xml.etree.ElementTree as ET,heapq,math,collections
import pcbnew as p
H=Path(__file__).resolve().parent;E=H/'exports';F=H.parent/'rev-f'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'));f=p.LoadBoard(str(F/'leaf-heat-v6.kicad_pcb'))
fps={x.GetReference():x for x in b.GetFootprints()};old={x.GetReference():x for x in f.GetFootprints()}
parts={q['ref']:q for q in json.loads((H/'parts.json').read_text())}
root=ET.parse(E/'leaf-heat-v7.net.xml').getroot();sch={q.attrib['ref']:q for q in root.findall('./components/comp')}
assert len(parts)==55 and set(sch)-set(parts)=={f'TP{i}' for i in range(1,8)}
assert set(parts)<=set(sch)
def norm(n):return None if not n or n.startswith('unconnected-') else n.removeprefix('/')
netmap={}
for net in root.findall('./nets/net'):
 for node in net.findall('node'):netmap[(node.attrib['ref'],node.attrib['pin'])]=norm(net.attrib['name'])
for ref,q in parts.items():
 fp=fps[ref];c=sch[ref]
 assert fp.GetValue()==c.findtext('value')==q['value'],ref
 assert fp.GetFPIDAsString()==c.findtext('footprint')==q['footprint'],ref
 for k in ['MPN','Manufacturer','Assembly']:
  val=c.find('./property[@name="%s"]'%k).attrib['value']
  assert fp.GetField(k).GetText()==val==q[{'MPN':'mpn','Manufacturer':'manufacturer','Assembly':'assembly'}[k]],(ref,k)
 for pad in fp.Pads():
  pin=pad.GetNumber()
  if not pin:continue
  assert norm(pad.GetNetname())==q['nets'][pin]==netmap.get((ref,pin)),(ref,pin,pad.GetNetname())
# Independent key electrical expectations, beyond consistency with parts.json.
checks={
 ('U5','1'):'VPWR',('U5','3'):'UV_SENSE',('U5','6'):'BUCK_EN',('U5','8'):'GND',('U5','9'):'UV_CTR',('U5','10'):'UV_CTS',('U5','13'):'GND',
 ('U1','3'):'BUCK_EN',('R21','1'):'VPWR',('R21','2'):'BULK_DAMPED',('C15','1'):'BULK_DAMPED',('C15','2'):'GND',
 ('U6','1'):'3V3',('U6','2'):'BAT_DIV',('U6','3'):'BAT_SENSE',('U6','14'):'3V3',
 ('R7','2'):'BAT_DIV',('R8','1'):'BAT_DIV',('C11','1'):'BAT_DIV',('U2','18'):'BAT_SENSE',('R26','1'):'BAT_SENSE',('R26','2'):'GND',
 ('U3','5'):'GND',('U3','8'):'CAN_STB',('J1','2'):'CAN_L',('J1','7'):'CAN_H',('J1','9'):'CAR_12V',('J1','3'):'GND'}
for key,n in checks.items():assert netmap[key]==n,(key,netmap[key],n)
assert parts['U5']['mpn']=='TPS3760A012DYYR'
assert parts['U6']['mpn']=='TMUX1511PWR'
for n in range(4,14):assert netmap['U6',str(n)]=='GND'
for ref in ['J1','J3','U2','U3','U4','H1','H2','H3','H4']:
 assert fps[ref].GetPosition()==old[ref].GetPosition() and fps[ref].GetOrientationDegrees()==old[ref].GetOrientationDegrees(),ref
# Only intended existing pin nets differ.
changes=[]
for ref,q in parts.items():
 if ref not in old:continue
 oldnets={x.GetNumber():norm(x.GetNetname()) for x in old[ref].Pads() if x.GetNumber()}
 for pin,net in q['nets'].items():
  if oldnets.get(pin)!=net:changes.append([ref,pin,oldnets.get(pin),net])
assert sorted((a,b) for a,b,_,_ in changes)==sorted([('U1','3'),('R7','2'),('R8','1'),('C11','1')]),changes
assert (H/'leaf-heat-v7.kicad_dru').read_bytes()==(F/'leaf-heat-v6.kicad_dru').read_bytes()
for sw in ['SW1','SW2']:
 pads=list(fps[sw].Pads());groups=collections.defaultdict(list)
 for x in pads:groups[x.GetNumber()].append(x.GetPosition())
 assert len(groups['1'])==len(groups['2'])==2
 for pair in groups.values():assert abs(p.ToMM((pair[0]-pair[1]).EuclideanNorm())-6.5)<.001
 assert abs(p.ToMM(groups['1'][0].y-groups['2'][0].y))==4.5
# Copper route length between pad centres, no zones needed for these signal nets.
def route_length(board,refa,pina,refb,pinb):
 fs={x.GetReference():x for x in board.GetFootprints()}
 a=next(x for x in fs[refa].Pads() if x.GetNumber()==pina);z=next(x for x in fs[refb].Pads() if x.GetNumber()==pinb)
 graph=collections.defaultdict(list)
 def node(x,layer):return (x.x,x.y,layer)
 for track in board.GetTracks():
  if track.GetNetCode()!=a.GetNetCode():continue
  if isinstance(track,p.PCB_VIA):
   layers=list(track.GetLayerSet().Seq())
   for layer in layers:
    for layer2 in layers:graph[node(track.GetPosition(),layer)].append((node(track.GetPosition(),layer2),0))
  else:
   na=node(track.GetStart(),track.GetLayer());nb=node(track.GetEnd(),track.GetLayer());d=p.ToMM(track.GetLength())
   graph[na].append((nb,d));graph[nb].append((na,d))
 start=node(a.GetPosition(),p.F_Cu);end=node(z.GetPosition(),p.F_Cu);dist={start:0};todo=[(0,start)]
 while todo:
  d,n=heapq.heappop(todo)
  if n==end:return d
  if d>dist[n]:continue
  for nn,w in graph[n]:
   if d+w<dist.get(nn,math.inf):dist[nn]=d+w;heapq.heappush(todo,(d+w,nn))
 raise AssertionError('Cannot find route '+refa+pina+' '+refb+pinb)
lengths={}
for name,args in [('VCC',('U1','6','C3','1')),('FB',('U1','5','R2','1')),('BOOT',('U1','7','C4','1'))]:
 lengths[name]={'rev_f_mm':route_length(f,*args),'rev_g_mm':route_length(b,*args)}
 assert lengths[name]['rev_g_mm']<lengths[name]['rev_f_mm']
paste={ref for ref,fp in fps.items() if any(p.F_Paste in x.GetLayerSet().Seq() for x in fp.Pads())}
assert paste=={'U1','U2','U4','U5','U6','L1'}
assert sha(F/'leaf-heat-v6.kicad_pcb')=='5b63416fd1c055faa55a8f8dfb4ba75da2f3052ad8de3801168372b136d7357c'
assert sha(F/'leaf-heat-v6.kicad_sch')=='e3e0ba99f9ab009493ed48b9decf28f02613305b7fe795ed2e3e3c0c555f89f2'
drc=json.loads((E/'drc-final.json').read_text());erc=json.loads((E/'erc.json').read_text())
assert not any(drc[k] for k in ['violations','unconnected_items','schematic_parity'])
assert not any(x['violations'] for x in erc['sheets'])
r={'components_checked':55,'factory_refs':sorted(paste),'hand_components':49,'electrical_pin_net_changes_from_F':changes,'regulator_route_lengths':lengths,'rev_f_preserved':True,'DRC_violations':0,'ERC_violations':0,'unconnected':0,'parity_errors':0,'board_sha256':sha(H/'leaf-heat-v7.kicad_pcb'),'schematic_sha256':sha(H/'leaf-heat-v7.kicad_sch'),'limits':'Static checks only; assembler exposed-pad approval and powered prototype tests remain.'}
(E/'independent-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

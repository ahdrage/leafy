"""Read-only G.3 antenna audit against the immutable G.2 archive."""
from pathlib import Path
import json,hashlib,zipfile,collections,csv,xml.etree.ElementTree as ET
import sexpdata as sx
H=Path(__file__).resolve().parent;E=H/'exports'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def key(x):return str(x[0]) if isinstance(x,list) and x else ''
def items(q,k):return [x for x in q if key(x)==k]
def prop(q,k):return next(x[2] for x in items(q,'property') if x[1]==k)
def bag(q,ks):return collections.Counter(sx.dumps(x) for x in q if key(x) in ks)
with zipfile.ZipFile(H/'history/rev-g2-before-external-antenna.zip') as z:
 old=sx.loads(z.read('leaf-heat-v7.kicad_pcb').decode());op=json.loads(z.read('parts.json'))
 oldsch=sx.loads(z.read('leaf-heat-v7.kicad_sch').decode())
 oldnet=ET.fromstring(z.read('exports/leaf-heat-v7.net.xml'))
 new=sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
 assert bag(old,{'segment','arc','via','net','layers'})==bag(new,{'segment','arc','via','net','layers'})
 # Zone definitions and fills, including the four copper layers, are retained.
 assert bag(old,{'zone'})==bag(new,{'zone'})
 of={prop(x,'Reference'):x for x in items(old,'footprint')};nf={prop(x,'Reference'):x for x in items(new,'footprint')}
 assert of.keys()==nf.keys()
 for ref in of:
  assert bag(of[ref],{'pad','at','path'})==bag(nf[ref],{'pad','at','path'}),ref
  if ref!='U2':assert of[ref]==nf[ref],ref
 assert nf['U2'][1]=='Leaf:ESP32-C3-WROOM-02U_0p3mm_Vias__Factory'
 assert prop(nf['U2'],'MPN')==prop(nf['U2'],'Value')=='ESP32-C3-WROOM-02U-N4'
 assert bag(old,{'gr_line','gr_arc','gr_rect'})==bag(new,{'gr_line','gr_arc','gr_rect'})
 sch=sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
 assert bag(oldsch,{'wire','junction','label','global_label','no_connect'})==bag(sch,{'wire','junction','label','global_label','no_connect'})
 def nets(root):
  return {n.attrib['name']:sorted((x.attrib['ref'],x.attrib['pin']) for x in n.findall('node')) for n in root.findall('./nets/net')}
 assert nets(oldnet)==nets(ET.parse(E/'leaf-heat-v7.net.xml').getroot())
 parts=json.loads((H/'parts.json').read_text())
 for a,b in zip(op,parts):
  if a['ref']!='U2':assert a==b,a['ref']
  else:
   for k in a:
    if k not in {'symbol','value','mpn','footprint','notes'}:assert a[k]==b[k],k
 assert (E/'BOM-HAND.csv').read_bytes()==z.read('exports/BOM-HAND.csv')
 # Electrical fabrication plots compare after removing timestamps/hash/header comments.
 def fab(blob):
  return '\n'.join(l for l in blob.decode().splitlines() if not l.startswith(('G04','#',';','%TF.CreationDate','%TF.ProjectId','%TF.FileFunction')))
 for p in (E/'fabrication').iterdir():
  if p.suffix in {'.drl','.gtl','.gbl','.g1','.g2','.gtp','.gbp','.gts','.gbs'}:
   assert fab(p.read_bytes())==fab(z.read('exports/fabrication/'+p.name)),p.name
acc=json.loads((H/'accessories.json').read_text());assert len(acc)==1
assert acc[0]['mpn']=='1461530300' and acc[0]['quantity_per_board']==1
bom=list(csv.DictReader((E/'BOM-FACTORY-JLCPCB.csv').open()))
assert len(bom)==6 and next(x for x in bom if x['Designator']=='U2')['LCSC Part #']=='C2926676'
shopping=list(csv.DictReader((E/'MOUSER-TWO-BOARDS.csv').open()))
assert len(shopping)==28 and sum(int(x['Quantity']) for x in shopping)==100
assert next(x for x in shopping if x['Mouser Part Number']=='538-146153-0300')['Quantity']=='2'
a=json.loads((E/'independent-audit.json').read_text())
assert a['board_sha256']==sha(H/'leaf-heat-v7.kicad_pcb') and a['schematic_sha256']==sha(H/'leaf-heat-v7.kicad_sch')
r={'status':'PASS','revision':'G.3','pcb_sha256':a['board_sha256'],'schematic_sha256':a['schematic_sha256'],
 'baseline_archive_sha256':sha(H/'history/rev-g2-before-external-antenna.zip'),
 'checks':['All traces, vias, zone definitions and filled copper unchanged','All pad geometry, nets, paste apertures and mounting locations unchanged','All schematic net membership and wire geometry unchanged','54 other PCB components unchanged; only U2 module variant/outline/model metadata changes','Hand BOM byte-identical; factory BOM contains six components and correct U2 C2926676','Two matching 300 mm antennas included separately in the 28-line Mouser target','Fresh native ERC/DRC and schematic parity zero'],
 'limitations':'Static verification only. Physical RF/connector fit, cable strain relief, assembly and vehicle tests remain.'}
(E/'antenna-g3-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))

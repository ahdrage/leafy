"""Package the checked Leafy G.5 release, with exact-input SHA-256 manifests."""
from pathlib import Path
import hashlib,json,zipfile,datetime,shutil,csv
H=Path(__file__).resolve().parent;E=H/'exports';D=H/'deliverables';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((E/'independent-audit.json').read_text());m=json.loads((E/'manufacturing-audit.json').read_text());g=json.loads((E/'filled-g5-audit.json').read_text())
assert a['board_sha256']==m['board_sha256']==g['pcb_sha256']==sha(H/'leaf-heat-v7.kicad_pcb')
assert a['schematic_sha256']==g['schematic_sha256']==sha(H/'leaf-heat-v7.kicad_sch')
assert g['status']=='PASS' and m['revision']==g['revision']=='G.5'
assert len(list(csv.DictReader((E/'BOM-FACTORY-JLCPCB.csv').open())))==6
# Archive superseded packages; the immutable full G.4 baseline also retains them.
archive=H/'history/g4-deliverables';archive.mkdir(exist_ok=True)
for p in D.glob('leaf-heat-rev-g4-*.zip'):
 dest=archive/p.name
 if dest.exists():assert sha(dest)==sha(p)
 else:shutil.copy2(p,dest)
 p.unlink()
for name in ['README.md','manifest.json']:
 if (D/name).exists() and not (archive/name).exists():shutil.copy2(D/name,archive/name)
(D/'README.md').write_text((H/'deliverables-README.tmp').read_text())
handoff={'product':'Leafy','revision':'G.5','status':'Verified files ready for new JLC Standard order; not uploaded or purchased',
 'pcb_sha256':a['board_sha256'],'schematic_sha256':a['schematic_sha256'],
 'JLCPCB':{'PCB_quantity':5,'assembled_quantity':2,'assembly_type':'Standard','side':'Top','factory_refs':['U1','U2','U4','U5','U6','L1'],
 'via_covering':'Epoxy Filled & Capped','via_plating':'Horizontal Electroless Copper Plating',
 'required_thermal_holes':{'U1':{'count':6,'drill_mm':.33},'U2':{'count':12,'drill_mm':.30}},
 'special_stencil':'No; JLC normal component-library engineering; supplied paste is reference only',
 'finished_board_mm':[100,100],'layers':4,'thickness_mm':1.6,'outer_copper_oz':1,'inner_copper_oz':1,'surface_finish':'Lead-free HASL','mask':'Green','silk':'White',
 'rails_fiducials':'Added by JLCPCB externally; remove before delivery', 'new_quote_total_USD':None,'prior_estimated_fill_plating_surcharge_USD':'21.06',
 'previous_order':'PRIVATE-RECORD-REMOVED','previous_cancellation_refund_status':'Not verified','new_order_created':False,'new_order_paid':False,
 'new_live_placement_verification':'Pending new upload; CPL identical to previously verified G.4',
 'upload_files':['deliverables/leafy-rev-g5-gerbers.zip','exports/BOM-FACTORY-JLCPCB.csv','exports/CPL-FACTORY-JLCPCB.csv']},
 'Mouser':{'user_reports_parts_received':True,'changes_required':False,'compatibility':'All 55 board MPNs and accessories unchanged; required quantities checked against saved 2026-09-16 supplier basket','physical_delivery_inspected':False},
 'validation':{'ERC':0,'DRC':0,'unconnected':0,'schematic_parity':0,'comparison_audit':'exports/filled-g5-audit.json'},
 'remaining':'Place new Standard quote/order with explicit 0.33 mm fill remark, verify price/parts/placement/processed artwork, supplier fabrication and physical prototype tests.'}
(H/'ORDER-HANDOFF-G5.json').write_text(json.dumps(handoff,indent=2)+'\n')
def make(name,files,base):
 files=sorted(set(files));assert all(p.is_file() for p in files),[str(p) for p in files if not p.is_file()]
 manifest={'product':'Leafy','revision':'G.5','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pcb_sha256':a['board_sha256'],'schematic_sha256':a['schematic_sha256'],'files':{str(p.relative_to(base)):sha(p) for p in files}}
 if (D/name).exists():
  with zipfile.ZipFile(D/name) as z:
   prior=json.loads(z.read('PACKAGE-MANIFEST.json'))
   if all(prior.get(k)==manifest[k] for k in ['product','revision','pcb_sha256','schematic_sha256','files']):
    assert z.testzip() is None
    for n,d in prior['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==d
    return
 with zipfile.ZipFile(D/name,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(base))
  z.writestr('PACKAGE-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
 with zipfile.ZipFile(D/name) as z:
  assert z.testzip() is None
  for n,d in manifest['files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==d
fab=list((E/'fabrication').iterdir())
make('leafy-rev-g5-gerbers.zip',fab,E/'fabrication')
factory=fab+[H/n for n in ['MANUFACTURING-NOTES.md','FILLED-G5-CHANGE.md','ORDER-G5.md','ORDER-HANDOFF-G5.json','JLCPCB-PLACEMENT-CHECK.md']]+[E/n for n in ['BOM-FACTORY-JLCPCB.csv','CPL-FACTORY-JLCPCB.csv','FACTORY-PIN1-REFERENCE.csv','assembly-map.png','factory-paste.png','thermal-fill-map.png','THERMAL-FILL-LOCATIONS.csv','schematic.pdf','filled-g5-audit.json','manufacturing-audit.json']]
make('leafy-rev-g5-factory-assembly.zip',factory,H)
hand=[H/n for n in ['HAND-ASSEMBLY.md','VEHICLE-WIRING.md','MOUSER-SHOPPING.md','DESIGN-REVIEW.md','FILLED-G5-CHANGE.md']]+[E/n for n in ['BOM-HAND.csv','BOM-ACCESSORIES.csv','MOUSER-TWO-BOARDS.csv','MOUSER-CART-WITH-SUPPLIES.csv','assembly-map.png','back-legend.png','schematic.pdf']]+[H/'quotations/2026-09-16'/n for n in ['cart-verification.json','mouser-basket-2026-09-16.xls']]
make('leafy-rev-g5-hand-assembly.zip',hand,H)
native=[H/n for n in ['leaf-heat-v7.kicad_pcb','leaf-heat-v7.kicad_sch','leaf-heat-v7.kicad_pro','leaf-heat-v7.kicad_dru','Leaf.kicad_sym','sym-lib-table','fp-lib-table','parts.json','accessories.json','testpoints.json','README.md','MANUFACTURING-NOTES.md','FABRICATION-NOTES.txt','FILLED-G5-CHANGE.md','ORDER-G5.md','ORDER-HANDOFF-G5.json','BUILD-REPRODUCTION.md','HAND-ASSEMBLY.md','VEHICLE-WIRING.md','DESIGN-REVIEW.md']]+list((H/'Leaf.pretty').glob('*.kicad_mod'))+[E/n for n in ['independent-audit.json','manufacturing-audit.json','filled-g5-audit.json','protection-calculations.json','erc.json','drc-final.json','BOM-FULL-REFERENCE-ONLY.csv','THERMAL-FILL-LOCATIONS.csv']]
make('leafy-rev-g5-kicad.zip',native,H)
images=[E/n for n in ['top.png','ground.png','power.png','bottom.png','placement.png','factory-paste.png','assembly-map.png','back-legend.png','schematic.png','schematic.pdf','thermal-fill-map.png','leafy-g5-3d.png']]
make('leafy-rev-g5-review-images.zip',images,E)
packages={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.glob('leafy-rev-g5-*.zip'))}
assert len(packages)==5
(D/'manifest.json').write_text(json.dumps({'product':'Leafy','revision':'G.5','pcb_sha256':a['board_sha256'],'schematic_sha256':a['schematic_sha256'],'packages':packages},indent=2)+'\n')
# A minimal flat upload folder avoids choosing an obsolete BOM or CPL.
U=D/'JLCPCB-UPLOAD-G5';U.mkdir(exist_ok=True)
for source in [D/'leafy-rev-g5-gerbers.zip',E/'BOM-FACTORY-JLCPCB.csv',E/'CPL-FACTORY-JLCPCB.csv',H/'ORDER-G5.md',H/'FABRICATION-NOTES.txt',E/'THERMAL-FILL-LOCATIONS.csv',E/'thermal-fill-map.png']:
 shutil.copy2(source,U/source.name)
(U/'README.txt').write_text('Leafy G.5: upload the Gerber ZIP, then the factory BOM CSV and JLC CPL CSV.\nStandard PCBA / 5 PCBs / 2 assembled / top only. See ORDER-G5.md for settings\nand remarks. Epoxy Filled & Capped + Horizontal Electroless Copper Plating.\nSpecial stencil = No. Explicitly include 6 x 0.33 mm U1 + 12 x 0.30 mm U2 holes.\nThe extra CSV/PNG/text files are engineering references, not BOM/CPL uploads.\n')
(U/'UPLOAD-MANIFEST.json').write_text(json.dumps({p.name:sha(p) for p in sorted(U.iterdir()) if p.name!='UPLOAD-MANIFEST.json'},indent=2)+'\n')
print('Verified five matched G.5 packages and the flat JLC upload folder.')

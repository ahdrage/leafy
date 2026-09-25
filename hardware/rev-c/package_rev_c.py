"""Package only the verified final CAD and exports; omit iteration snapshots."""
from pathlib import Path
import json, csv, hashlib, shutil, zipfile
H=Path(__file__).resolve().parent;E=H/'exports';D=H.parent.parent/'deliverables'
P=D/'leaf-heat-rev-c';P.mkdir(exist_ok=True)
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
drc=json.loads((E/'drc-final.json').read_text());erc=json.loads((E/'erc.json').read_text())
assert not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity']
assert all(not sheet['violations'] for sheet in erc['sheets'])
audit=json.loads((E/'independent-audit.json').read_text())
assert audit['component_count']==41 and audit['unique_mpns']==25 and not audit['unexplained_ground_gaps']
m=json.loads((E/'manufacturing-audit.json').read_text())
assert m['board_sha256']==sha(H/'leaf-heat-v3.kicad_pcb')
for f,expected in m['fabrication_files'].items():assert sha(E/'fabrication'/f)==expected
assert len(list(csv.DictReader((E/'placements.csv').open())))==41
final_exports=['BOM.csv','BOM-PCBWay.csv','BOM-JLCPCB.csv','placements.csv','CPL-JLCPCB.csv','leaf-heat-v3-ipc2581.xml',
 'top.png','ground.png','power.png','bottom.png','placement.png','board-3d.png','schematic.png','programming-schematic.png',
 'top.svg','ground.svg','power.svg','bottom.svg','placement.svg','erc.json','drc-final.json','drc-expanded.json','independent-audit.json','manufacturing-audit.json','baseline-sha256.json','drill-report.txt','leaf-heat-v3.net.xml']
native=['leaf-heat-v3.kicad_pro','leaf-heat-v3.kicad_pcb','leaf-heat-v3.kicad_sch','leaf-heat-v3.kicad_dru','Leaf.kicad_sym','fp-lib-table','sym-lib-table','parts.json','README.md','DESIGN-REVIEW.md','MANUFACTURING-NOTES.md','PROGRAMMING.md']
for name in native:shutil.copy2(H/name,P/name)
shutil.copytree(H/'Leaf.pretty',P/'Leaf.pretty',dirs_exist_ok=True)
(P/'exports').mkdir(exist_ok=True)
for name in final_exports:shutil.copy2(E/name,P/'exports'/name)
shutil.copytree(E/'fabrication',P/'exports/fabrication',dirs_exist_ok=True)
shutil.copytree(E/'schematic',P/'exports/schematic',dirs_exist_ok=True)
manifest={str(f.relative_to(P)):sha(f) for f in sorted(P.rglob('*')) if f.is_file() and f.name!='SHA256SUMS.json'}
(P/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2)+'\n')
def zipfiles(dest,files):
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for source,arc in files:z.write(source,arc)
    with zipfile.ZipFile(dest) as z:assert z.testzip() is None
gerber=D/'leaf-heat-rev-c-gerbers.zip'
zipfiles(gerber,[(f,f.name) for f in sorted((E/'fabrication').iterdir()) if f.is_file()])
assembly=D/'leaf-heat-rev-c-assembly.zip'
assembly_names=['BOM-PCBWay.csv','BOM-JLCPCB.csv','placements.csv','CPL-JLCPCB.csv','placement.png','schematic.png','board-3d.png','leaf-heat-v3-ipc2581.xml']
zipfiles(assembly,[(E/n,n) for n in assembly_names]+[(H/'MANUFACTURING-NOTES.md','MANUFACTURING-NOTES.md'),(gerber,gerber.name)])
project=D/'leaf-heat-rev-c-kicad-review.zip'
zipfiles(project,[(f,str(Path('leaf-heat-rev-c')/f.relative_to(P))) for f in sorted(P.rglob('*')) if f.is_file()])
images=D/'leaf-heat-rev-c-review-images.zip'
zipfiles(images,[(E/n,n) for n in final_exports if n.endswith('.png')]+[(H/'DESIGN-REVIEW.md','DESIGN-REVIEW.md')])
summary={'revision':'C','prototype_status':'CAD checked, not physically tested; quotation/review files only',
 'board_sha256':sha(H/'leaf-heat-v3.kicad_pcb'),'schematic_sha256':sha(H/'leaf-heat-v3.kicad_sch'),
 'parts':41,'mpns':25,'assembly':'39 SMT + 2 THT, all top','controlled_impedance_required':False,
 'packages':{f.name:{'sha256':sha(f),'bytes':f.stat().st_size} for f in [gerber,assembly,project,images]}}
(D/'leaf-heat-rev-c-package-manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))

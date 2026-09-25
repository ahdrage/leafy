"""Package explicit, audited outputs without router intermediates or stale revisions."""
from pathlib import Path
import csv,hashlib,io,json,zipfile

H=Path(__file__).resolve().parent
E=H/'exports';D=H/'deliverables';D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=H/'leaf-heat-v5.kicad_pcb'
audit=json.loads((E/'independent-audit.json').read_text())
manufacturing=json.loads((E/'manufacturing-audit.json').read_text())
assert sha(native)==audit['board_sha256']==manufacturing['board_sha256']
assert sha(H/'leaf-heat-v5.kicad_sch')==audit['schematic_sha256']
assert all(sha(E/'fabrication'/name)==value for name,value in manufacturing['fabrication_files'].items())
assert audit['factory_refs']==['L1','U1','U2','U4'] and audit['hand_count']==37

records={}
def package(name,files):
    contents={str(arc):Path(src) for src,arc in files}
    assert len(contents)==len(files),name
    path=D/name
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for arc,src in sorted(contents.items()):
            assert src.is_file(),src
            z.write(src,arc)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(contents)
        assert all(hashlib.sha256(z.read(arc)).hexdigest()==sha(src) for arc,src in contents.items())
    records[name]={'sha256':sha(path),'bytes':path.stat().st_size,'file_count':len(contents),
                   'contents':{arc:sha(src) for arc,src in sorted(contents.items())}}
    return path

fab=[(E/'fabrication'/n,n) for n in sorted(manufacturing['fabrication_files'])]
assert len([n for _,n in fab if n.endswith('.drl')])==2
gerber=package('leaf-heat-rev-e-gerbers.zip',fab)
factory_names=['BOM-FACTORY-PCBWay.csv','BOM-FACTORY-JLCPCB.csv','placements-FACTORY.csv','CPL-FACTORY-JLCPCB.csv']
factory=[(E/n,n) for n in factory_names]
factory += [(H/'MANUFACTURING-NOTES.md','MANUFACTURING-NOTES.md'),(gerber,gerber.name),
            (E/'assembly-map.png','assembly-map.png'),(E/'placement.svg','placement.svg'),
            (E/'schematic.pdf','REFERENCE-ONLY-schematic.pdf'),(E/'drill-report.txt','drill-report.txt')]
factory_zip=package('leaf-heat-rev-e-factory-assembly.zip',factory)
with zipfile.ZipFile(factory_zip) as z:
    assert not any('BOM-HAND' in n or 'FULL-REFERENCE' in n for n in z.namelist())
    for n,key in [(factory_names[0],'Designator'),(factory_names[1],'Designator'),(factory_names[2],'Ref'),(factory_names[3],'Designator')]:
        rows=list(csv.DictReader(io.StringIO(z.read(n).decode())))
        assert len(rows)==4 and {r[key] for r in rows}==set(audit['factory_refs'])

docs=['README.md','DESIGN-REVIEW.md','HAND-ASSEMBLY.md','MANUFACTURING-NOTES.md','PROGRAMMING.md','REVIEW-IMAGES.md','RECHECK-2026-09-12.md','VEHICLE-WIRING.md']
images=['board-3d.png','assembly-map.png','assembly-map.svg','placement.png','placement.svg',
        'back-legend.png','back-legend.svg','top.png','top.svg','ground.png','ground.svg','power.png','power.svg','bottom.png','bottom.svg',
        'factory-paste.png','factory-paste.svg','schematic.png']
review_exports=images+factory_names+['BOM-HAND.csv','BOM-FULL-REFERENCE-ONLY.csv',
        'placements-FULL-REFERENCE-ONLY.csv','schematic.pdf','erc.json','drc-final.json',
        'independent-audit.json','manufacturing-audit.json','leaf-heat-v5.net.xml','drill-report.txt']
source=[(H/n,'leaf-heat-rev-e/'+n) for n in docs+['leaf-heat-v5.kicad_pro','leaf-heat-v5.kicad_sch',
        'leaf-heat-v5.kicad_pcb','leaf-heat-v5.kicad_dru','Leaf.kicad_sym','sym-lib-table','fp-lib-table',
        'parts.json','testpoints.json']]
source += [(p,'leaf-heat-rev-e/Leaf.pretty/'+p.name) for p in sorted((H/'Leaf.pretty').glob('*.kicad_mod'))]
source += [(E/n,'leaf-heat-rev-e/exports/'+n) for n in review_exports]
source += [(E/'schematic/leaf-heat-v5.svg','leaf-heat-rev-e/exports/schematic/leaf-heat-v5.svg')]
source += [(p,'leaf-heat-rev-e/exports/fabrication/'+n) for p,n in fab]
recheck_names=['drc-fresh.json','erc-fresh.json','netlist-fresh.xml','connections-and-packages.json','check_connections.py','d1-change-verification.json']
source += [(H/'review-2026-09-12'/n,'leaf-heat-rev-e/review-2026-09-12/'+n) for n in recheck_names]
package('leaf-heat-rev-e-kicad-review.zip',source)
hand=[(H/n,n) for n in ['HAND-ASSEMBLY.md','PROGRAMMING.md','DESIGN-REVIEW.md','REVIEW-IMAGES.md','RECHECK-2026-09-12.md','VEHICLE-WIRING.md']]
hand += [(E/n,n) for n in ['BOM-HAND.csv','BOM-FULL-REFERENCE-ONLY.csv','assembly-map.png','assembly-map.svg',
                         'placement.png','placement.svg','top.png','board-3d.png','schematic.pdf']]
hand += [(H/'review-2026-09-12'/n,'review-2026-09-12/'+n) for n in recheck_names]
package('leaf-heat-rev-e-hand-assembly.zip',hand)
review=[(E/n,n) for n in images]+[(H/n,n) for n in ['REVIEW-IMAGES.md','DESIGN-REVIEW.md','RECHECK-2026-09-12.md','VEHICLE-WIRING.md','HAND-ASSEMBLY.md','PROGRAMMING.md']]
review += [(H/'review-2026-09-12'/n,'review-2026-09-12/'+n) for n in recheck_names]
review += [(E/'schematic/leaf-heat-v5.svg','schematic.svg')]
package('leaf-heat-rev-e-review-images.zip',review)
adi=[(p,'naerbilder/'+p.name) for p in sorted((E/'screenshots').iterdir()) if p.suffix in {'.png','.svg','.txt'}]
adi += [(E/n,'oversikter/'+n) for n in ['top.png','ground.png','power.png','bottom.png','back-legend.png','assembly-map.png','board-3d.png','schematic.png']]
package('leaf-heat-rev-e-screenshots-for-adi.zip',adi)
(D/'manifest.json').write_text(json.dumps({'revision':'E','date':'2026-09-12','board_sha256':sha(native),
    'schematic_sha256':sha(H/'leaf-heat-v5.kicad_sch'),'packages':records},indent=2)+'\n')
print(json.dumps({name:{k:v for k,v in value.items() if k!='contents'} for name,value in records.items()},indent=2))

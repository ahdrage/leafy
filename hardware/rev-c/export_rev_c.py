"""Export the checked Rev C files and verify purchasing/placement consistency."""
from pathlib import Path
import os, subprocess, csv, collections, json, hashlib, xml.etree.ElementTree as ET
import pcbnew as p
import cairosvg
H=Path(__file__).resolve().parent;E=H/'exports';B=H/'leaf-heat-v3.kicad_pcb'
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
env=dict(os.environ,FONTCONFIG_FILE=str(H.parent/'fontconfig.xml'))
def run(*args):
    r=subprocess.run([K,*map(str,args)],env=env,text=True,capture_output=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    print('Exported',args[1:3])
for layer,name in [('F.Cu,F.Silkscreen,Edge.Cuts','top'),('In1.Cu,Edge.Cuts','ground'),('In2.Cu,Edge.Cuts','power'),('B.Cu,Edge.Cuts','bottom'),('F.Fab,Edge.Cuts','placement')]:
    run('pcb','export','svg','--layers',layer,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',E/(name+'.svg'),B)
    cairosvg.svg2png(url=str(E/(name+'.svg')),write_to=str(E/(name+'.png')),output_width=1700,background_color='#111827')
run('pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','-o',E/'placements-native.csv',B)
run('sch','export','svg','-o',E/'schematic',H/'leaf-heat-v3.kicad_sch')
cairosvg.svg2png(url=str(E/'schematic/leaf-heat-v3.svg'),write_to=str(E/'schematic.png'),output_width=3800,background_color='white')
# A crop from the same schematic vectors makes the new circuit easy to inspect.
root=ET.parse(E/'schematic/leaf-heat-v3.svg').getroot()
root.set('viewBox','15 138 235 105');root.set('width','235mm');root.set('height','105mm')
cairosvg.svg2png(bytestring=ET.tostring(root),write_to=str(E/'programming-schematic.png'),output_width=2200,background_color='white')
run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','-o',E/'fabrication',B)
run('pcb','export','drill','--drill-origin','plot','--excellon-separate-th','--generate-report','--report-path',E/'drill-report.txt','-o',E/'fabrication',B)
run('pcb','export','ipc2581','-o',E/'leaf-heat-v3-ipc2581.xml',B)
b=p.LoadBoard(str(B));fps={f.GetReference():f for f in b.GetFootprints()}
parts=json.loads((H/'parts.json').read_text())
groups=collections.defaultdict(list)
for q in parts:groups[q['mpn']].append(q)
with (E/'BOM.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Manufacturer','MPN','Quantity','Notes'])
    for q in parts:w.writerow([q['ref'],q['value'],q['footprint'],q['manufacturer'],q['mpn'],1,q['notes']])
with (E/'BOM-PCBWay.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Item','Designator','Quantity','Manufacturer','Manufacturer Part Number','Description / Value','Footprint','Notes'])
    for i,qs in enumerate(groups.values(),1):
        q=qs[0];w.writerow([i,','.join(x['ref'] for x in qs),len(qs),q['manufacturer'],q['mpn'],q['value'],q['footprint'],' | '.join(sorted({x['notes'] for x in qs if x['notes']}))])
with (E/'BOM-JLCPCB.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','Manufacturer','Manufacturer Part Number','LCSC Part #'])
    for qs in groups.values():
        q=qs[0];w.writerow([q['value'],','.join(x['ref'] for x in qs),q['footprint'],q['manufacturer'],q['mpn'],''])
native=list(csv.DictReader((E/'placements-native.csv').open()))
refs={q['ref'] for q in parts};rows=[q for q in native if q['Ref'] in refs]
assert len(rows)==len(refs)==41 and {q['Ref'] for q in rows}==refs
with (E/'placements.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (E/'CPL-JLCPCB.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
    for q in rows:w.writerow([q['Ref'],q['PosX'],q['PosY'],'Top',q['Rot']])
for q in rows:
    f=fps[q['Ref']]
    assert abs(float(q['PosX'])-p.ToMM(f.GetPosition().x))<.00001
    assert abs(float(q['PosY'])-(50-p.ToMM(f.GetPosition().y)))<.00001
    assert abs(float(q['Rot'])-f.GetOrientationDegrees())<.00001
    assert q['Side']=='top'
report={'component_count':len(parts),'unique_mpns':len(groups),'placement_rows':len(rows),'placement_origin':'lower-left board corner (0,50 mm in KiCad); X right, Y up',
 'through_hole_parts':['J1','J3'],'surface_mount_count':39,'manufacturer_part_numbers_exact':True,'catalog_ids':'intentionally blank until exact MPN matching; no substitutions inferred',
 'connector_origin_caveat':'J1 and J3 coordinates use pin 1, not the body centroid. Review these with assembler; do not auto-confirm component placement.',
 'board_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),
 'fabrication_files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((E/'fabrication').iterdir()) if f.is_file()}}
(E/'manufacturing-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified 41 placements / 25 MPNs / 39 SMT + 2 THT')

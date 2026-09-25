"""Export final Rev F. Factory CSVs and paste contain exactly four parts."""
from pathlib import Path
import os,subprocess,csv,collections,json,hashlib,xml.etree.ElementTree as ET,html
import pcbnew as p
import cairosvg
H=Path(__file__).resolve().parent;E=H/'exports';B=H/'leaf-heat-v6.kicad_pcb'
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
env=dict(os.environ,FONTCONFIG_FILE=str(H.parent/'fontconfig.xml'))
def run(*args):
    r=subprocess.run([K,*map(str,args)],env=env,text=True,capture_output=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    print('Exported',args[1:3])
for layer,name in [('F.Cu,F.Silkscreen,Edge.Cuts','top'),('In1.Cu,Edge.Cuts','ground'),('In2.Cu,Edge.Cuts','power'),('B.Cu,Edge.Cuts','bottom'),('F.Fab,Edge.Cuts','placement'),('F.Paste,Edge.Cuts','factory-paste'),('B.Silkscreen,Edge.Cuts','back-legend')]:
    extra=['--mirror','--black-and-white'] if name=='back-legend' else []
    run('pcb','export','svg',*extra,'--layers',layer,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',E/(name+'.svg'),B)
    cairosvg.svg2png(url=str(E/(name+'.svg')),write_to=str(E/(name+'.png')),output_width=2000,background_color='#f8fafc')
run('pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','-o',E/'placements-native.csv',B)
run('sch','export','svg','-o',E/'schematic',H/'leaf-heat-v6.kicad_sch')
cairosvg.svg2png(url=str(E/'schematic/leaf-heat-v6.svg'),write_to=str(E/'schematic.png'),output_width=4000,background_color='white')
run('sch','export','pdf','-o',E/'schematic.pdf',H/'leaf-heat-v6.kicad_sch')
run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','-o',E/'fabrication',B)
run('pcb','export','drill','--drill-origin','plot','--excellon-separate-th','--generate-report','--report-path',E/'drill-report.txt','-o',E/'fabrication',B)
parts=json.loads((H/'parts.json').read_text());factory=[q for q in parts if q['assembly']=='FACTORY'];hand=[q for q in parts if q['assembly']=='HAND']
assert {q['ref'] for q in factory}=={'U1','U2','U4','L1'} and len(hand)==37
b=p.LoadBoard(str(B));fps={f.GetReference():f for f in b.GetFootprints()}
def groups(ps):
    d=collections.defaultdict(list)
    for q in ps:d[q['mpn']].append(q)
    return list(d.values())
with (E/'BOM-FULL-REFERENCE-ONLY.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Manufacturer','MPN','Assembly','Notes'])
    for q in parts:w.writerow([q[k] for k in ['ref','value','footprint','manufacturer','mpn','assembly','notes']])
with (E/'BOM-HAND.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['References','Value','Manufacturer','MPN','Qty for ONE board','Qty for TWO boards','Footprint','Datasheet','Notes'])
    for qs in groups(hand):
        q=qs[0];w.writerow([','.join(x['ref'] for x in qs),q['value'],q['manufacturer'],q['mpn'],len(qs),2*len(qs),q['footprint'],q['datasheet'],' | '.join(sorted({x['notes'] for x in qs if x['notes']}))])
with (E/'BOM-FACTORY-PCBWay.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Item','Designator','Quantity','Manufacturer','Manufacturer Part Number','Description / Value','Footprint','Notes'])
    for i,q in enumerate(factory,1):w.writerow([i,q['ref'],1,q['manufacturer'],q['mpn'],q['value'],q['footprint'],'FACTORY FIT. Only U1 U2 U4 L1 are factory-assembled; all other parts customer-fitted.'])
with (E/'BOM-FACTORY-JLCPCB.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','Manufacturer','Manufacturer Part Number','LCSC Part #'])
    for q in factory:w.writerow([q['value'],q['ref'],q['footprint'],q['manufacturer'],q['mpn'],''])
native=list(csv.DictReader((E/'placements-native.csv').open()));refs={q['ref'] for q in parts};rows=[q for q in native if q['Ref'] in refs]
assert len(rows)==len(refs)==41 and {q['Ref'] for q in rows}==refs
fr=[q for q in rows if q['Ref'] in {x['ref'] for x in factory}];assert len(fr)==4
for name,rr in [('placements-FULL-REFERENCE-ONLY.csv',rows),('placements-FACTORY.csv',fr)]:
    with (E/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
with (E/'CPL-FACTORY-JLCPCB.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
    for q in fr:w.writerow([q['Ref'],q['PosX'],q['PosY'],'Top',q['Rot']])
for q in rows:
    f=fps[q['Ref']]
    assert abs(float(q['PosX'])-p.ToMM(f.GetPosition().x))<.00001
    assert abs(float(q['PosY'])-(100-p.ToMM(f.GetPosition().y)))<.00001
    assert abs(float(q['Rot'])-f.GetOrientationDegrees())<.00001 and q['Side']=='top'
paste={f.GetReference() for f in b.GetFootprints() if any(p.F_Paste in pad.GetLayerSet().Seq() for pad in f.Pads())}
assert paste=={'U1','U2','U4','L1'},paste
# A native drawing with overlays clarifies assembly ownership. Raster exports
# remain separate, so nothing relies on colour to define the supplier's scope.
source=ET.parse(E/'placement.svg').getroot();vb=[float(x) for x in source.get('viewBox').split()]
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="2010" viewBox="-5 -18 110 123">',
     '<rect x="-5" y="-18" width="110" height="123" fill="#f8fafc"/>',
     '<text x="0" y="-11" font-family="Arial" font-size="2.9" fill="#0f172a">LEAF HEAT REV F — 100 × 100 mm</text>',
     '<text x="0" y="-5" font-family="Arial" font-size="1.8" fill="#9a3412">Orange: factory fits U1 / U2 / U4 / L1. Remaining 37 parts: hand solder.</text>',
     '<rect x="0" y="0" width="100" height="100" rx="0" fill="#e2e8f0" stroke="#475569" stroke-width=".25"/>']
for f in b.GetFootprints():
    ref=f.GetReference();factory_part=ref in paste
    for pad in f.Pads():
        layers=list(pad.GetLayerSet().Seq())
        if p.F_Cu not in layers and pad.GetAttribute()!=p.PAD_ATTRIB_NPTH:continue
        x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y);w,h=p.ToMM(pad.GetSize().x),p.ToMM(pad.GetSize().y)
        fill='#f59e0b' if factory_part else '#94a3b8'
        angle=-pad.GetOrientationDegrees()
        svg.append(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx=".1" fill="{fill}" stroke="#475569" stroke-width=".08" transform="rotate({angle} {x} {y})"/>')
        if pad.GetAttribute() in {p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH}:
            svg.append(f'<circle cx="{x}" cy="{y}" r="{p.ToMM(pad.GetDrillSize().x)/2}" fill="#f8fafc"/>')
    if ref in refs or ref.startswith('TP'):
        x,y=p.ToMM(f.Reference().GetPosition().x),p.ToMM(f.Reference().GetPosition().y)
        if ref=='U4':x,y=83,87
        svg.append(f'<text x="{x}" y="{y+.4}" text-anchor="middle" font-family="Arial" font-size="1.7" font-weight="bold" fill="{"#9a3412" if factory_part else "#0f172a"}">{html.escape(ref)}</text>')
        if factory_part:
            x,y=p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)
            svg.append(f'<circle cx="{x}" cy="{y}" r="{11 if ref=="U2" else 5}" fill="none" stroke="#ea580c" stroke-width=".4"/>')
for i,(text,x,y) in enumerate([('POWER',4,35),('Wi-Fi',65,25),('CAR / CAN',4,57),('RESET / BOOT',57,74),('UART',84,94)]):
    svg.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="2.5" fill="#334155">{text}</text>')
svg.append('</svg>');(E/'assembly-map.svg').write_text('\n'.join(svg));cairosvg.svg2png(url=str(E/'assembly-map.svg'),write_to=str(E/'assembly-map.png'),output_width=2000)
report={'component_count':41,'factory_count':4,'hand_count':37,'factory_refs':sorted(paste),'hand_mpns':len(groups(hand)),'unique_mpns':len(groups(parts)),
 'placement_origin':'lower-left (0,100 mm in KiCad), X right / Y up','factory_placement_rows':4,'full_placement_rows':41,
 'stencil_refs':sorted(paste),'bare_test_holes':7,'mounting_holes':4,'board_sha256':hashlib.sha256(B.read_bytes()).hexdigest(),
 'catalog_ids':'blank until exact manufacturer matching','fabrication_files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((E/'fabrication').iterdir()) if f.is_file()}}
(E/'manufacturing-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified 4 factory placements, 37 hand parts, and factory-only paste.')

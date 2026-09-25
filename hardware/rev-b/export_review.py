from pathlib import Path
import subprocess,os,csv,json,collections
import pcbnew as p,cairosvg
H=Path(__file__).resolve().parent;E=H/'exports';B=H/'leaf-heat-v2.kicad_pcb';K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
env=dict(os.environ,FONTCONFIG_FILE=str(H.parent/'fontconfig.xml'))
def run(*args):
 r=subprocess.run([K,*map(str,args)],env=env,text=True,capture_output=True)
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 print('Exported',args[1:3])
for layer,name in [('F.Cu,F.Silkscreen,Edge.Cuts','top'),('In1.Cu,Edge.Cuts','ground'),('In2.Cu,Edge.Cuts','power'),('B.Cu,Edge.Cuts','bottom'),('F.Fab,Edge.Cuts','placement')]:
 run('pcb','export','svg','--layers',layer,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',E/(name+'.svg'),B)
 cairosvg.svg2png(url=str(E/(name+'.svg')),write_to=str(E/(name+'.png')),output_width=1500,background_color='#111827')
run('pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--exclude-dnp','-o',E/'placements.csv',B)
run('sch','export','svg','-o',E/'schematic',H/'leaf-heat-v2.kicad_sch')
run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','--subtract-soldermask','-o',E/'fabrication-review',B)
run('pcb','export','drill','--drill-origin','plot','--excellon-separate-th','--generate-report','--report-path',E/'drill-report.txt','-o',E/'fabrication-review',B)
# BOM unchanged electrically, but refresh all locations/net names from the saved PCB.
b=p.LoadBoard(str(B));fps={f.GetReference():f for f in b.GetFootprints()}
parts=json.loads((H.parent/'parts.json').read_text())
for q in parts:
 f=fps[q['ref']];q['xy']=[p.ToMM(f.GetPosition().x),p.ToMM(f.GetPosition().y)];q['angle']=f.GetOrientationDegrees();q['rotation']=f.GetOrientationDegrees()
 for n in list(q['nets']):
  pads=[v for v in f.Pads() if v.GetNumber()==n]
  if pads and not pads[0].GetNetname().startswith('unconnected-'):q['nets'][n]=pads[0].GetNetname().lstrip('/')
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
with (E/'BOM.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Manufacturer','MPN','Quantity','Notes'])
 for q in parts:w.writerow([q['ref'],q['value'],q['footprint'],q['manufacturer'],q['mpn'],1,q['notes']])
groups=collections.defaultdict(list)
for q in parts:groups[q['mpn']].append(q)
with (E/'BOM-PCBWay.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Item','Designator','Quantity','Manufacturer','Manufacturer Part Number','Description / Value','Footprint','Notes'])
 for i,qs in enumerate(groups.values(),1):
  q=qs[0];w.writerow([i,','.join(v['ref'] for v in qs),len(qs),q['manufacturer'],q['mpn'],q['value'],q['footprint'],q['notes']])
print('Parts',len(parts),'unique MPNs',len(groups))

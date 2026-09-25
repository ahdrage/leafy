"""Apply final precision-divider and delay-capacitor selection, without rerouting."""
from pathlib import Path
import json,sexpdata as sx,pcbnew as p
from collections import defaultdict
H=Path(__file__).resolve().parent
def children(q,k):return [x for x in q if isinstance(x,list) and x and str(x[0])==k]
changes={
 'C15':dict(mpn='EEU-FR1J470H',notes='47 uF, 63 V FR series; taped straight leads, 6.3 mm diameter x 11.2 mm height, 2.5 mm pitch. Packaging substitute for backordered EEU-FR1J470; trim leads after soldering.'),
 'R22':dict(value='680k / 0.1%',mpn='RT1206BRD07680KL',notes='Precision 0.1%, 25 ppm/C cutoff divider. Do not substitute the 1% general-purpose part.'),
 'R23':dict(value='47k / 0.1%',mpn='RT1206BRD0747KL',notes='Precision 0.1%, 25 ppm/C cutoff divider. R8 remains a separate 1% ADC resistor.'),
 'C18':dict(value='10uF / 16V',mpn='C1206C106K4RACTU',notes='CTS: nominal 1.27 s sense delay before DC-bias/tolerance effects. Within TI recommended maximum 10 uF.'),
 'C19':dict(value='10uF / 16V',mpn='C1206C106K4RACTU',notes='CTR: nominal 12.7 s recovery delay before DC-bias/tolerance effects. Within TI recommended maximum 10 uF.')}
parts=json.loads((H/'parts.json').read_text())
for q in parts:
 if q['ref'] in changes:
  q.update(changes[q['ref']]);q['datasheet']=('https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1J470' if q['ref']=='C15' else ('https://search.kemet.com/component-documentation/download/specsheet/' if q['ref'].startswith('C') else 'https://www.yageogroup.com/component-documentation/download/specsheet/')+q['mpn'])
meta={q['ref']:q for q in parts};sch=sx.load(open(H/'leaf-heat-v7.kicad_sch'))
for inst in children(sch,'symbol'):
 props={q[1]:q for q in children(inst,'property')};ref=props['Reference'][2]
 if ref in changes:
  for field,key in [('Value','value'),('MPN','mpn'),('Datasheet','datasheet')]:props[field][2]=meta[ref][key]
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'))
for fp in b.GetFootprints():
 if fp.GetReference() in changes:
  q=meta[fp.GetReference()];fp.SetValue(q['value']);fp.SetField('MPN',q['mpn']);fp.SetField('Datasheet',q['datasheet'])
# Rebuild the hand-parts legend from the final values, including all new parts.
for t in list(b.GetDrawings()):
 if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.B_SilkS and p.ToMM(t.GetPosition().x) in (54.,93.) and 11<=p.ToMM(t.GetPosition().y)<=61.1:
  b.RemoveNative(t)
groups=defaultdict(list)
for q in parts:
 if q['assembly']=='HAND':groups[q['mpn']].append(q)
assert len(groups)==27
for i,qs in enumerate(groups.values()):
 q=qs[0];value=q['value']
 if q['ref']=='J1':value='DB9 male'
 if q['ref']=='SW1':value='RESET / BOOT buttons'
 if q['ref']=='J3':value='3-pin UART'
 for x,txt in [(93,' '.join(z['ref'] for z in qs)),(54,value)]:
  t=p.PCB_TEXT(b);t.SetLayer(p.B_SilkS);t.SetText(txt);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(12+i*1.85)))
  t.SetTextSize(p.VECTOR2I(p.FromMM(.85),p.FromMM(.85)));t.SetTextThickness(p.FromMM(.15));t.SetMirrored(True);t.SetHorizJustify(-1);b.Add(t)
p.SaveBoard(str(H/'leaf-heat-v7.kicad_pcb'),b)
(H/'leaf-heat-v7.kicad_sch').write_text(sx.dumps(sch));(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
print('Final divider and delay values applied. Regenerate netlist and reports.')

"""Supplier-independent pin-one coordinates for placement/DFM review."""
from pathlib import Path
import csv, json
import pcbnew as p
H=Path(__file__).resolve().parent;E=H/'exports'
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'))
refs={'U1','U2','U4','U5','U6','L1'}
rows=[]
for f in b.GetFootprints():
    if f.GetReference() not in refs:continue
    pad=next(x for x in f.Pads() if x.GetNumber()=='1')
    rows.append({'Designator':f.GetReference(),'MPN':f.GetField('MPN').GetText(),
                 'Centre X mm':p.ToMM(f.GetPosition().x),'Centre Y mm':100-p.ToMM(f.GetPosition().y),
                 'Pad 1 X mm':p.ToMM(pad.GetPosition().x),'Pad 1 Y mm':100-p.ToMM(pad.GetPosition().y),
                 'Note':'L1 is nonpolar; pads must align.' if f.GetReference()=='L1' else 'Top view. IC pin 1 must align to this pad.'})
rows.sort(key=lambda x:x['Designator'])
with (E/'FACTORY-PIN1-REFERENCE.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('Exported six independent centre/pad-1 coordinate references. Origin: PCB lower-left, X right, Y up.')

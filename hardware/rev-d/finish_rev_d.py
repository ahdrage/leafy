"""Add the fourth support hole and a readable on-board hand-parts legend."""
from pathlib import Path
import json,collections,uuid
import pcbnew as p
H=Path(__file__).resolve().parent;B=H/'leaf-heat-v4.kicad_pcb'
b=p.LoadBoard(str(B))
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def ident(tag):return str(uuid.uuid5(uuid.NAMESPACE_URL,'leaf-revd-legend/'+tag))
parts=json.loads((H/'parts.json').read_text());groups=collections.defaultdict(list)
for q in parts:
    if q['assembly']=='HAND':groups[q['mpn']].append(q)
tags=['title']+[str(i)+col for i in range(len(groups)) for col in ['r','v']]
ids={ident(tag) for tag in tags}
for d in list(b.GetDrawings()):
    if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_SilkS and 54<p.ToMM(d.GetPosition().x)<145 and 46<p.ToMM(d.GetPosition().y)<105:b.RemoveNative(d)
def label(tag,txt,at,size):
    d=p.PCB_TEXT(b);d.SetText(txt);d.SetPosition(v(at));d.SetTextSize(v((size,size)));d.SetTextThickness(p.FromMM(.15));d.SetLayer(p.F_SilkS);d.SetHorizJustify(p.GR_TEXT_H_ALIGN_LEFT);b.Add(d)
label('title','HAND-FITTED PARTS / CHECK VALUES BEFORE SOLDERING',(55,47),1.2)
short={'J1':'DB9 male','J3':'3-pin UART','U3':'TCAN3403DRQ1','D4':'PESD2CAN','D1':'SS110 / 100V','D6':'GREEN LED / K = cathode','SW1':'RESET / BOOT buttons'}
for i,qs in enumerate(groups.values()):
    label(str(i)+'r',' '.join(q['ref'] for q in qs),(55,51+i*2.5),1)
    label(str(i)+'v',short.get(qs[0]['ref'],qs[0]['value']),(94,51+i*2.5),1)
if not any(f.GetReference()=='H4' for f in b.GetFootprints()):
    f=p.FootprintLoad('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/MountingHole.pretty','MountingHole_2.7mm_M2.5')
    f.SetReference('H4');f.Reference().SetVisible(False);f.Value().SetVisible(False);b.Add(f)
f=next(f for f in b.GetFootprints() if f.GetReference()=='H4');f.SetPosition(v((146,44)));f.SetAttributes(p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
b.BuildConnectivity();p.SaveBoard(str(B),b)
print('Added four supports and',len(groups),'rows of hand-parts values on the board.')

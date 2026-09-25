"""One-time G.4 -> G.5 mask/process and Leafy silkscreen revision."""
from pathlib import Path
import hashlib, json, uuid
import sexpdata as sx
import pcbnew as p

H = Path(__file__).resolve().parent
S = sx.Symbol
def key(q): return str(q[0]) if isinstance(q,list) and q else ''
def items(q,k): return [v for v in q if key(v)==k]
def child(q,k): return next(v for v in q if key(v)==k)
def prop(q,k): return next(v for v in items(q,'property') if v[1]==k)

assert (H/'history/rev-g4-before-filled-g5.zip').exists()
assert hashlib.sha256((H/'leaf-heat-v7.kicad_pcb').read_bytes()).hexdigest() == '1b46a5b65acba3df29483509f488be3b8119a9854dad4f33adc2d537fc51ba4f', 'Only apply to the preserved G.4 board'
names = {
    'U1': ('LMR36510_DDA_TopTented_G4__Factory', 'LMR36510_DDA_FilledCapped_G5__Factory'),
    'U2': ('ESP32-C3-WROOM-02U_TopTented_G4__Factory', 'ESP32-C3-WROOM-02U_FilledCapped_G5__Factory'),
}

def update(fp, ref, library=False):
    fp[1] = ('' if library else 'Leaf:')+names[ref][1]
    child(fp,'descr')[1] = 'Leafy G.5: thermal PTHs REQUIRE epoxy fill, planarization and copper caps; continuous top mask opening; normal JLC stencil engineering; see FILLED-G5-CHANGE.md'
    for q in list(fp):
        if key(q)=='pad' and q[1]=='' and child(q,'layers')[1:]==['F.Mask']: fp.remove(q)
        elif key(q)=='fp_poly' and child(q,'layer')[1]=='F.Mask': fp.remove(q)
    cx,cy,w,h = (0,0,2.71,3.4) if ref=='U1' else (.96,.2,2.7,2.7)
    fp.append([S('pad'),'',S('smd'),S('rect'),[S('at'),cx,cy],[S('size'),w,h],
               [S('layers'),'F.Mask'],[S('solder_mask_margin'),0],
               [S('uuid'),str(uuid.uuid4())]])

board = sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
for ref,(old,new) in names.items():
    lib = sx.loads((H/'Leaf.pretty'/f'{old}.kicad_mod').read_text())
    update(lib,ref,True)
    (H/'Leaf.pretty'/f'{new}.kicad_mod').write_text(sx.dumps(lib)+'\n')
    update(next(v for v in items(board,'footprint') if prop(v,'Reference')[2]==ref),ref)
tb=child(board,'title_block')
child(tb,'rev')[1]='G.5'
child(tb,'date')[1]='2026-09-22'
child(tb,'title')[1]='Leafy - Wi-Fi Leaf climate controller'
for q in items(board,'gr_text'):
    q[1]=q[1].replace('LEAF HEAT','Leafy').replace('Leaf heat','Leafy').replace('REV G.4','REV G.5')
(H/'leaf-heat-v7.kicad_pcb').write_text(sx.dumps(board)+'\n')
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'))
p.SaveBoard(str(H/'leaf-heat-v7.kicad_pcb'),b)

sch=sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
tb=child(sch,'title_block')
child(tb,'rev')[1]='G.5'
child(tb,'date')[1]='2026-09-22'
child(tb,'title')[1]='Leafy - Wi-Fi Leaf climate controller'
for q in items(sch,'text'):
    q[1]=q[1].replace('LEAF HEAT','Leafy').replace('Leaf heat','Leafy').replace('G.4','G.5')
schtext=sx.dumps(sch)+'\n'
lib=(H/'Leaf.kicad_sym').read_text()
for old,new in names.values():
    schtext=schtext.replace('Leaf:'+old,'Leaf:'+new)
    lib=lib.replace('Leaf:'+old,'Leaf:'+new)
(H/'leaf-heat-v7.kicad_sch').write_text(schtext)
(H/'Leaf.kicad_sym').write_text(lib)
parts=json.loads((H/'parts.json').read_text())
for q in parts:
    if q['ref'] in names:
        q['footprint']='Leaf:'+names[q['ref']][1]
        q['notes']=q['notes'].replace(' G.4: top-side thermal-hole mask tents; stencil/process review required.','')
        q['notes']+=' G.5: epoxy-filled/copper-capped thermal holes; JLC normal stencil process.'
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
print('Applied Leafy G.5. Copper, drills, parts, placement and reference paste retained. Fresh exports/checks required.')

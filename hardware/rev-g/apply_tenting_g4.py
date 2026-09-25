"""One-time G.3 -> G.4 manufacturing overlay; preserve copper and drills."""
from pathlib import Path
import copy, hashlib, json, uuid
import sexpdata as sx
import pcbnew as p
from shapely.geometry import Point, box
from shapely.ops import triangulate, unary_union

H = Path(__file__).resolve().parent
S = sx.Symbol
def key(q): return str(q[0]) if isinstance(q, list) and q else ''
def items(q, name): return [x for x in q if key(x) == name]
def child(q, name): return next(x for x in q if key(x) == name)
def prop(q, name): return next(x for x in items(q, 'property') if x[1] == name)
def ident(): return str(uuid.uuid4())

assert (H/'history/rev-g3-before-tenting.zip').exists()
assert hashlib.sha256((H/'leaf-heat-v7.kicad_pcb').read_bytes()).hexdigest() == '8e2212587dd6681346d546cb83727e9c3ea1c5138e4bad50e19c11775217e952'
old_names = {
    'U1': 'Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias__Factory',
    'U2': 'ESP32-C3-WROOM-02U_0p3mm_Vias__Factory',
}
new_names = {'U1': 'LMR36510_DDA_TopTented_G4__Factory', 'U2': 'ESP32-C3-WROOM-02U_TopTented_G4__Factory'}

def aperture(x, y, w, h, layer):
    # Mask-only pads deliberately override U1's inherited +0.07 mm expansion.
    return [S('pad'), '', S('smd'), S('rect'),
            [S('at'), round(x, 6), round(y, 6)], [S('size'), round(w, 6), round(h, 6)],
            [S('layers'), layer], [S('solder_mask_margin'), 0], [S('solder_paste_margin'), 0],
            [S('uuid'), ident()]]

def mask_tiles(bounds, caps):
    # Positive Gerber apertures: tile the opening minus the covered rectangles.
    # Adjacent tiles touch, so they form continuous exposed solderable copper.
    x0, y0, x1, y1 = bounds
    xs = sorted({x0, x1} | {max(x0, min(x1, c[i])) for c in caps for i in [0, 2]})
    ys = sorted({y0, y1} | {max(y0, min(y1, c[i])) for c in caps for i in [1, 3]})
    result = []
    for xa, xb in zip(xs, xs[1:]):
        for ya, yb in zip(ys, ys[1:]):
            x, y = (xa+xb)/2, (ya+yb)/2
            if any(a < x < c and b < y < d for a,b,c,d in caps): continue
            result.append(aperture(x, y, xb-xa, yb-ya, 'F.Mask'))
    return result

def round_mask_caps(bounds, holes):
    # Circular caps avoid the narrow diagonal mask necks created by square
    # caps on U2's staggered hole grid. Plot the positive opening as filled
    # triangles; no negative-polarity trick or overlapping pad mask survives.
    opening=box(*bounds).difference(unary_union([Point(x,y).buffer(.31,resolution=16) for x,y in holes]))
    triangles=[t for t in triangulate(opening) if opening.covers(t.representative_point())]
    assert unary_union(triangles).symmetric_difference(opening).area < 1e-9
    return [[S('fp_poly'), [S('pts'),*[[S('xy'),round(x,6),round(y,6)] for x,y in list(t.exterior.coords)[:-1]]],
             [S('stroke'),[S('width'),0],[S('type'),S('solid')]], [S('fill'),S('solid')],
             [S('layer'),'F.Mask'], [S('uuid'),ident()]] for t in triangles]

def update(fp, ref, library=False):
    ep = '9' if ref == 'U1' else '19'
    fp[1] = new_names[ref] if library else 'Leaf:'+new_names[ref]
    child(fp, 'descr')[1] = ('G.4: component-side solder-mask tents over unfilled thermal PTHs; '
                             'back holes open; see TENTING-G4-CHANGE.md and stencil review requirements')
    holes = [child(a, 'at')[1:3] for a in items(fp,'pad') if a[1] == ep and a[2] == S('thru_hole')]
    assert len(holes) == (6 if ref == 'U1' else 12)
    for a in list(items(fp, 'pad')):
        layers = child(a,'layers')
        if a[1] == ep:
            layers[:] = [S('layers')] + [v for v in layers[1:] if v not in ['F.Mask', '*.Mask']]
            if a[2] == S('thru_hole') and 'B.Mask' not in layers: layers.append('B.Mask')
        elif a[1] == '' and set(layers[1:]) <= {'F.Mask','F.Paste'}:
            fp.remove(a)
    if ref == 'U1':
        # TI's current DDA0008B example: 2.71 x 3.40 mm mask envelope.
        # Caps cover the full nominal annulus and allow 0.16 mm to hole edge.
        caps = []
        for x,y in holes:
            lo,hi = y-.325,y+.325
            if y < -1: lo = -1.7
            if y > 1: hi = 1.7
            caps.append((x-.325,lo,x+.325,hi))
        fp.extend(mask_tiles((-1.355,-1.7,1.355,1.7),caps))
        # Two apertures, 0.30 mm central web, nominal 0.125 mm stencil.
        # Paste on the covered via caps is intentional and coalesces onto
        # the remaining exposed copper; the cap blocks access to the barrel.
        for y in [-.925,.925]: fp.append(aperture(0,y,2.71,1.55,'F.Paste'))
    else:
        cx,cy=.96,.2
        # 0.10 mm copper overlap at the outside boundary; outer caps connect
        # to the border, avoiding narrow 0.05 mm openings at the pad edge.
        fp.extend(round_mask_caps((cx-1.35,cy-1.35,cx+1.35,cy+1.35),holes))
        for x in [cx-1.1,cx,cx+1.1]:
            for y in [cy-1.1,cy,cy+1.1]: fp.append(aperture(x,y,.6,.6,'F.Paste'))

board=sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
for ref, old in old_names.items():
    local=sx.loads((H/'Leaf.pretty'/f'{old}.kicad_mod').read_text())
    update(local,ref,True)
    (H/'Leaf.pretty'/f'{new_names[ref]}.kicad_mod').write_text(sx.dumps(local)+'\n')
    fp=next(x for x in items(board,'footprint') if prop(x,'Reference')[2] == ref)
    update(fp,ref)
child(child(board,'title_block'),'rev')[1]='G.4'
tb=child(board,'title_block')
if items(tb,'date'):child(tb,'date')[1]='2026-09-15'
else:tb.append([S('date'),'2026-09-15'])
for q in items(board,'gr_text'): q[1]=q[1].replace('REV G.3','REV G.4')
(H/'leaf-heat-v7.kicad_pcb').write_text(sx.dumps(board)+'\n')
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'));p.SaveBoard(str(H/'leaf-heat-v7.kicad_pcb'),b)

sch=sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
for ref in old_names:
    inst=next(x for x in items(sch,'symbol') if prop(x,'Reference')[2]==ref)
    prop(inst,'Footprint')[2]='Leaf:'+new_names[ref]
child(child(sch,'title_block'),'rev')[1]='G.4'
child(child(sch,'title_block'),'date')[1]='2026-09-15'
for q in items(sch,'text'):q[1]=q[1].replace('G.3','G.4')
sch_text=sx.dumps(sch)+'\n'
for ref,old in old_names.items():sch_text=sch_text.replace('Leaf:'+old,'Leaf:'+new_names[ref])
(H/'leaf-heat-v7.kicad_sch').write_text(sch_text)

lib=(H/'Leaf.kicad_sym').read_text()
for ref,old in old_names.items():lib=lib.replace('Leaf:'+old,'Leaf:'+new_names[ref])
(H/'Leaf.kicad_sym').write_text(lib)
parts=json.loads((H/'parts.json').read_text())
for q in parts:
    if q['ref'] in old_names:
        q['footprint']='Leaf:'+new_names[q['ref']]
        q['notes']+=' G.4: top-side thermal-hole mask tents; stencil/process review required.'
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
print('Applied G.4 mask/paste overlay; copper/drill verification and release exports required.')

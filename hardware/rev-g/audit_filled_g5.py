"""Release checks for Leafy G.5 against the preserved, received-parts G.4 design.

Native geometry and plotted mask/paste are checked separately. Gerbers cannot
prove physical resin filling: the supplier must implement the process notes.
"""
from pathlib import Path
import collections, copy, csv, hashlib, json, sys, zipfile
import xml.etree.ElementTree as ET
import sexpdata as sx
from gerbonara import GerberFile
from gerbonara.utils import MM
from shapely.geometry import Point, Polygon, box, GeometryCollection
from shapely.affinity import rotate

H = Path(__file__).resolve().parent
E = H / 'exports'
F = E / 'fabrication'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def key(q): return str(q[0]) if isinstance(q, list) and q else ''
def items(q, k): return [v for v in q if key(v) == k]
def child(q, k): return next(v for v in q if key(v) == k)
def prop(q, k): return next(v[2] for v in items(q, 'property') if v[1] == k)
def bag(q, ks): return collections.Counter(sx.dumps(v) for v in q if key(v) in ks)
def copper_pads(fp):
    result = []
    for pad in items(fp, 'pad'):
        copper = [v for v in child(pad, 'layers')[1:] if v.endswith('.Cu')]
        if not copper and pad[2] != sx.Symbol('np_thru_hole'): continue
        q = copy.deepcopy(pad)
        child(q, 'layers')[:] = [sx.Symbol('layers'), *copper]
        q = [v for v in q if key(v) not in {'solder_mask_margin', 'solder_paste_margin', 'solder_paste_margin_ratio'}]
        result.append(sx.dumps(q))
    return collections.Counter(result)

def primitive_shape(p):
    if type(p).__name__ == 'Rectangle':
        return rotate(box(p.x-p.w/2, p.y-p.h/2, p.x+p.w/2, p.y+p.h/2), p.rotation, origin=(p.x,p.y), use_radians=True)
    if type(p).__name__ == 'Circle': return Point(p.x,p.y).buffer(p.r, resolution=64)
    if type(p).__name__ == 'ArcPoly':
        assert all(v is None for v in p.arc_centers), 'Unexpected curved mask/paste polygon'
        return Polygon(p.outline)
    raise AssertionError('Unexpected Gerber primitive: '+type(p).__name__)

def gerber_shape(path):
    result = GeometryCollection()
    for obj in GerberFile.open(path).objects:
        local = GeometryCollection()
        for prim in obj.to_primitives(unit=MM):
            shape = primitive_shape(prim)
            local = local.union(shape) if prim.polarity_dark == obj.polarity_dark else local.difference(shape)
        result = result.union(local) if obj.polarity_dark else result.difference(local)
    return result

def main():
    with zipfile.ZipFile(H/'history/rev-g4-before-filled-g5.zip') as z:
        manifest = json.loads(z.read('BASELINE-MANIFEST.json'))
        for n, digest in manifest.items(): assert hashlib.sha256(z.read(n)).hexdigest() == digest, n
        old = sx.loads(z.read('leaf-heat-v7.kicad_pcb').decode())
        board = sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
        oldfps = {prop(f,'Reference'): f for f in items(old,'footprint')}
        fps = {prop(f,'Reference'): f for f in items(board,'footprint')}
        assert fps.keys() == oldfps.keys()
        assert bag(old, {'segment','arc','via','net','layers','zone','gr_line','gr_arc','gr_rect','setup'}) == bag(board, {'segment','arc','via','net','layers','zone','gr_line','gr_arc','gr_rect','setup'}), 'Electrical copper, drill routing, outline or stackup changed'
        for ref, fp in fps.items():
            assert bag(fp, {'at','path','model','attr'}) == bag(oldfps[ref], {'at','path','model','attr'}), ref
            assert copper_pads(fp) == copper_pads(oldfps[ref]), (ref, 'Copper/pin/drill changed')
            if ref not in {'U1','U2'}: assert fp == oldfps[ref], (ref,'Unexpected footprint change')
        oldsch = sx.loads(z.read('leaf-heat-v7.kicad_sch').decode())
        sch = sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
        assert bag(oldsch, {'wire','junction','label','global_label','no_connect'}) == bag(sch, {'wire','junction','label','global_label','no_connect'})
        parts = json.loads((H/'parts.json').read_text())
        oldparts = json.loads(z.read('parts.json'))
        assert len(parts) == len(oldparts) == 55
        for a, b in zip(oldparts, parts):
            assert {k:v for k,v in a.items() if k not in {'footprint','notes'}} == {k:v for k,v in b.items() if k not in {'footprint','notes'}}, a['ref']
        assert (H/'accessories.json').read_bytes() == z.read('accessories.json')
        for name in ['BOM-HAND.csv','MOUSER-TWO-BOARDS.csv','MOUSER-CART-WITH-SUPPLIES.csv','CPL-FACTORY-JLCPCB.csv']:
            assert (E/name).read_bytes() == z.read('exports/'+name), name

        # This intentionally fails on G.4: the central mask must now be one
        # continuous opening, with no local solder-mask tents over the holes.
        groups = [('U1','9',6,.33,(0,0),(2.71,3.4)), ('U2','19',12,.30,(.96,.2),(2.7,2.7))]
        expected_holes = []
        for ref, ep, count, drill, centre, size in groups:
            fp = fps[ref]
            masks = [p for p in items(fp,'pad') if child(p,'layers')[1:] == ['F.Mask']]
            polygons = [p for p in items(fp,'fp_poly') if child(p,'layer')[1] == 'F.Mask']
            assert len(masks) == 1 and not polygons, (ref, 'Remove fragmented G.4 mask tents; use a continuous exposed thermal pad')
            assert child(masks[0],'at')[1:3] == list(centre)
            assert child(masks[0],'size')[1:3] == list(size)
            assert child(masks[0],'solder_mask_margin')[1] == 0
            holes = [p for p in items(fp,'pad') if p[1] == ep and p[2] == sx.Symbol('thru_hole')]
            assert len(holes) == count
            fx, fy = child(fp,'at')[1:3]
            for pad in holes:
                assert child(pad,'drill')[1] == drill
                assert child(pad,'zone_connect')[1] == 2, 'Thermal heat paths must remain solid'
                x,y = child(pad,'at')[1:3]
                expected_holes.append({'Reference':ref, 'X mm':f'{fx+x:.6f}', 'Y mm':f'{100-fy-y:.6f}', 'Drill mm':f'{drill:.2f}'})
        texts = [q[1] for q in items(board,'gr_text')]
        assert any('Leafy' in t and 'REV G.5' in t for t in texts)
        assert not any('LEAF HEAT' in t.upper() for t in texts)
        assert child(child(board,'title_block'),'rev')[1] == 'G.5'
        assert child(child(sch,'title_block'),'rev')[1] == 'G.5'
        print('PASS: native electrical/mechanical/received-parts compatibility, thermal mask geometry and Leafy branding')
        if '--native-only' in sys.argv: return

        def nets(root): return {n.attrib['name']:sorted((v.attrib['ref'],v.attrib['pin']) for v in n.findall('node')) for n in root.findall('./nets/net')}
        assert nets(ET.fromstring(z.read('exports/leaf-heat-v7.net.xml'))) == nets(ET.parse(E/'leaf-heat-v7.net.xml').getroot())
        def fab(blob): return '\n'.join(l for l in blob.decode().splitlines() if not l.startswith(('G04','#',';','%TF.CreationDate','%TF.ProjectId','%TF.FileFunction')))
        for path in F.iterdir():
            if path.suffix in {'.drl','.gtl','.gbl','.g1','.g2','.gbp','.gbs','.gtp'}:
                assert fab(path.read_bytes()) == fab(z.read('exports/fabrication/'+path.name)), (path.name,'Unexpected fabrication change')

    top = gerber_shape(F/'leaf-heat-v7-F_Mask.gts')
    back = gerber_shape(F/'leaf-heat-v7-B_Mask.gbs')
    paste = gerber_shape(F/'leaf-heat-v7-F_Paste.gtp')
    metrics = {}
    for ref, ep, count, drill, centre, size in groups:
        fx,fy = child(fps[ref],'at')[1:3]
        cx,cy = fx+centre[0],100-fy-centre[1]
        rect = box(cx-size[0]/2,cy-size[1]/2,cx+size[0]/2,cy+size[1]/2)
        crop = rect.buffer(.05,join_style=2)
        assert top.intersection(crop).symmetric_difference(rect).area < 1e-7, (ref,'Mask plot contains a tent or wrong boundary')
        for hole in [q for q in expected_holes if q['Reference'] == ref]:
            disk = Point(float(hole['X mm']),float(hole['Y mm'])).buffer(drill/2,resolution=64)
            assert top.buffer(1e-8).covers(disk), (ref,'Top hole artwork still tented')
            assert back.buffer(1e-8).covers(disk), (ref,'Back mask unexpected')
        reference_paste = paste.intersection(crop)
        assert abs(reference_paste.area - (8.401 if ref=='U1' else 3.24)) < 1e-6
        metrics[ref] = {'count':count, 'drill_mm':drill, 'continuous_top_mask_opening_mm':list(size), 'mask_area_mm2':round(rect.area,6), 'reference_paste_area_mm2':round(reference_paste.area,6)}
    rows = list(csv.DictReader((E/'THERMAL-FILL-LOCATIONS.csv').open()))
    assert len(rows) == 18
    assert sorted(tuple(q[k] for k in ['Reference','X mm','Y mm','Drill mm']) for q in rows) == sorted(tuple(q[k] for k in ['Reference','X mm','Y mm','Drill mm']) for q in expected_holes)
    assert all(q['Treatment']=='Epoxy filled, planarized and copper capped' for q in rows)
    native = json.loads((E/'independent-audit.json').read_text())
    assert native['board_sha256'] == sha(H/'leaf-heat-v7.kicad_pcb')
    assert native['schematic_sha256'] == sha(H/'leaf-heat-v7.kicad_sch')
    drc = json.loads((E/'drc-final.json').read_text())
    erc = json.loads((E/'erc.json').read_text())
    assert not any(drc[k] for k in ['violations','unconnected_items','schematic_parity'])
    assert not any(q['violations'] for q in erc['sheets'])
    # Compare quantities/MPNs to the last saved supplier basket, not live stock.
    received = json.loads((H/'quotations/2026-09-16/cart-verification.json').read_text())['Mouser']['rows']
    ordered = {q['mpn']:q['quantity'] for q in received}
    for q in csv.DictReader((E/'MOUSER-TWO-BOARDS.csv').open()):
        assert ordered[q['Manufacturer Part Number']] >= int(q['Quantity']), q
    report = {'status':'PASS', 'revision':'G.5', 'product':'Leafy', 'pcb_sha256':native['board_sha256'], 'schematic_sha256':native['schematic_sha256'], 'baseline_archive_sha256':sha(H/'history/rev-g4-before-filled-g5.zip'), 'metrics':metrics,
              'checks':['All copper, nets, drills, layer stackup, component placements and mechanical geometry unchanged from G.4', 'All 55 MPNs and all accessory requirements unchanged', 'Mouser hand BOM and basket files byte-identical; recorded purchased quantities cover required parts', 'Four copper Gerbers, both drill files, back mask and reference paste unchanged after header normalization', 'All 18 hole ends exposed in mask plots for required epoxy fill and copper cap process', 'Fill-location CSV agrees with the native board', 'Leafy / REV G.5 printed on the board', 'Fresh ERC/DRC including zone refill and schematic parity zero'],
              'limitations':'This verifies artwork and compatibility, not completed fabrication. JLC must apply filling/capping to all listed thermal PTHs, including 0.33 mm. Normal JLC stencil process is authorized; final placement/DFM review and prototype tests remain.'}
    (E/'filled-g5-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__': main()

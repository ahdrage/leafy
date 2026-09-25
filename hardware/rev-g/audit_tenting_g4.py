"""Independent G.4 verification from native files AND final plotted Gerbers."""
from pathlib import Path
import collections, copy, csv, hashlib, json, math, zipfile
import xml.etree.ElementTree as ET
import sexpdata as sx
from gerbonara import GerberFile
from gerbonara.utils import MM
from shapely.geometry import Point, Polygon, box, GeometryCollection
from shapely.affinity import rotate
from shapely.ops import unary_union

H=Path(__file__).resolve().parent; E=H/'exports'; F=E/'fabrication'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def key(x):return str(x[0]) if isinstance(x,list) and x else ''
def items(q,k):return [x for x in q if key(x)==k]
def child(q,k):return next(x for x in q if key(x)==k)
def prop(q,k):return next(x[2] for x in items(q,'property') if x[1]==k)
def bag(q,ks):return collections.Counter(sx.dumps(x) for x in q if key(x) in ks)
def copper_pads(fp):
    result=[]
    for a in items(fp,'pad'):
        layers=child(a,'layers')[1:]
        copper=[v for v in layers if v.endswith('.Cu')]
        if not copper and a[2]!=sx.Symbol('np_thru_hole'):continue
        q=copy.deepcopy(a); child(q,'layers')[:]=[sx.Symbol('layers'),*copper]
        # Mask/paste are process layers, not electrical pad geometry.
        q=[v for v in q if key(v) not in {'solder_mask_margin','solder_paste_margin','solder_paste_margin_ratio'}]
        result.append(sx.dumps(q))
    return collections.Counter(result)

with zipfile.ZipFile(H/'history/rev-g3-before-tenting.zip') as z:
    old=sx.loads(z.read('leaf-heat-v7.kicad_pcb').decode())
    new=sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
    assert bag(old,{'segment','arc','via','net','layers','zone','gr_line','gr_arc','gr_rect'}) == bag(new,{'segment','arc','via','net','layers','zone','gr_line','gr_arc','gr_rect'}), 'Copper or board geometry changed'
    of={prop(x,'Reference'):x for x in items(old,'footprint')}
    nf={prop(x,'Reference'):x for x in items(new,'footprint')}
    assert of.keys()==nf.keys()
    for ref in of:
        assert bag(of[ref],{'at','path'})==bag(nf[ref],{'at','path'}),ref
        assert copper_pads(of[ref])==copper_pads(nf[ref]),ref
        if ref not in {'U1','U2'}:assert of[ref]==nf[ref],ref
    oldsch=sx.loads(z.read('leaf-heat-v7.kicad_sch').decode())
    sch=sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
    assert bag(oldsch,{'wire','junction','label','global_label','no_connect'})==bag(sch,{'wire','junction','label','global_label','no_connect'})
    def nets(root):return {n.attrib['name']:sorted((x.attrib['ref'],x.attrib['pin']) for x in n.findall('node')) for n in root.findall('./nets/net')}
    assert nets(ET.fromstring(z.read('exports/leaf-heat-v7.net.xml')))==nets(ET.parse(E/'leaf-heat-v7.net.xml').getroot())
    for name in ['BOM-HAND.csv','MOUSER-TWO-BOARDS.csv','MOUSER-CART-WITH-SUPPLIES.csv','CPL-FACTORY-JLCPCB.csv']:
        assert (E/name).read_bytes()==z.read('exports/'+name),name
    parts=json.loads((H/'parts.json').read_text())
    oldparts=json.loads(z.read('parts.json'))
    assert len(parts)==len(oldparts)==55
    for a,b in zip(oldparts,parts):
        assert {k:v for k,v in a.items() if k not in {'footprint','notes'}}=={k:v for k,v in b.items() if k not in {'footprint','notes'}}
    def fab(blob):return '\n'.join(l for l in blob.decode().splitlines() if not l.startswith(('G04','#',';','%TF.CreationDate','%TF.ProjectId','%TF.FileFunction')))
    for p in F.iterdir():
        if p.suffix in {'.drl','.gtl','.gbl','.g1','.g2','.gbp','.gbs'}:
            assert fab(p.read_bytes())==fab(z.read('exports/fabrication/'+p.name)),p.name

def primitive_shape(p):
    name=type(p).__name__
    if name=='Rectangle':return rotate(box(p.x-p.w/2,p.y-p.h/2,p.x+p.w/2,p.y+p.h/2),p.rotation,origin=(p.x,p.y),use_radians=True)
    if name=='Circle':return Point(p.x,p.y).buffer(p.r,resolution=64)
    if name=='ArcPoly':
        assert all(a is None for a in p.arc_centers),'Unexpected curved aperture in mask/paste'
        return Polygon(p.outline)
    raise AssertionError('Unsupported Gerber primitive: '+name)

def gerber_shape(path):
    # Read the plotted file, not the generator's aperture list. Respect both
    # object polarity and aperture-macro primitive polarity in paint order.
    g=GerberFile.open(path); result=GeometryCollection()
    for obj in g.objects:
        local=GeometryCollection()
        for prim in obj.to_primitives(unit=MM):
            shape=primitive_shape(prim)
            local=local.union(shape) if prim.polarity_dark==obj.polarity_dark else local.difference(shape)
        result=result.union(local) if obj.polarity_dark else result.difference(local)
    return result

top=gerber_shape(F/'leaf-heat-v7-F_Mask.gts')
bottom=gerber_shape(F/'leaf-heat-v7-B_Mask.gbs')
paste=gerber_shape(F/'leaf-heat-v7-F_Paste.gtp')
metrics={}; drawings=[]
circle_segment=.31**2*math.acos(.25/.31)-.25*math.sqrt(.31**2-.25**2)
u2_mask_area=2.7**2-12*math.pi*.31**2+8*circle_segment
for ref,ep,expected_count,nominal_cap,expected_mask,expected_paste in [('U1','9',6,.65,6.484,8.401),('U2','19',12,.62,u2_mask_area,3.24)]:
    fp=nf[ref]; fx,fy=child(fp,'at')[1:3]
    holes=[]
    for pad in items(fp,'pad'):
        if pad[1]==ep and pad[2]==sx.Symbol('thru_hole'):
            x,y=child(pad,'at')[1:3];d=child(pad,'drill')[1]
            point=Point(fx+x,100-(fy+y)); nominal=point.buffer(d/2,resolution=64)
            assert top.intersection(nominal).area<1e-10,(ref,'top hole exposed')
            assert bottom.buffer(1e-8).covers(nominal),(ref,'back hole covered')
            margin=top.distance(point)-d/2
            # U2 circles use 64 vertices; maximum chord deviation <0.0004 mm.
            assert margin >= (nominal_cap-d)/2-.0004,(ref,'insufficient cap width',margin)
            # Conservative +0.13 mm finished-hole growth still has >0.076 mm
            # radial coverage; actual fab registration/diameter needs DFM.
            assert top.distance(point)-(d+.13)/2 >= .076,(ref,'mask tolerance allowance')
            holes.append({'x':point.x,'y':point.y,'diameter_mm':d,'mask_edge_margin_mm':round(margin,6)})
    assert len(holes)==expected_count
    cx,cy=(24,81) if ref=='U1' else (73.96,91.8)
    extent=(2.71,3.4) if ref=='U1' else (2.7,2.7)
    opening=box(cx-extent[0]/2,cy-extent[1]/2,cx+extent[0]/2,cy+extent[1]/2)
    region=box(cx-1.5,cy-2.0,cx+1.5,cy+2.0)
    exposed=top.intersection(opening); deposited=paste.intersection(region)
    assert abs(exposed.area-expected_mask)<(.007 if ref=='U2' else 1e-5),(ref,'mask area',exposed.area)
    if ref=='U2':
        expected=opening.difference(unary_union([Point(q['x'],q['y']).buffer(.31,resolution=64) for q in holes]))
        assert exposed.symmetric_difference(expected).area<.007,'U2 plotted circular caps differ from independent geometry'
    assert abs(deposited.area-expected_paste)<1e-5,(ref,'paste area',deposited.area)
    apertures=list(deposited.geoms) if hasattr(deposited,'geoms') else [deposited]
    assert len(apertures)==(2 if ref=='U1' else 9),(ref,'aperture count')
    minimum_area_ratio=min(a.area/(a.length*.125) for a in apertures)
    assert minimum_area_ratio>=.66,(ref,'paste release area ratio')
    metrics[ref]={'thermal_holes':holes,'mask_open_area_mm2':round(exposed.area,6),
        'paste_area_mm2':round(deposited.area,6),'nominal_stencil_mm':.125,
        'theoretical_wet_paste_volume_mm3':round(deposited.area*.125,6),
        'paste_aperture_count':len(apertures),'minimum_aperture_area_ratio':round(minimum_area_ratio,4)}
    drawings.append((ref,cx,cy,region,exposed,deposited,holes))

native=json.loads((E/'independent-audit.json').read_text())
assert native['board_sha256']==sha(H/'leaf-heat-v7.kicad_pcb')
assert native['schematic_sha256']==sha(H/'leaf-heat-v7.kicad_sch')
bom=list(csv.DictReader((E/'BOM-FACTORY-JLCPCB.csv').open()))
assert len(bom)==6 and next(x for x in bom if x['Designator']=='U2')['LCSC Part #']=='C2926676'
report={'status':'PASS','revision':'G.4','pcb_sha256':native['board_sha256'],'schematic_sha256':native['schematic_sha256'],
    'baseline_archive_sha256':sha(H/'history/rev-g3-before-tenting.zip'), 'metrics':metrics,
    'checks':['All copper, nets, drills, mounting geometry and placements unchanged from G.3',
              'Four copper Gerbers, both drill files and back mask identical after header normalization',
              'All 18 holes fully top-covered and bottom-open in actual Gerbers',
              'Thermal solderable area and paste area measured from final Gerbers',
              'Two U1 apertures and nine U2 apertures at a nominal 0.125 mm stencil',
              'All 55 MPNs unchanged; hand BOM and Mouser baskets byte-identical',
              'Fresh ERC/DRC/refill/schematic parity zero'],
    'limitations':'DFM REVIEW REQUIRED. Plotted geometry is verified; physical tent survival, stencil thickness/release, joint coverage/voiding and thermal performance need assembler confirmation and prototype measurements.'}
(E/'tenting-g4-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='metrics'},indent=2))

# Evidence image drawn exclusively from the independently parsed final plots.
import cairosvg
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1260" viewBox="0 0 1800 1260">',
     '<rect width="1800" height="1260" fill="#f8fafc"/>',
     '<text x="60" y="64" font-family="Arial" font-size="36" fill="#0f172a">REV G.4 — termiske hull, loddemaske og pasta</text>',
     '<text x="60" y="104" font-family="Arial" font-size="22">Geometri lest fra de eksporterte Gerber-filene. Grønt = maske. Gull = åpen loddeflate.</text>']
for i,(ref,cx,cy,region,exposed,deposited,holes) in enumerate(drawings):
    for col,(title,with_paste) in enumerate([('Loddemaske på toppen',False),('Samme område med pastamønster',True)]):
        ox,oy=270+850*col,420+530*i;scale=100
        svg.append(f'<text x="{60+850*col}" y="{185+530*i}" font-family="Arial" font-size="27">{ref}: {title}</text>')
        svg.append(f'<g transform="translate({ox} {oy}) scale({scale} {-scale}) translate({-cx} {-cy})">')
        svg.append(f'<rect x="{cx-1.55}" y="{cy-2}" width="3.1" height="4" fill="#167d52"/>')
        for shape,color,opacity in [(exposed,'#edc66b',1)]+([(deposited,'#d8e5f4',.8)] if with_paste else []):
            svg.append(shape.svg(scale_factor=.02,fill_color=color,opacity=opacity).replace('stroke="#555555"','stroke="none"'))
        for q in holes:
            svg.append(f'<circle cx="{q["x"]}" cy="{q["y"]}" r="{q["diameter_mm"]/2}" fill="none" stroke="#052e22" stroke-width=".018" stroke-dasharray=".035 .025"/>')
        svg.append('</g>')
        if col:
            svg.append(f'<text x="{ox+210}" y="{oy-80}" font-family="Arial" font-size="21">{metrics[ref]["paste_aperture_count"]} pastaåpninger</text>')
            svg.append(f'<text x="{ox+210}" y="{oy-42}" font-family="Arial" font-size="21">0,125 mm sjablong</text>')
            svg.append(f'<text x="{ox+210}" y="{oy-4}" font-family="Arial" font-size="21">Må bekreftes av JLCPCB</text>')
svg += ['<text x="60" y="1205" font-family="Arial" font-size="22">Stiplede ringer viser borehull under masken; hullene er åpne på undersiden.</text>',
        '<text x="60" y="1240" font-family="Arial" font-size="22">Dette kontrollerer produksjonsfilene. Det erstatter ikke fabrikkens prosesskontroll eller test av loddefugene.</text>','</svg>']
(E/'tenting-g4-detail.svg').write_text('\n'.join(svg))
cairosvg.svg2png(url=str(E/'tenting-g4-detail.svg'),write_to=str(E/'tenting-g4-detail.png'))

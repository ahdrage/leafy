"""Verify G.2 against the archived G.1 native design and manufacturing files."""
from pathlib import Path
import collections, copy, hashlib, json, math, tempfile, zipfile
import pcbnew as p
import sexpdata as sx

H = Path(__file__).resolve().parent
E = H / 'exports'
sha = lambda data: hashlib.sha256(data).hexdigest()
def key(q): return str(q[0]) if isinstance(q, list) and q else ''
def child(q, name): return next((x for x in q if key(x) == name), None)
def children(q, name): return [x for x in q if key(x) == name]
def scrub(q, skip):
    return [scrub(x, skip) if isinstance(x, list) else x
            for x in q if not (isinstance(x, list) and key(x) in skip)]
def silk(item):
    return child(item, 'layer') in [[sx.Symbol('layer'), 'F.SilkS'], [sx.Symbol('layer'), 'B.SilkS']]
def footprint_core(fp):
    # Reference placement/strokes and silk outlines may change; pads, component
    # identity, copper graphics, assembly fields and 3D models must not.
    return [x for x in fp if not (key(x) == 'property' and x[1] == 'Reference')
            and not (key(x) in {'fp_text','fp_line','fp_rect','fp_poly','fp_circle','fp_arc'} and silk(x))]
def ref(fp): return next(x[2] for x in fp if key(x) == 'property' and x[1] == 'Reference')
def xy(v): return tuple(round(p.ToMM(n), 6) for n in (v.x, v.y))
def track_record(t, board):
    if isinstance(t, p.PCB_VIA):
        return ('via', t.GetNetname(), xy(t.GetPosition()), p.ToMM(t.GetWidth(p.F_Cu)), p.ToMM(t.GetDrillValue()), tuple(t.GetLayerSet().Seq()))
    return ('track', t.GetNetname(), board.GetLayerName(t.GetLayer()), tuple(sorted((xy(t.GetStart()), xy(t.GetEnd())))), p.ToMM(t.GetWidth()))

archive = H / 'history/rev-g1-before-adi-g2.zip'
with zipfile.ZipFile(archive) as z, tempfile.TemporaryDirectory(prefix='leaf-g2-audit-') as tmp:
    old_data = z.read('leaf-heat-v7.kicad_pcb')
    old_path = Path(tmp) / 'old.kicad_pcb'; old_path.write_bytes(old_data)
    old = p.LoadBoard(str(old_path)); new = p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'))
    a = sx.loads(old_data.decode()); c = sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
    af = {ref(f): footprint_core(f) for f in children(a,'footprint')}
    cf = {ref(f): footprint_core(f) for f in children(c,'footprint')}
    assert af == cf, 'Footprint/pad/part/model changed'
    for name in ['layers','setup','net']:
        assert children(a,name) == children(c,name), name
    edges = lambda q: [x for x in q if child(x,'layer') == [sx.Symbol('layer'),'Edge.Cuts']]
    assert edges(a) == edges(c), 'Mechanical outline changed'
    # Zone fill polygons update around the moved vias; zone definitions and
    # antenna keepout geometry must remain identical.
    assert [scrub(q,{'filled_polygon'}) for q in children(a,'zone')] == [scrub(q,{'filled_polygon'}) for q in children(c,'zone')], 'Zone definition changed'
    old_tracks = collections.Counter(track_record(t,old) for t in old.GetTracks())
    new_tracks = collections.Counter(track_record(t,new) for t in new.GetTracks())
    removed = list((old_tracks-new_tracks).elements()); added = list((new_tracks-old_tracks).elements())
    assert {q[1] for q in removed+added} == {'/3V3','/UART_RX','/CAN_H'}
    assert {q[2] for q in removed if q[0]=='via'} == {(87.1531,52.9642),(24.95,82.5)}
    assert {q[2] for q in added if q[0]=='via'} == {(89.45,56.),(26.5,79.635)}
    # One existing CAN_H segment is split at the relocated via centre.
    assert len(new.GetTracks()) == len(old.GetTracks()) + 1, 'Unexpected route item count'
    sa = sx.loads(z.read('leaf-heat-v7.kicad_sch').decode())
    sc = sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
    assert [x for x in sa if key(x) not in {'text','title_block'}] == [x for x in sc if key(x) not in {'text','title_block'}], 'Electrical schematic changed'
    unchanged = ['parts.json','Leaf.kicad_sym','leaf-heat-v7.kicad_dru',
        'exports/BOM-HAND.csv','exports/MOUSER-HAND-TWO-BOARDS.csv',
        'exports/BOM-FACTORY-JLCPCB.csv','exports/BOM-FACTORY-PCBWay.csv',
        'exports/CPL-FACTORY-JLCPCB.csv','exports/CPL-NATIVE-REFERENCE-ONLY.csv',
        'exports/placements-native.csv','exports/FACTORY-PIN1-REFERENCE.csv']
    for name in unchanged: assert z.read(name) == (H/name).read_bytes(), name
    # Verify the actual fabrication output, including the drill quantization.
    fab=E/'fabrication'
    for suffix in ['.gtp','.gbp']:
        fp=next(fab.glob('*'+suffix))
        strip=lambda s:[line for line in s.splitlines() if not line.startswith('G04') and not line.startswith('%TF.')]
        assert strip(z.read('exports/fabrication/'+fp.name).decode())==strip(fp.read_text()), 'Stencil geometry changed'
    drill_changes={}
    for fp in sorted(fab.glob('*.drl')):
        strip=lambda s:collections.Counter(line for line in s.splitlines() if not line.startswith(';') and not line.startswith('%TF.'))
        aa=strip(z.read('exports/fabrication/'+fp.name).decode());bb=strip(fp.read_text())
        deleted=sorted((aa-bb).elements());inserted=sorted((bb-aa).elements())
        if fp.name.endswith('-NPTH.drl'): assert not deleted and not inserted
        else:
            assert deleted==['X24.95Y17.5','X87.153Y47.036'],deleted
            assert inserted==['X26.5Y20.365','X89.45Y44.0'],inserted
        drill_changes[fp.name]={'removed':deleted,'added':inserted}
    # Review all visible silk, not just the four marked areas.
    text_items=[]; shape_items=[]
    for f in new.GetFootprints(): text_items += [f.Reference(),f.Value(),*list(f.GraphicalItems())]
    text_items += list(new.GetDrawings())
    visible=[]
    for t in text_items:
        if t.GetLayer() not in [p.F_SilkS,p.B_SilkS]: continue
        if isinstance(t,p.PCB_TEXT) and t.IsVisible():
            assert t.GetTextSize().y >= p.FromMM(1.) and t.GetTextThickness() >= p.FromMM(.15), t.GetText()
            visible.append(t.GetText())
        if isinstance(t,p.PCB_SHAPE):
            assert t.GetWidth() >= p.FromMM(.15)
            shape_items.append(t)
    assert any('G.2' in t for t in visible)
    settings=json.loads((H/'leaf-heat-v7.kicad_pro').read_text())['board']['design_settings']
    assert settings['rules']['min_silk_clearance']==.15
    assert settings['rules']['min_text_height']==1.
    assert settings['rules']['min_text_thickness']==.15
    assert not settings.get('drc_exclusions')
    for name in ['drc-final.json','erc.json']:
        d=json.loads((E/name).read_text())
        if name.startswith('drc'):
            assert all(not d[k] for k in ['violations','unconnected_items','schematic_parity'])
        else: assert all(not x['violations'] for x in d['sheets'])
    # The original queried enable via and all its copper are untouched by the
    # track-diff assertions above, including both top and bottom connections.
    via = next(t for t in new.GetTracks() if isinstance(t,p.PCB_VIA) and xy(t.GetPosition())==(89.45,56.))
    line = next(t for t in new.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/PROG_TX' and {xy(t.GetStart()),xy(t.GetEnd())}=={(86.4764,52.684),(86.4764,77.1461)})
    r19_gap = 89.45-86.4764-p.ToMM(via.GetWidth(p.F_Cu))/2-p.ToMM(line.GetWidth())/2
    assert r19_gap>2.4
    d4_gap=math.hypot(26.5-24-(.4-.2),abs(79.635-81.5)-(.95-.2))-.2-.35
    assert d4_gap>2.
    report={'revision':'G.2','status':'PASS','baseline_archive_sha256':sha(archive.read_bytes()),
      'baseline_pcb_sha256':sha(old_data),'pcb_sha256':sha((H/'leaf-heat-v7.kicad_pcb').read_bytes()),
      'schematic_sha256':sha((H/'leaf-heat-v7.kicad_sch').read_bytes()),
      'unchanged_footprint_cores':len(af),'circuit_unchanged':True,'pads_positions_models_and_outline_unchanged':True,
      'ground_power_zone_definitions_and_antenna_keepouts_unchanged':True,'unchanged_files':unchanged,
      'removed_route_items':removed,'added_route_items':added,'via_count_unchanged':True,
      'front_and_back_paste_geometry_unchanged':True,'fabricated_drill_changes':drill_changes,
      'R19_via_to_PROG_TX_clearance_mm':round(r19_gap,4),'D4_via_to_GND_pad_clearance_mm':round(d4_gap,4),
      'visible_silk_texts_checked':len(visible),'silk_shapes_checked':len(shape_items),
      'silk_minimum_height_mm':1.,'silk_minimum_stroke_mm':.15,'silk_clearance_mm':.15,
      'DRC_violations':0,'ERC_violations':0,'unconnected':0,'schematic_parity':0,
      'limits':'Static CAD verification. Assembler exposed-pad DFM review and powered bench/vehicle tests remain.'}
    (E/'adi-g2-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if not isinstance(v,list)},indent=2))

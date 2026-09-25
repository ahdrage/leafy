"""Create Rev F from the final, checked Rev E native files.

This is a narrow revision, not a reroute. It records every copper change and
keeps the source revision byte-for-byte intact. Run with KiCad's Python venv.
"""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import sexpdata as sx
import pcbnew as p

H = Path(__file__).resolve().parent
OLD = H.parent / 'rev-e'
OUT = H / 'exports'
OUT.mkdir(exist_ok=True)
NAME = 'leaf-heat-v6'

def child(q, k):
    return next((x for x in q if isinstance(x, list) and x and str(x[0]) == k), None)

def children(q, k):
    return [x for x in q if isinstance(x, list) and x and str(x[0]) == k]

def sha(q):
    return hashlib.sha256(q.read_bytes()).hexdigest()

baseline = {q.name: sha(q) for q in OLD.glob('leaf-heat-v5.kicad_*')
            if q.suffix != '.kicad_prl'}
(OUT / 'baseline-rev-e-sha256.json').write_text(json.dumps(baseline, indent=2) + '\n')
shutil.copytree(OLD / 'Leaf.pretty', H / 'Leaf.pretty', dirs_exist_ok=True)
for name in ['fp-lib-table', 'sym-lib-table', 'testpoints.json']:
    shutil.copy2(OLD / name, H / name)
for suffix in ['kicad_pro', 'kicad_dru']:
    shutil.copy2(OLD / ('leaf-heat-v5.' + suffix), H / (NAME + '.' + suffix))

parts = json.loads((OLD / 'parts.json').read_text())
meta = {q['ref']: q for q in parts}
meta['U3'].update(symbol='Leaf:TCAN3404DRQ1', value='TCAN3404DRQ1',
                  mpn='TCAN3404DRQ1', datasheet='https://www.ti.com/lit/gpn/TCAN3404-Q1',
                  notes='Rev F only: pin 5 SHDN is tied to GND; pin 8 STB remains MCU-controlled with pull-up. Not interchangeable with TCAN3403 on this PCB.')
meta['U3']['nets']['5'] = 'GND'
meta['J1'].update(mpn='182-009-113R561', footprint='Leaf:NorComp_182-009-113R561__Hand',
                 notes='Male DB9 with fork boardlocks and fitted 4-40 female screwlocks. Same 2.77 x 2.84 mm contacts and 24.99 mm anchor centres. Nissan OVMS cable pinout only; verify actual cable mating before power.')
for ref in ['C5', 'C6', 'C7']:
    meta[ref].update(mpn='C1210C226K3RAC7210', manufacturer='KEMET',
                     datasheet='https://search.kemet.com/component-documentation/download/specsheet/C1210C226K3RAC7210',
                     notes='22 uF, 25 V, X7R, 10%, 1210. Fit all three output capacitors. Purchase cut tape, not a full reel. See DESIGN-REVIEW.md for DC-bias assessment and bench validation.')
meta['C13']['notes'] = 'Additional 3V3-to-GND bypass retained. U3 pin 5 is now SHDN/GND and must not connect to this capacitor\'s 3V3 terminal.'

def change_can_symbol(symbol, library_name):
    symbol[1] = library_name
    for prop in children(symbol, 'property'):
        if prop[1] == 'Value': prop[2] = 'TCAN3404DRQ1'
    for unit in children(symbol, 'symbol'):
        unit[1] = unit[1].replace('TCAN3403DRQ1', 'TCAN3404DRQ1')
        for pin in children(unit, 'pin'):
            if child(pin, 'number')[1] == '5':
                pin[1] = sx.Symbol('input')
                child(pin, 'name')[1] = 'SHDN'

def update_connector_filter(node):
    if not isinstance(node, list): return
    if node and str(node[0]) == 'property' and node[1] == 'ki_fp_filters':
        node[2] = node[2].replace('NorComp_182-009-113R531', 'NorComp_182-009-113R561')
    for item in node:
        update_connector_filter(item)

# Keep the cached schematic symbol and project-local library consistent.
lib = sx.load(open(OLD / 'Leaf.kicad_sym'))
symbol = next(q for q in children(lib, 'symbol') if q[1] == 'TCAN3403DRQ1')
change_can_symbol(symbol, 'TCAN3404DRQ1')
update_connector_filter(lib)
(H / 'Leaf.kicad_sym').write_text(sx.dumps(lib))
sch = sx.load(open(OLD / 'leaf-heat-v5.kicad_sch'))
symbol = next(q for q in children(child(sch, 'lib_symbols'), 'symbol')
              if q[1] == 'Leaf:TCAN3403DRQ1')
change_can_symbol(symbol, 'Leaf:TCAN3404DRQ1')
update_connector_filter(sch)
for inst in children(sch, 'symbol'):
    props = {q[1]: q for q in children(inst, 'property')}
    ref = props['Reference'][2]
    if ref in meta:
        part = meta[ref]
        for field, key in [('Value','value'), ('MPN','mpn'), ('Manufacturer','manufacturer'),
                           ('Footprint','footprint'), ('Datasheet','datasheet')]:
            if field in props: props[field][2] = part[key]
        if ref == 'U3': child(inst, 'lib_id')[1] = part['symbol']
    for project in children(child(inst, 'instances') or [], 'project'):
        project[1] = NAME
labels = [q for q in children(sch, 'label')
          if child(q, 'uuid')[1] == '52b04751-169e-5f96-a6b3-0b494e6b13af']
assert len(labels) == 1 and labels[0][1] == '3V3'
assert child(labels[0], 'at')[1:3] == [325.12, 182.88]
labels[0][1] = 'GND'
for t in children(sch, 'text'):
    t[1] = t[1].replace('REV E', 'REV F').replace('Rev E', 'Rev F')
    if t[1].startswith('CAN TX: GPIO4'):
        t[1] += '\nTCAN3404: SHDN pin 5 tied to GND. C13 remains an extra rail bypass.'
title = child(sch, 'title_block')
child(title, 'rev')[1] = 'F'
child(title, 'date')[1] = '2026-09-12'
(H / (NAME + '.kicad_sch')).write_text(sx.dumps(sch))

# NorComp options 53 and 56 share the manufacturer's plated-hole pattern;
# option 56 adds the female screwlock hardware forward of the mating face.
old_fp = H / 'Leaf.pretty/NorComp_182-009-113R531__Hand.kicad_mod'
fp = sx.load(open(old_fp))
fp[1] = 'NorComp_182-009-113R561__Hand'
child(fp, 'descr')[1] = ('NorComp 182-009-113R561, 9-pin male right-angle DB9; '
    '0.318 inch / 8.08 mm offset; 2.77 x 2.84 mm contacts; 24.99 mm fork-boardlock centres; '
    '3.2 mm anchor holes; fitted 4-40 female screwlocks. Manufacturer drawing 182-YYY-113RYY1 Rev 16.')
child(fp, 'tags')[1] = 'NorComp 182 009 113R561 DB9 male 4-40 screwlocks 8.08mm'
for prop in children(fp, 'property'):
    if prop[1] == 'Value': prop[2] = '182-009-113R561'
    if prop[1] == 'Datasheet': prop[2] = meta['J1']['datasheet']
(H / 'Leaf.pretty/NorComp_182-009-113R561__Hand.kicad_mod').write_text(sx.dumps(fp))
old_fp.unlink()

board = p.LoadBoard(str(OLD / 'leaf-heat-v5.kicad_pcb'))
fps = {f.GetReference(): f for f in board.GetFootprints()}
for ref, part in meta.items():
    f = fps[ref]
    f.SetValue(part['value'])
    for field, key in [('MPN','mpn'), ('Manufacturer','manufacturer'), ('Datasheet','datasheet')]:
        f.SetField(field, part[key])
fps['J1'].SetFPID(p.LIB_ID(*meta['J1']['footprint'].split(':', 1)))
fps['J1'].SetLibDescription(child(fp, 'descr')[1])
fps['J1'].SetKeywords(child(fp, 'tags')[1])
u3_pin5 = next(q for q in fps['U3'].Pads() if q.GetNumber() == '5')
assert u3_pin5.GetNetname() == '/3V3'
u3_pin5.SetNet(board.FindNet('/GND'))
u3_pin5.SetPinFunction('SHDN')
u3_pin5.SetPinType('input')

# Remove exactly the old three-segment C13-to-VIO branch. C13 keeps its own
# supply via. Reuse the existing pin-5 via and short trace for ground.
remove = {'243053fc-629b-45c1-bffd-34a2012ad1f7',
          '919d2525-9790-49f4-a8cd-d172c1a4fce9',
          'e4352eb1-c995-4b55-932a-45f484173721'}
ground = {'b0a7b973-c068-4f43-b110-33e82b02df7d',
          '07170d68-d4c3-413c-a34c-8b5e1a07d958'}
seen_remove, seen_ground = set(), set()
for t in list(board.GetTracks()):
    uid = t.m_Uuid.AsString()
    if uid in remove:
        assert t.GetNetname() == '/3V3' and not isinstance(t, p.PCB_VIA)
        board.RemoveNative(t)
        seen_remove.add(uid)
    if uid in ground:
        assert t.GetNetname() == '/3V3'
        t.SetNet(board.FindNet('/GND'))
        seen_ground.add(uid)
assert seen_remove == remove and seen_ground == ground
for item in board.GetDrawings():
    if isinstance(item, p.PCB_TEXT):
        item.SetText(item.GetText().replace('REV E','REV F').replace('TCAN3403DRQ1','TCAN3404DRQ1'))
board.GetTitleBlock().SetRevision('F')
board.GetTitleBlock().SetTitle('Leaf Heat - Mouser hand-solder prototype')
board.BuildConnectivity()
p.SaveBoard(str(H / (NAME + '.kicad_pcb')), board)
(H / 'parts.json').write_text(json.dumps(parts, indent=2) + '\n')
(OUT / 'intended-changes.json').write_text(json.dumps({
    'source_revision': 'E', 'revision': 'F',
    'changed_mpns': {ref: meta[ref]['mpn'] for ref in ['U3','J1','C5','C6','C7']},
    'changed_pin': {'ref':'U3','pin':'5','old_net':'3V3','new_net':'GND','function':'SHDN'},
    'removed_copper_uuids': sorted(remove), 'regrounded_copper_uuids': sorted(ground),
    'factory_refs': ['L1','U1','U2','U4'], 'hand_count': 37,
}, indent=2) + '\n')
assert all(sha(OLD / n) == digest for n, digest in baseline.items())
print('Rev F created: three sourcing groups changed; U3.5 grounded; source Rev E intact.')

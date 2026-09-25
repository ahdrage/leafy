"""Package only final, audited Rev F outputs and verify every ZIP member."""
from pathlib import Path
import csv
import hashlib
import io
import json
import zipfile
from decimal import Decimal

H = Path(__file__).resolve().parent
E = H / 'exports'
D = H / 'deliverables'
D.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
native = H / 'leaf-heat-v6.kicad_pcb'
audit = json.loads((E / 'independent-audit.json').read_text())
manufacturing = json.loads((E / 'manufacturing-audit.json').read_text())
assert sha(native) == audit['board_sha256'] == manufacturing['board_sha256']
assert sha(H / 'leaf-heat-v6.kicad_sch') == audit['schematic_sha256']
assert all(sha(E / 'fabrication' / n) == v for n, v in manufacturing['fabrication_files'].items())
assert all(c['pass'] for c in audit['checks'])
assert audit['factory_refs'] == ['L1', 'U1', 'U2', 'U4'] and audit['hand_count'] == 37
hand_rows = list(csv.DictReader((E / 'BOM-HAND.csv').open()))
shopping = list(csv.DictReader((E / 'MOUSER-HAND-TWO-BOARDS.csv').open()))
assert len(shopping) == 21 and sum(int(r['Quantity']) for r in shopping) == 74
assert {r['Manufacturer Part Number']: int(r['Quantity']) for r in shopping} == {
    r['MPN']: int(r['Qty for TWO boards']) for r in hand_rows}
verified_name = 'MOUSER-BASKET-VERIFIED-2026-09-12.csv'
verified = list(csv.DictReader((E / verified_name).open()))
assert len(verified) == len(shopping) == 21
assert {(r['Mouser Part Number'], r['Manufacturer Part Number'], int(r['Quantity'])) for r in verified} == {
    (r['Mouser Part Number'], r['Manufacturer Part Number'], int(r['Quantity'])) for r in shopping}
assert all(int(r['Dispatches Now']) == int(r['Quantity']) for r in verified)
assert sum(Decimal(r['Line Price NOK']) for r in verified) == Decimal('347.53')

records = {}
def package(name, files):
    contents = {str(arc): Path(src) for src, arc in files}
    assert len(contents) == len(files), name
    path = D / name
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arc, src in sorted(contents.items()):
            assert src.is_file(), src
            z.write(src, arc)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(contents)
        assert all(hashlib.sha256(z.read(a)).hexdigest() == sha(s) for a, s in contents.items())
    records[name] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'file_count': len(contents),
                     'contents': {a: sha(s) for a, s in sorted(contents.items())}}
    return path

fab = [(E / 'fabrication' / n, n) for n in sorted(manufacturing['fabrication_files'])]
assert sum(n.endswith('.drl') for _, n in fab) == 2
gerber = package('leaf-heat-rev-f-gerbers.zip', fab)
factory_names = ['BOM-FACTORY-PCBWay.csv', 'BOM-FACTORY-JLCPCB.csv',
                 'placements-FACTORY.csv', 'CPL-FACTORY-JLCPCB.csv']
factory = [(E / n, n) for n in factory_names] + [
    (H / 'MANUFACTURING-NOTES.md', 'MANUFACTURING-NOTES.md'), (gerber, gerber.name),
    (E / 'assembly-map.png', 'assembly-map.png'), (E / 'placement.svg', 'placement.svg'),
    (E / 'schematic.pdf', 'REFERENCE-ONLY-schematic.pdf'), (E / 'drill-report.txt', 'drill-report.txt')]
factory_zip = package('leaf-heat-rev-f-factory-assembly.zip', factory)
with zipfile.ZipFile(factory_zip) as z:
    assert not any('BOM-HAND' in n or 'FULL-REFERENCE' in n for n in z.namelist())
    for n, key in zip(factory_names, ['Designator', 'Designator', 'Ref', 'Designator']):
        rows = list(csv.DictReader(io.StringIO(z.read(n).decode())))
        assert len(rows) == 4 and {r[key] for r in rows} == set(audit['factory_refs'])

docs = ['README.md', 'DESIGN-REVIEW.md', 'HAND-ASSEMBLY.md', 'MANUFACTURING-NOTES.md',
        'PROGRAMMING.md', 'REVIEW-IMAGES.md', 'RECHECK-2026-09-12.md', 'VEHICLE-WIRING.md', 'MOUSER-SHOPPING.md']
images = ['board-3d.png', 'can-change.png', 'can-change.svg', 'assembly-map.png', 'assembly-map.svg',
          'placement.png', 'placement.svg', 'back-legend.png', 'back-legend.svg', 'top.png', 'top.svg',
          'ground.png', 'ground.svg', 'power.png', 'power.svg', 'bottom.png', 'bottom.svg',
          'factory-paste.png', 'factory-paste.svg', 'schematic.png']
shopping_files = ['MOUSER-HAND-TWO-BOARDS.csv', 'MOUSER-QUICK-ORDER-TWO-BOARDS.txt', verified_name]
review_exports = images + factory_names + shopping_files + ['BOM-HAND.csv', 'BOM-FULL-REFERENCE-ONLY.csv',
    'placements-FULL-REFERENCE-ONLY.csv', 'schematic.pdf', 'erc.json', 'drc-final.json',
    'independent-audit.json', 'manufacturing-audit.json', 'leaf-heat-v6.net.xml', 'drill-report.txt',
    'intended-changes.json', 'baseline-rev-e-sha256.json']
native_files = ['leaf-heat-v6.kicad_pro', 'leaf-heat-v6.kicad_sch', 'leaf-heat-v6.kicad_pcb',
    'leaf-heat-v6.kicad_dru', 'Leaf.kicad_sym', 'sym-lib-table', 'fp-lib-table', 'parts.json', 'testpoints.json']
source = [(H / n, 'leaf-heat-rev-f/' + n) for n in docs + native_files]
source += [(p, 'leaf-heat-rev-f/Leaf.pretty/' + p.name) for p in sorted((H / 'Leaf.pretty').glob('*.kicad_mod'))]
source += [(E / n, 'leaf-heat-rev-f/exports/' + n) for n in review_exports]
source += [(E / 'schematic/leaf-heat-v6.svg', 'leaf-heat-rev-f/exports/schematic/leaf-heat-v6.svg')]
source += [(p, 'leaf-heat-rev-f/exports/fabrication/' + n) for p, n in fab]
source += [(p, 'leaf-heat-rev-f/references/' + p.name) for p in sorted((H / 'references').glob('*.pdf'))]
package('leaf-heat-rev-f-kicad-review.zip', source)
hand = [(H / n, n) for n in docs if n != 'README.md']
hand += [(E / n, n) for n in shopping_files + ['BOM-HAND.csv', 'assembly-map.png', 'placement.png',
                                             'top.png', 'board-3d.png', 'schematic.pdf']]
package('leaf-heat-rev-f-hand-assembly.zip', hand)
review = [(E / n, n) for n in images] + [(H / n, n) for n in docs if n != 'README.md']
review += [(E / 'schematic.pdf', 'schematic.pdf')]
package('leaf-heat-rev-f-review-images.zip', review)
(D / 'manifest.json').write_text(json.dumps({'revision': 'F', 'date': '2026-09-12',
    'board_sha256': sha(native), 'schematic_sha256': sha(H / 'leaf-heat-v6.kicad_sch'),
    'packages': records}, indent=2) + '\n')
print(json.dumps({n: {k: v for k, v in r.items() if k != 'contents'} for n, r in records.items()}, indent=2))

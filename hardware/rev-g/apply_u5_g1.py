"""One-time, metadata-only Rev G.1 substitution; preserve the original release."""
from pathlib import Path
import datetime, hashlib, json, zipfile

H = Path(__file__).resolve().parent
archive = H / 'history' / 'rev-g-before-u5-g1.zip'
old, new = 'TPS3760A012DYYRQ1', 'TPS3760A012DYYR'
assert not archive.exists(), 'The migration has already been applied.'
archive.parent.mkdir(exist_ok=True)
files = [p for p in H.iterdir() if p.is_file()]
files += list((H/'Leaf.pretty').glob('*'))
files += list((H/'deliverables').glob('*'))
files += list((H/'exports').glob('*.*'))
files += list((H/'exports/fabrication').glob('*'))
files += list((H/'quotations/2026-09-13').glob('*'))
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        if p.is_file(): z.write(p, p.relative_to(H))
    assert z.testzip() is None

for name in ['leaf-heat-v7.kicad_pcb', 'leaf-heat-v7.kicad_sch', 'Leaf.kicad_sym',
             'build_rev_g.py', 'audit_rev_g.py', 'MANUFACTURING-NOTES.md', 'DESIGN-REVIEW.md']:
    p = H/name
    s = p.read_text()
    assert old in s, name
    p.write_text(s.replace(old, new).replace('tps3760-q1', 'tps3760').replace('TPS3760-Q1 datasheet', 'TPS3760 datasheet'))

p = H/'parts.json'
parts = json.loads(p.read_text())
u5 = next(q for q in parts if q['ref'] == 'U5')
assert u5['mpn'] == u5['value'] == old
u5['mpn'] = u5['value'] = new
u5['symbol'] = u5.get('symbol', '').replace(old, new) if 'symbol' in u5 else None
if u5['symbol'] is None: del u5['symbol']
u5['datasheet'] = 'https://www.ti.com/lit/ds/symlink/tps3760.pdf'
u5['notes'] += ' Rev G.1: Catalog grade, not AEC-Q100; 65 V operating maximum, no Q1 70 V/50 ms operating allowance. User-approved prototype substitution.'
p.write_text(json.dumps(parts, indent=2)+'\n')

# A distinct package name prevents accidental use of the superseded Q1 BOM.
for name in ['package_rev_g.py', 'deliverables-README.tmp']:
    p = H/name
    s = p.read_text().replace('leaf-heat-rev-g-', 'leaf-heat-rev-g1-')
    s = s.replace("'revision':'G'", "'revision':'G.1'").replace('# Rev G deliverables', '# Rev G.1 deliverables')
    p.write_text(s)
for p in (H/'deliverables').glob('*.zip'):
    p.unlink()  # Exact old ZIPs are retained inside the verified archive above.

for name in ['README.md', 'MOUSER-CART-BACKUP.md']:
    p = H.parents[1]/name
    s = p.read_text().replace('leaf-heat-rev-g-hand-assembly.zip', 'leaf-heat-rev-g1-hand-assembly.zip')
    p.write_text(s)
print('Archived original Rev G and applied U5 metadata changes for Rev G.1.')

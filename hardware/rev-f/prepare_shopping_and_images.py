"""Create Rev F purchasing files and a close view from the native PCB SVG."""
from pathlib import Path
import csv
import re
import cairosvg

H = Path(__file__).resolve().parent
E = H / 'exports'
M = {
    '182-009-113R561': '636-182-009-113R561',
    '0451001.MRL': '576-0451001.MRL',
    'B1100-13-F': '621-B1100-F',
    'SMBJ24CA': '576-SMBJ24CA',
    'GRM32ER72A225KA35L': '81-GRM32ER72A225KA35',
    'C1206C224K1RACTU': '80-C1206C224K1R',
    'C1206C105K3RACTU': '80-C1206C105K3R',
    'C1206C104K5RACTU': '80-C1206C104K5R',
    'C1210C226K3RAC7210': '80-C1210C226K3R7210',
    'RC1206FR-07100KL': '603-RC1206FR-07100KL',
    'RC1206FR-0743K2L': '603-RC1206FR-0743K2L',
    'RC1206FR-0710KL': '603-RC1206FR-0710KL',
    'C1206C106K4RACTU': '80-C1206C106K4R',
    'B3F-1000': '653-B3F-1000',
    'RC1206FR-071ML': '603-RC1206FR-071ML',
    'RC1206FR-0747KL': '603-RC1206FR-0747KL',
    'RC1206FR-071KL': '603-RC1206FR-071KL',
    'LTST-C150KGKT': '859-LTST-C150KGKT',
    'TCAN3404DRQ1': '595-TCAN3404DRQ1',
    'PESD2CAN,215': '771-PESD2CAN-T/R',
    'M20-9990346': '855-M20-9990346',
}
rows = list(csv.DictReader((E / 'BOM-HAND.csv').open()))
assert {r['MPN'] for r in rows} == set(M)
assert sum(int(r['Qty for TWO boards']) for r in rows) == 74
assert len(rows) == 21
with (E / 'MOUSER-HAND-TWO-BOARDS.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Mouser Part Number', 'Quantity', 'Customer Part Number', 'Manufacturer', 'Manufacturer Part Number'])
    for r in rows:
        w.writerow([M[r['MPN']], r['Qty for TWO boards'], 'RevF-' + r['References'], r['Manufacturer'], r['MPN']])
(E / 'MOUSER-QUICK-ORDER-TWO-BOARDS.txt').write_text(''.join(
    f"{M[r['MPN']]}|{r['Qty for TWO boards']}\n" for r in rows))

# This is a viewBox crop of the native CAD plot, with no reconstructed copper.
svg = (E / 'top.svg').read_text()
svg = re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
             'width="1500" height="1500" viewBox="13 57 32 32"', svg, count=1)
(E / 'can-change.svg').write_text(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to=str(E / 'can-change.png'),
                 output_width=1500, output_height=1500, background_color='white')
print('Mouser mapping verified: 21 lines, 74 parts; native CAN close-up generated.')

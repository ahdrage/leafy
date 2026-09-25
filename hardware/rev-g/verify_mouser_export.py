"""Check a downloaded Mouser XLS against both the shopping CSV and PCB BOM."""
from pathlib import Path
from decimal import Decimal
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import sys,json,csv,hashlib,shutil
import xlrd
H=Path(__file__).resolve().parent;E=H/'exports';source=Path(sys.argv[1])
expected={r['Mouser Part Number']:r for r in csv.DictReader((E/'MOUSER-TWO-BOARDS.csv').open())}
parts=json.loads((H/'parts.json').read_text())
counts=Counter(q['mpn'] for q in parts if q['assembly']=='HAND')
for a in json.loads((H/'accessories.json').read_text()):counts[a['mouser_ordering_mpn']]+=a['quantity_per_board']
assert {r['Manufacturer Part Number']:int(r['Quantity']) for r in expected.values()}=={k:v*2 for k,v in counts.items()}
s=xlrd.open_workbook(str(source)).sheet_by_index(0)
raw=[s.row_values(i) for i in range(9,s.nrows) if isinstance(s.cell_value(i,0),float)]
assert len(raw)==len(expected)==28
seen=set();rows=[];total=Decimal(0);qty=0
money=lambda value:Decimal(value.removeprefix('kr ').replace(',','.'))
for r in raw:
 sku=r[1];assert sku not in seen;seen.add(sku);e=expected[sku]
 assert r[2]==e['Manufacturer Part Number'],(sku,r[2])
 assert int(r[8])==int(e['Quantity']),(sku,r[8])
 assert not r[4].startswith('RevF'),(sku,r[4])
 qty+=int(r[8]);total+=money(r[10])
 rows.append({'Mouser Part Number':sku,'Manufacturer Part Number':r[2],'Quantity':int(r[8]),'PCB references':e['Customer Part Number'],'Manufacturer':r[3],'Description':r[5],'Supplier customer label':r[4],'Unit Price NOK':str(money(r[9])),'Line Total NOK':str(money(r[10])),'Supplier lifecycle flag':r[7] or 'Not stated in export'})
assert seen==set(expected) and qty==100 and total==Decimal('483.34')
# Availability is a separate direct observation of the final Chrome basket, not
# a column in Mouser's Excel file. Re-verify it in Chrome before rerunning later.
live={'observed_date':'2026-09-14','source':'Final Chrome Mouser basket accessibility snapshot','products':28,'pieces':100,'all_requested_quantities_dispatch_now':True,'duplicate_skus':0,'backorder_warning':False,'merchandise_NOK':'483.34','selected_delivery_NOK':'280.00','displayed_basket_subtotal_NOK':'763.34','checkout_taxes':'not calculated/verified','purchase_made':False}
for r in rows:r['Availability verified in Chrome']='Requested quantity dispatches now (2026-09-14)'
with (E/'MOUSER-BASKET-VERIFIED-2026-09-14.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dest=E/'MOUSER-ORIGINAL-EXPORT-2026-09-14.xls';shutil.copy2(source,dest)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'verified_at_oslo':datetime.now(ZoneInfo('Europe/Oslo')).isoformat(),'supplier_export_timestamp':s.cell_value(7,0),'scope':'Hand-fitted components plus plug-in antennas for two Rev G.3 boards, no spares','comparison':'All exact Mouser SKUs, manufacturer MPNs and quantities match the shopping list and parts.json','live_browser_observation':live,'lifecycle_flags':{r['Mouser Part Number']:r['Supplier lifecycle flag'] for r in rows if r['Supplier lifecycle flag']!='Not stated in export'},'factory_refs_excluded':sorted(q['ref'] for q in parts if q['assembly']=='FACTORY'),'pcb_sha256':sha(H/'leaf-heat-v7.kicad_pcb'),'files':{p.name:sha(p) for p in [dest,E/'MOUSER-BASKET-VERIFIED-2026-09-14.csv',E/'MOUSER-TWO-BOARDS.csv',H/'parts.json']}}
(E/'MOUSER-CART-VERIFICATION-2026-09-14.json').write_text(json.dumps(report,indent=2)+'\n')
print('VERIFIED: 28 products / 100 pieces / NOK 483.34. Exact SKUs, MPNs and quantities match both sources.')
print('Lifecycle flags:',report['lifecycle_flags'])

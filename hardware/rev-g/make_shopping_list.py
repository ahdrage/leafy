from pathlib import Path
import json,csv,collections
H=Path(__file__).resolve().parent;E=H/'exports'
old=list(csv.DictReader((H.parent/'rev-f/exports/MOUSER-HAND-TWO-BOARDS.csv').open()))
ids={q['Manufacturer Part Number']:q['Mouser Part Number'] for q in old}
ids.update({'EEU-FR1J470H':'667-EEU-FR1J470H','CRCW25121R00FKEGHP':'71-CRCW25121R00FKEGH','RT1206BRD07680KL':'603-RT1206BRD07680KL','RT1206BRD0747KL':'603-RT1206BRD0747KL','RC1206FR-0710ML':'603-RC1206FR-0710ML','RC1206FR-07470KL':'603-RC1206FR-07470KL','PTS645SL43-2 LFS':'611-PTS645SL432'})
g=collections.defaultdict(list)
for q in json.loads((H/'parts.json').read_text()):
 if q['assembly']=='HAND':g[q['mpn']].append(q)
rows=[]
for mpn,qs in g.items():rows.append({'Mouser Part Number':ids[mpn],'Quantity':2*len(qs),'Customer Part Number':'RevG-'+','.join(q['ref'] for q in qs),'Manufacturer':qs[0]['manufacturer'],'Manufacturer Part Number':mpn})
assert len(rows)==27 and sum(q['Quantity'] for q in rows)==98
with (E/'MOUSER-HAND-TWO-BOARDS.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
accessories=json.loads((H/'accessories.json').read_text())
for a in accessories:
 rows.append({'Mouser Part Number':a['mouser_mpn'],'Quantity':2*a['quantity_per_board'],'Customer Part Number':'RevG3-'+a['ref'],'Manufacturer':a['manufacturer'],'Manufacturer Part Number':a['mouser_ordering_mpn']})
assert len(rows)==28 and sum(q['Quantity'] for q in rows)==100
with (E/'MOUSER-TWO-BOARDS.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (E/'BOM-ACCESSORIES.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Manufacturer','MPN','Mouser Part Number','Quantity per board','Quantity two boards','Assembly'])
 for a in accessories:w.writerow([a['ref'],a['manufacturer'],a['mpn'],a['mouser_mpn'],a['quantity_per_board'],2*a['quantity_per_board'],a['assembly']])
(E/'MOUSER-QUICK-ORDER-TWO-BOARDS.txt').write_text('\n'.join(q['Mouser Part Number']+'|'+str(q['Quantity']) for q in rows)+'\n')
oldmap={q['Mouser Part Number']:int(q['Quantity']) for q in old};changes=[]
for q in rows:
 qty=oldmap.pop(q['Mouser Part Number'],0)
 if qty!=q['Quantity']:changes.append({'Mouser Part Number':q['Mouser Part Number'],'Rev F quantity':qty,'Rev G target quantity':q['Quantity'],'Action':'change quantity' if qty else 'add'})
for mpn,qty in oldmap.items():changes.append({'Mouser Part Number':mpn,'Rev F quantity':qty,'Rev G target quantity':0,'Action':'remove'})
with (E/'MOUSER-CART-CHANGES.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(changes[0]));w.writeheader();w.writerows(changes)
print('28 products / 100 pieces: 98 hand-solder parts plus two plug-in antennas')

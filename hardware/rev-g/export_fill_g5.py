"""Explicit thermal-hole scope for fabrication; no PCB edits."""
from pathlib import Path
import csv, json
import sexpdata as sx
import cairosvg
H=Path(__file__).resolve().parent; E=H/'exports'; F=E/'fabrication'
def key(q):return str(q[0]) if isinstance(q,list) and q else ''
def items(q,k):return [v for v in q if key(v)==k]
def child(q,k):return next(v for v in q if key(v)==k)
def prop(q,k):return next(v[2] for v in items(q,'property') if v[1]==k)
b=sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text());fps={prop(f,'Reference'):f for f in items(b,'footprint')}
rows=[]
for ref,ep in [('U1','9'),('U2','19')]:
 f=fps[ref];fx,fy=child(f,'at')[1:3]
 holes=[q for q in items(f,'pad') if q[1]==ep and q[2]==sx.Symbol('thru_hole')]
 for i,q in enumerate(sorted(holes,key=lambda v:child(v,'at')[1:3]),1):
  x,y=child(q,'at')[1:3];d=child(q,'drill')[1]
  rows.append({'Reference':ref,'Hole':i,'X mm':f'{fx+x:.6f}','Y mm':f'{100-fy-y:.6f}','Drill mm':f'{d:.2f}','Treatment':'Epoxy filled, planarized and copper capped'})
assert len(rows)==18
for dest in [E/'THERMAL-FILL-LOCATIONS.csv',F/'THERMAL-FILL-LOCATIONS.csv']:
 with dest.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120">',
'<rect width="1800" height="1120" fill="#f7f9fc"/>',
'<g font-family="Arial" fill="#112d37">',
'<text x="60" y="65" font-size="38" font-weight="bold">Leafy G.5 — required thermal-hole filling</text>',
'<text x="60" y="108" font-size="23">18 thermal PTHs per PCB: epoxy fill, planarize and copper cap BOTH ends.</text>',
'<text x="60" y="145" font-size="22">Include U1’s 0.33 mm holes explicitly. Top faces must be flat and solderable.</text>',
'<rect x="70" y="225" width="650" height="650" fill="#116048" stroke="#163329" stroke-width="3"/>',
'<text x="90" y="263" font-size="26" fill="white">Leafy / REV G.5</text>']
for ref,(cx,cy,w,hh) in {'U1':(24,19,6,5.6),'U2':(73,8,19,20)}.items():
 # Location outline is illustrative, drill dots and CSV are actual coordinates.
 svg.append(f'<rect x="{70+(cx-w/2)*6.5}" y="{225+(cy-hh/2)*6.5}" width="{w*6.5}" height="{hh*6.5}" fill="#334155" stroke="white"/>')
 svg.append(f'<text x="{70+cx*6.5}" y="{225+(cy+hh/2)*6.5+28}" text-anchor="middle" fill="white" font-size="21">{ref}</text>')
for q in rows:
 x=float(q['X mm']);y=100-float(q['Y mm'])
 svg.append(f'<circle cx="{70+x*6.5}" cy="{225+y*6.5}" r="2" fill="#ffd36a"/>')
svg.extend(['<text x="70" y="921" font-size="21">Finished board: 100 × 100 mm, top view</text>',
'<text x="70" y="958" font-size="20">CSV origin: lower-left; X right, Y up; millimetres.</text>'])
for i,(ref,cx,cy,w,hh,count,d) in enumerate([('U1',24,81,2.71,3.4,6,.33),('U2',73.96,91.8,2.7,2.7,12,.30)]):
 ox=1070;oy=410+380*i;scale=70
 svg.append(f'<text x="850" y="{oy-165}" font-size="28" font-weight="bold">{ref}: {count} × {d:.2f} mm</text>')
 svg.append(f'<rect x="{ox-w*scale/2}" y="{oy-hh*scale/2}" width="{w*scale}" height="{hh*scale}" fill="#edc66b" stroke="#9c7221" stroke-width="2"/>')
 for q in [q for q in rows if q['Reference']==ref]:
  x=ox+(float(q['X mm'])-cx)*scale;y=oy-(float(q['Y mm'])-cy)*scale
  svg.append(f'<circle cx="{x}" cy="{y}" r="{d*scale/2}" fill="#b7832c" stroke="#493510" stroke-width="2"/>')
 svg.append(f'<text x="1240" y="{oy-35}" font-size="21">Continuous top mask opening</text>')
 svg.append(f'<text x="1240" y="{oy+5}" font-size="21">{w:.2f} × {hh:.2f} mm</text>')
 svg.append(f'<text x="1240" y="{oy+45}" font-size="21">Circles locate required copper caps.</text>')
svg += ['<text x="70" y="1030" font-size="22">No mask tents. Bottom mask openings expose CAPS, not open barrels. Keep thermal connections solid.</text>',
'<text x="70" y="1070" font-size="21">Component-lead, connector, test and mounting holes remain open. No special stencil requested.</text>','</g></svg>']
(E/'thermal-fill-map.svg').write_text('\n'.join(svg))
cairosvg.svg2png(url=str(E/'thermal-fill-map.svg'),write_to=str(E/'thermal-fill-map.png'))
(F/'THERMAL-FILL-MAP.png').write_bytes((E/'thermal-fill-map.png').read_bytes())
print('Exported 18-hole fill/cap CSV and annotated fabrication map.')

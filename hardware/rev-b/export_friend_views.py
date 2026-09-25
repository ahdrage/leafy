"""Render labeled review views directly from the native KiCad vector exports."""
from pathlib import Path
import xml.etree.ElementTree as ET, html,zipfile
import cairosvg
H=Path(__file__).resolve().parent;E=H/'exports';OUT=H.parent.parent/'deliverables/rev-b-screenshots';OUT.mkdir(exist_ok=True)
ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
def view(src,name,title,subtitle,crop=None,width=1700):
 root=ET.parse(src).getroot(); vb=list(map(float,root.attrib['viewBox'].split()))
 box=list(crop) if crop else vb
 height=round(width*box[3]/box[2]);header=140;footer=75
 inner=ET.tostring(root,encoding='unicode')
 # Nested SVG uses the original CAD vectors without changing copper geometry.
 r=ET.fromstring(inner);r.set('x','0');r.set('y',str(header));r.set('width',str(width));r.set('height',str(height));r.set('viewBox',' '.join(map(str,box)))
 drawing=ET.tostring(r,encoding='unicode')
 full=f'''<svg xmlns="{ns}" width="{width}" height="{height+header+footer}" viewBox="0 0 {width} {height+header+footer}">
<rect width="100%" height="100%" fill="#111827"/>
<text x="36" y="52" font-family="Arial,sans-serif" font-size="32" font-weight="bold" fill="white">{html.escape(title)}</text>
<text x="36" y="94" font-family="Arial,sans-serif" font-size="22" fill="#cad5e4">{html.escape(subtitle)}</text>
{drawing}
<text x="36" y="{height+header+45}" font-family="Arial,sans-serif" font-size="19" fill="#cad5e4">REV B | Native KiCad export | Engineering prototype — not yet physically tested</text>
</svg>'''
 (OUT/(name+'.svg')).write_text(full)
 cairosvg.svg2png(bytestring=full.encode(),write_to=str(OUT/(name+'.png')))
 print(name, width,height+header+footer)
view(E/'placement.svg','01-component-placement','1. Component placement','Top assembly drawing | 65 x 50 mm | 47 populated components')
view(E/'top.svg','02-top-copper','2. Top copper — F.Cu','Components, signals and local power routing; copper fills shown')
view(E/'ground.svg','03-ground-plane','3. Dedicated ground plane — In1.Cu','GND reference | No routed tracks | Openings around non-ground vias and holes')
view(E/'power.svg','04-power-plane','4. Internal power distribution — In2.Cu','Upper/central enclosed island: 3.3 V | Surrounding copper: GND | No tracks')
view(E/'bottom.svg','05-bottom-copper','5. Bottom copper — B.Cu','Supply areas, GND, limited control routing and USB-C contact bridges')
view(E/'top.svg','06-usb-route','6. USB routing — top layer','0.25 mm main traces / 0.15 mm gap | Matched main copper paths: approx. 40.991 mm',crop=(45,7,20,42),width=1150)
view(E/'top.svg','07-usb-connector','7. USB-C connector and ESD protection','Top view | Four local data vias bridge the duplicated USB-C contacts',crop=(45.5,33.5,18.5,16.3))
view(E/'bottom.svg','08-usb-bridges-bottom','8. USB-C contact bridges — bottom layer','Same viewing direction as top view; the bottom view is not mirrored',crop=(45.5,33.5,18.5,16.3))
view(E/'top.svg','09-regulator-layout','9. Regulator layout — top copper','U1 with input bypass C2, VCC capacitor C3, bootstrap C4 and feedback R1/R2',crop=(8,.8,26.5,18.6))
view(E/'schematic/leaf-heat-v2.svg','10-schematic','10. Complete circuit schematic','Rev B circuit | USB net names identify differential pairs',width=3400)
(OUT/'README.txt').write_text('Leaf Heat Rev B — images for review\n\nThese images are rendered from the checked KiCad files; they are CAD exports, not photographs or fabricated UI screenshots. The board is an untested engineering prototype.\n\n01: placement\n02: top copper\n03: dedicated GND plane\n04: internal power/GND\n05: bottom copper\n06: USB route\n07: USB-C and protection, top\n08: USB-C local bridges, bottom (not mirrored)\n09: regulator placement/routing\n10: schematic\n\nThe 90 ohm USB impedance target still requires manufacturer stackup confirmation. No order has been placed for Rev B.\n')
with zipfile.ZipFile(OUT.parent/'leaf-heat-rev-b-screenshots.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(OUT.iterdir()):
  if p.suffix in ['.png','.txt']:z.write(p,p.name)
print('Shareable PNG ZIP saved.')

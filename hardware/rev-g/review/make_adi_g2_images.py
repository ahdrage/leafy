"""Actual KiCad vector exports with matched before/after crops for Adi."""
from pathlib import Path
import copy, hashlib, json, math, shutil, zipfile
import xml.etree.ElementTree as ET
import cairosvg

H=Path(__file__).resolve().parents[1]; E=H/'exports'
O=H/'review/adi-g2-2026-09-14'; S=O/'source';S.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(H/'history/rev-g1-before-adi-g2.zip') as z:
    for n in ['top','bottom','back-legend']:
        (S/f'before-{n}.svg').write_bytes(z.read(f'exports/{n}.svg'))
for n in ['top','bottom','ground','power','back-legend']:
    shutil.copy2(E/f'{n}.svg',S/f'after-{n}.svg')
rows=[]
def page(name,title,subtitle,panels,cols=2):
    width=2400; pad=42; gap=36; header=154; cellw=(width-2*pad-(cols-1)*gap)/cols
    ratio=max(view[3]/view[2] for _,_,view in panels)
    cellh=cellw*ratio+58; count=math.ceil(len(panels)/cols); height=round(header+count*cellh+(count-1)*gap+80)
    root=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','width':str(width),'height':str(height),'viewBox':f'0 0 {width} {height}'})
    ET.SubElement(root,'rect',{'width':'100%','height':'100%','fill':'#f8fafc'})
    def text(x,y,size,value,color='#0f172a',weight='normal'):
        t=ET.SubElement(root,'text',{'x':str(x),'y':str(y),'font-family':'Arial, sans-serif','font-size':str(size),'fill':color,'font-weight':weight});t.text=value
    text(pad,57,38,title,weight='bold');text(pad,106,25,subtitle,'#475569')
    for i,(src,label,view) in enumerate(panels):
        x=pad+(i%cols)*(cellw+gap); y=header+(i//cols)*(cellh+gap)
        text(x,y+28,28,label,weight='bold')
        inner=ET.SubElement(root,'svg',{'x':str(x),'y':str(y+50),'width':str(cellw),'height':str(cellh-58),'viewBox':' '.join(map(str,view)),'overflow':'hidden'})
        ET.SubElement(inner,'rect',{'x':str(view[0]),'y':str(view[1]),'width':str(view[2]),'height':str(view[3]),'fill':'#f8fafc'})
        for item in ET.parse(src).getroot():inner.append(copy.deepcopy(item))
    text(pad,height-25,22,'14.09.2026 · Faktiske KiCad-lag, sett ovenfra · Statisk kontroll; fysisk prototype er ikke testet','#475569')
    data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    (O/f'{name}.svg').write_bytes(data);cairosvg.svg2png(bytestring=data,write_to=str(O/f'{name}.png'))
    rows.append({'file':f'{name}.png','title':title,'panels':[{'source':str(src.relative_to(H)),'label':label,'view':view} for src,label,view in panels]})
    print(name,flush=True)
def before_after(name,title,subtitle,view,both=False):
    panels=[(S/'before-top.svg','FØR — G.1, topplag',view),(S/'after-top.svg','ETTER — G.2, topplag',view)]
    if both:panels += [(S/'before-bottom.svg','FØR — G.1, bunnlag sett ovenfra',view),(S/'after-bottom.svg','ETTER — G.2, bunnlag sett ovenfra',view)]
    page(name,title,subtitle,panels)
page('01-hele-kortet','LEAF HEAT — REV G.2','100 × 100 mm · Samme komponenter og plasseringer · Rødt = toppkobber, gult = silketrykk',[(S/'after-top.svg','Topplag og komponentreferanser',[-.5,-.5,101,101])],1)
before_after('02-c10-for-etter','C10 / U2 — enklere 3,3 V-føring','Den doble trekantføringen er fjernet. Forsyningen går via C10 til U2 pinne 1.',[57,-.5,12,13])
before_after('03-r19-for-etter','R19 — UART_RX-via flyttet','Avstand til nabobanen PROG_TX: 0,202 → 2,499 mm. Begge kobberlag er kontrollert.',[83,49,12,11],True)
before_after('04-d4-for-etter','D4 — CAN_H-via flyttet','Avstand til D4-jordpad: 0,241 → 2,006 mm. Via ligger fortsatt direkte på CAN_H-banen.',[16,76,15,13],True)
before_after('05-u1-c2-for-etter','U1 / C2 — forbindelsen var riktig','BUCK_EN kobler via til U1 pinne 3 og fortsetter på bunnlaget. Kobberet er uendret; tekst er flyttet.',[12.5,13,22,19],True)
page('06-bakside-loddeoversikt','Bakside — større og lesbart silketrykk','Alle tekster er minst 1,0 mm høye; strekbredde minst 0,15 mm. 27 håndloddede varetyper.',[(S/'after-back-legend.svg','Bakside sett direkte fra undersiden',[-.5,-.5,101,101])],1)
page('07-indre-kobberlag','Indre lag — jord og strøm','Planenes definisjoner og antenne-klaring er uendret. Kobberfyll er oppdatert rundt flyttede vias.',[(S/'after-ground.svg','In1.Cu — jordplan',[-.5,-.5,101,101]),(S/'after-power.svg','In2.Cu — strømplan',[-.5,-.5,101,101])])
shutil.copy2(E/'schematic.pdf',O/'08-fullstendig-skjema.pdf')
(O/'LES-MEG.txt').write_text('''REV G.2 — BILDER TIL ADI, 14.09.2026

01: Hele kortet. 02: C10 før/etter. 03: R19 før/etter på begge lag.
04: D4 før/etter på begge lag. 05: U1/C2, uendret enable-forbindelse.
06: Større bakside-silketrykk. 07: Jord-/strømplan. 08: Fullstendig skjema.

Rødt = toppkobber inklusive jordfyll. Gult = silketrykk. Hvitt = klaringer.
Bunnkobber i sammenligningene sees ovenfra gjennom kortet. Bakside-teksten
i bilde 06 sees derimot direkte fra undersiden for å kunne leses.

Alle komponenter, pads, footprint-plasseringer, BOM, fabrikk-CPL og mål er
uendret. C10-føring ryddet, R19- og D4-via flyttet, silketrykk forbedret.
Fersk ERC/DRC med kobberfyll og 0,15 mm silkeklaring: null avvik, manglende
forbindelser eller skjemamismatch. Fabrikken monterer U1/U2/U4/U5/U6/L1.

Bruk G.2-produksjonsfiler; G.1-nettbutikktilbudet har eldre Gerber-/boredata.
Produsentens eksponert-pad-prosess og fysisk strøm-/Wi-Fi-/biltest gjenstår.
''')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
manifest={'revision':'G.2','pcb_sha256':sha(H/'leaf-heat-v7.kicad_pcb'),'schematic_sha256':sha(H/'leaf-heat-v7.kicad_sch'),'images':rows,
          'files':{f.name:sha(f) for f in O.iterdir() if f.is_file() and f.name!='manifest.json'}}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
with zipfile.ZipFile(O.parent/'leaf-heat-rev-g2-bilder-til-adi.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(O.iterdir()):
        if f.suffix in {'.png','.pdf','.txt','.json'}:z.write(f,f.name)

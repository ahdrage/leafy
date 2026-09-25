"""Read-only CAD plotting for Adi; outputs isolated from ordering packages."""
from pathlib import Path
import os, subprocess, hashlib, json, copy, html, shutil, zipfile
import xml.etree.ElementTree as ET
import cairosvg
H=Path(__file__).resolve().parents[1]
O=H/'review/adi-g1-2026-09-13'; S=O/'source'; S.mkdir(parents=True,exist_ok=True)
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
B=H/'leaf-heat-v7.kicad_pcb';SCH=H/'leaf-heat-v7.kicad_sch'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p.relative_to(H)):sha(p) for p in [B,SCH,*sorted((H/'deliverables').glob('*'))] if p.is_file()}
env=dict(os.environ,FONTCONFIG_FILE=str(H.parent/'fontconfig.xml'))
def run(*args):
 p=subprocess.run([K,*map(str,args)],env=env,text=True,capture_output=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
for name,layers in [('top','F.Cu,F.Silkscreen,Edge.Cuts'),('ground','In1.Cu,Edge.Cuts'),('power','In2.Cu,Edge.Cuts'),('bottom','B.Cu,Edge.Cuts'),('factory-paste','F.Paste,Edge.Cuts')]:
 run('pcb','export','svg','--layers',layers,'--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-o',S/(name+'.svg'),B)
run('sch','export','svg','-o',S,SCH)
shutil.copy2(H/'exports/schematic.pdf',O/'13-fullstendig-skjema.pdf')
rows=[]
def panel(src,name,title,subtitle,view=None,width=2400):
 root=ET.parse(src).getroot(); vb=view or [float(x) for x in root.get('viewBox').split()]
 x,y,w,h=vb;head=w*.087;foot=w*.045;pad=w*.025
 out=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','width':str(width),'height':str(round(width*(h+head+foot+2*pad)/(w+2*pad))),'viewBox':f'0 0 {w+2*pad} {h+head+foot+2*pad}'})
 ET.SubElement(out,'rect',{'x':'0','y':'0','width':'100%','height':'100%','fill':'#f8fafc'})
 def text(tx,ty,size,value,color='#0f172a',weight='normal'):
  el=ET.SubElement(out,'text',{'x':str(tx),'y':str(ty),'font-family':'Arial, sans-serif','font-size':str(size),'fill':color,'font-weight':weight});el.text=value
 text(pad,pad+w*.024,w*.023,title,weight='bold')
 text(pad,pad+w*.055,w*.0125,subtitle,'#475569')
 inner=ET.SubElement(out,'svg',{'x':str(pad),'y':str(pad+head),'width':str(w),'height':str(h),'viewBox':' '.join(map(str,vb)),'overflow':'hidden'})
 ET.SubElement(inner,'rect',{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'fill':'#f8fafc'})
 for child in root:inner.append(copy.deepcopy(child))
 text(pad,pad+head+h+w*.030,w*.011,'Rev G.1 · KiCad CAD-eksport · 13.09.2026 · Prototype, ikke fysisk validert','#475569')
 data=ET.tostring(out,encoding='utf-8',xml_declaration=True)
 (O/(name+'.svg')).write_bytes(data)
 cairosvg.svg2png(bytestring=data,write_to=str(O/(name+'.png')),output_width=width)
 rows.append({'file':name+'.png','title':title,'description':subtitle,'source':str(src.relative_to(H)),'source_sha256':sha(src),'viewBox':vb})
 print(name,flush=True)
panel(H/'exports/assembly-map.svg','01-komponentoversikt','Komponentoversikt / fabrikk og håndlodding','100 × 100 mm · Oransje: U1, U2, U4, U5, U6 og L1. Øvrige 49 komponenter håndloddes.')
panel(S/'top.svg','02-topplag','Topplag — F.Cu + silketrykk','Rødt viser kobber. Hvit bakgrunn viser klaringer. Silketrykk er gult. Sett ovenfra.')
panel(S/'ground.svg','03-jordplan','Jordplan — In1.Cu','Det indre jordlaget. Grønt viser kobber; klaringer og gjennomføringer er synlige. Sett ovenfra.')
panel(S/'power.svg','04-stromplan','Strømplan — In2.Cu','Indre kobberlag for strømfordeling. Geometrien er identisk med produksjonsunderlaget. Sett ovenfra.')
panel(S/'bottom.svg','05-bunnlag','Bunnlag — B.Cu','Bunnkobber vist ovenfra gjennom kortet; bildet er ikke speilvendt.')
panel(S/'top.svg','06-regulator-og-u5-layout','Nærbilde — regulator, inngangsdemping og U5','F.Cu + silketrykk. U1/L1, C1–C7, R21/C15 og batteribeskyttelsen rundt U5.',view=[4,5,43,50],width=2600)
panel(S/'leaf-heat-v7.svg','07-stromforsyning-skjema','Skjema — kjøretøyinngang og 3,3 V','J1 → F1 → D1 → VPWR. D3-transientvern og U1/L1-regulator; BUCK_EN styres av U5.',view=[15,24,242,116],width=3000)
panel(S/'leaf-heat-v7.svg','08-batteribeskyttelse-skjema','Skjema — inngangsdemping og batteribeskyttelse','U5: TPS3760A012DYYR. R21/C15 demper inngangen; U6 isolerer ADC-signalet når strømmen er av.',view=[15,266,298,124],width=3200)
panel(S/'leaf-heat-v7.svg','09-can-og-uart-skjema','Skjema — CAN og UART','CAN uten ekstra terminering. UART har ESD-beskyttelse; programmeringskontakten har ingen strømpinne.',view=[15,139,390,108],width=3600)
panel(S/'factory-paste.svg','10-fabrikk-loddepasta','Loddepasta — kun de seks fabrikkmonterte komponentene','Grått = F.Paste. Svart = borehull, ikke pasta. U1/U2: prosess for ufylt termisk hull må avklares med JLCPCB.')
panel(S/'leaf-heat-v7.svg','11-fullstendig-skjema','Fullstendig skjema — Rev G.1','U5 er oppdatert til TPS3760A012DYYR. Fabrikkmontering: U1/U2/U4/U5/U6/L1.',width=6000)
panel(S/'leaf-heat-v7.svg','12-wifi-og-batterimaling','Skjema — Wi-Fi, knapper og batterimåling','ESP32-C3 med RESET/BOOT. BAT_DIV går via U6 til ADC; spenningsmåling skjer etter D1.',view=[250,17,158,129],width=2800)
assert before=={name:sha(H/name) for name in before},'CAD or ordering package changed'
manifest={'revision':'G.1','pcb_sha256':sha(B),'schematic_sha256':sha(SCH),'ordering_packages_unchanged':True,'images':rows,'file_hashes':{p.name:sha(p) for p in O.iterdir() if p.is_file() and p.name not in {'manifest.json','LES-MEG.txt'}}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
(O/'LES-MEG.txt').write_text('''BILDER TIL ADI — REV G.1, 13.09.2026

Bildene er tekniske KiCad-eksporter fra gjeldende kort og skjema, ikke genererte illustrasjoner. Ingen CAD- eller bestillingsfiler er endret.

01: Komponentoversikt; oransje = fabrikkmontert.
02–05: F.Cu, In1.Cu (GND), In2.Cu og B.Cu. Alle sett ovenfra.
06: Nærbilde av regulator, inngangsdemping og U5.
07–09: Lesbare utsnitt av strømforsyning, beskyttelse, CAN og UART.
10: Fabrikkens loddepastaområder.
11/13: Fullstendig skjema som PNG/PDF.
12: Wi-Fi, knapper og batterimåling.

Silketrykk og eldre statisk skjematittel sier Rev G; gjeldende BOM er G.1. Den statiske teksten øverst i skjemaet nevner den tidligere fabrikklisten på fire komponenter. Korrekt nåværende liste er U1/U2/U4/U5/U6/L1, også angitt nederst i skjemaet og i bildetekstene.

U5 er byttet til TPS3760A012DYYR / JLCPCB C5218894. Pinout, kobber og plassering er uendret. Den er ikke AEC-Q100-kvalifisert og har 65 V maksimal driftsspenning, uten Q1-versjonens ekstra 70 V / 50 ms driftsområde.

JLCPCB-CPL har allerede korrigerte katalogvinkler: L1 0, U1 270, U2 0, U4 0, U5 270, U6 270 grader. Disse må ikke korrigeres to ganger. Sjekk mot pinne 1 og produksjonsgodkjenningen.

Fortsatt å avklare: U1/U2 eksponerte puter og ufylt termisk hull, sjablong/pasta, tinnsuging og inspeksjon hos produsent. Fysiske strøm-, transient-, Wi-Fi- og kjøretøytester gjenstår. Lav batterispenning vil slå av kortet, også Wi-Fi. Det er ingen planlagt periodisk Wi-Fi-frakobling.
''')
zip_path=O.parent/'leaf-heat-rev-g1-bilder-til-adi.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(O.iterdir()):
  if p.suffix in {'.png','.pdf','.txt','.json'}:z.write(p,p.name)
print('Saved',zip_path)

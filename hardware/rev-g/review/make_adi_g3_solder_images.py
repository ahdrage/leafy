"""Render the unchanged G.3 KiCad layers and explain its open thermal holes."""
from pathlib import Path
import copy
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

import cairosvg
import pcbnew as p

H = Path(__file__).resolve().parents[1]
O = H / 'review/adi-g3-lodding-2026-09-14'
S = O / 'source'
board_path = H / 'leaf-heat-v7.kicad_pcb'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
before = sha(board_path)
board = p.LoadBoard(str(board_path))
fps = {f.GetReference(): f for f in board.GetFootprints()}
ns = 'http://www.w3.org/2000/svg'
ET.register_namespace('', ns)


def element(parent, name, **attrs):
    return ET.SubElement(parent, f'{{{ns}}}{name}', {k.replace('_', '-'): str(v) for k, v in attrs.items()})


def text(root, x, y, value, size=28, color='#334155', bold=False):
    node = element(root, 'text', x=x, y=y, font_family='Arial, sans-serif', font_size=size,
                   fill=color, font_weight='bold' if bold else 'normal')
    node.text = value


def page(height, title, subtitle):
    root = ET.Element(f'{{{ns}}}svg', {'width': '2000', 'height': str(height), 'viewBox': f'0 0 2000 {height}'})
    element(root, 'rect', width=2000, height=height, fill='#f8fafc')
    text(root, 50, 66, title, 43, '#0f172a', True)
    text(root, 50, 118, subtitle, 27)
    text(root, 50, height-30, 'Rev G.3 · 14.09.2026 · Eksportert fra gjeldende KiCad-fil · Ingen endring i kortdesignet', 23)
    return root


def panel(root, src, x, y, width, height, view):
    element(root, 'rect', x=x, y=y, width=width, height=height, fill='white', stroke='#cbd5e1', stroke_width=2)
    inner = element(root, 'svg', x=x, y=y, width=width, height=height,
                    viewBox=' '.join(map(str, view)), overflow='hidden')
    for item in ET.parse(src).getroot():
        inner.append(copy.deepcopy(item))
    return inner


def save(root, name):
    data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    (O / f'{name}.svg').write_bytes(data)
    cairosvg.svg2png(bytestring=data, write_to=str(O / f'{name}.png'))


def geometry(ref, pad_number):
    pads = list(fps[ref].Pads())
    holes = [d for d in pads if d.GetNumber() == pad_number and d.GetAttribute() == p.PAD_ATTRIB_PTH]
    copper = [d for d in pads if d.GetNumber() == pad_number and d.GetAttribute() == p.PAD_ATTRIB_SMD and p.F_Cu in d.GetLayerSet().Seq()][0]
    return copper, holes


u1, h1 = geometry('U1', '9')
u2, h2 = geometry('U2', '19')
assert len(h1) == 6 and len(h2) == 12
assert all(abs(p.ToMM(d.GetDrillSize().x)-0.33) < 1e-6 for d in h1)
assert all(abs(p.ToMM(d.GetDrillSize().x)-0.30) < 1e-6 for d in h2)


def copper_outline(root, pad, color='#2563eb'):
    x, y = p.ToMM(pad.GetPosition().x), p.ToMM(pad.GetPosition().y)
    w, h = p.ToMM(pad.GetSize().x), p.ToMM(pad.GetSize().y)
    element(root, 'rect', x=x-w/2, y=y-h/2, width=w, height=h, fill='none',
            stroke=color, stroke_width=.035, stroke_dasharray='.12 .09')


root = page(2190, 'LEAF HEAT — gjeldende kort, Rev G.3',
            '100 × 100 mm · Fire kobberlag · U1 og U2 er markert med blå rammer')
overview = panel(root, S/'top.svg', 70, 155, 1860, 1860, [-.6, -.6, 101.2, 101.2])
for x,y,w,h in [(19,14,10,10), (61.5,.1,25,17)]:
    element(overview, 'rect', x=x, y=y, width=w, height=h, fill='none', stroke='#38bdf8', stroke_width=.28)
text(root, 70, 2059, 'Rødt = toppkobber med jordfyll · Hvitt = kobberklaringer/borehull · Gult = silketrykk', 27)
text(root, 70, 2103, 'Blå rammer er forklaringsmarkeringer. Nærbildene viser skjulte loddeområder under komponentene.', 26)
save(root, '01-hele-kortet-g3')


def detail(ref, pad, holes, left_view, right_view, title, subtitle, caption, note):
    root = page(1200, title, subtitle)
    text(root, 50, 182, 'A · Toppkobber og silketrykk, sett ovenfra', 27, '#0f172a', True)
    text(root, 1025, 182, 'B · Loddepasta + borehull under komponenten', 27, '#0f172a', True)
    left = panel(root, S/'top.svg', 50, 210, 925, 780, left_view)
    copper_outline(left, pad, '#38bdf8')
    right = panel(root, S/'paste.svg', 1025, 210, 925, 780, right_view)
    copper_outline(right, pad)
    for hole in holes:
        element(right, 'circle', cx=p.ToMM(hole.GetPosition().x), cy=p.ToMM(hole.GetPosition().y),
                r=p.ToMM(hole.GetDrillSize().x)/2, fill='none', stroke='#111827', stroke_width=.023)
    text(root, 50, 1032, caption, 27, '#0f172a', True)
    text(root, 50, 1075, 'B: Grå flater = faktisk F.Paste. Sorte sirkler = faktiske hull, tegnet oppå for sammenligning.', 25)
    text(root, 50, 1116, note, 25)
    save(root, f'0{2 if ref == "U1" else 3}-{ref.lower()}-loddeomrade')


detail('U1', u1, h1, [18.5,13.5,11,11], [21.5,16,5,6],
       'U1 — spenningsregulator LMR36510ADDAR',
       'Seks åpne, metalliserte hull på Ø 0,33 mm i loddeområdet under kapslingen',
       'Én sentral pastaåpning på 2,4 × 3,1 mm. Hullene ligger innenfor pastaåpningen.',
       'Blå stiplet ramme = kobberpadens ytterkant (2,95 × 4,90 mm), lagt til som forklaring.')
detail('U2', u2, h2, [61.5,0,25,17], [71.56,5.8,4.8,4.8],
       'U2 — Wi-Fi-modul ESP32-C3-WROOM-02U-N4',
       'Tolv åpne, metalliserte hull på Ø 0,30 mm i den sentrale jordpaden under modulen',
       'Ni pastaåpninger på 0,7 × 0,7 mm. Hullene er plassert i mellomrommene.',
       'Blå stiplet ramme = jordpadens ytterkant (2,90 × 2,90 mm), lagt til som forklaring.')

message = '''Hei Adi! Her er bilder av gjeldende Rev G.3 (100 × 100 mm, fire lag). Det er én produksjonsdetalj vi vil ha vurdert før bestilling:

U1 (LMR36510ADDAR) og U2 (ESP32-C3-WROOM-02U-N4) har loddepader på undersiden med åpne, metalliserte hull ned gjennom kortet. Hullene er ikke resin-fylte eller kobberkappede.

U1 har 6 hull på Ø 0,33 mm. Den sentrale pastaåpningen er 2,4 × 3,1 mm og dekker hullene. U2 har 12 hull på Ø 0,30 mm i en jordpad på 2,9 × 2,9 mm. Her er pastaen fordelt på 9 åpninger à 0,7 × 0,7 mm, med hullene mellom åpningene.

Bekymringen er at flytende loddetinn kan trekkes ned i hullene under reflow, slik at det blir for lite tinn eller dårlig kontakt under komponenten. Dette må vurderes sammen med sjablongtykkelse, pastamengde og loddeprosess. At pastaen er delt opp under U2 er ikke alene bevis på at prosessen er avklart.

KiCad-kontrollene har bestått, men de kontrollerer ikke kvaliteten på disse skjulte loddeforbindelsene. Dette er en uavklart produksjonsrisiko; JLCPCB har foreløpig ikke bekreftet noen feil eller gitt pristillegg.

Vi har lagt inn et ønske om at JLCPCB bekrefter om kortet kan monteres pålitelig slik det er, hvordan de kontrollerer loddetap gjennom hullene, og hvordan de inspiserer forbindelsene. Hvis de krever resin-fylte/kobberkappede hull eller en annen endring, må løsning og pris avklares først. Vanlig tenting med loddemaske er ikke det samme som fylte og kappede hull.

Hva tenker du om denne løsningen – særlig den sammenhengende pastaåpningen over hullene under U1? Ville du beholdt den dersom fabrikken godkjenner prosessen, endret pastamønsteret eller valgt fylte/kappede hull?

Bildene er eksportert fra gjeldende kortfil. Blå rammer og svarte hullsirkler i pastavisningen er forklaringsmarkeringer; kortet er ikke endret.
'''
(O/'MELDING-TIL-ADI.txt').write_text(message)
(O/'LES-MEG.txt').write_text('''Bilder til Adi — Rev G.3 — 14.09.2026

01: Hele kortet, med U1/U2 markert.
02: U1 med toppkobber og forstørret pasta-/hullvisning.
03: U2 med toppkobber og forstørret pasta-/hullvisning.

Alle visninger sees ovenfra. Komponentene er skjult for å vise loddeområdene.
Dette er tekniske KiCad-eksporter, ikke foto av produserte kort.
I pastavisning B er de faktiske borehullene tegnet oppå pastalaget som svarte sirkler.
Den blå stiplede rammen angir sentral kobberpad, ikke komponentens ytre kapsling.
Ingen produksjonsfiler, handlekurver eller firmware er endret.

Bakgrunn:
https://jlcpcb.com/help/article/pcb-via-covering
https://www.ti.com/lit/an/slma002h/slma002h.pdf

JLCPCBs prosessgodkjenning og fysisk prototypetest gjenstår.
''')
assert sha(board_path) == before
manifest = {'revision': 'G.3', 'pcb_sha256': before,
            'board_unmodified': True,
            'U1': {'open_holes': 6, 'drill_mm': .33, 'paste_opening_mm': [2.4,3.1]},
            'U2': {'open_holes': 12, 'drill_mm': .30, 'paste_windows': 9, 'paste_window_mm': [.7,.7]},
            'images': {f.name: sha(f) for f in O.glob('*.png')},
            'sources': {f.name: sha(f) for f in S.glob('*.svg')}}
(O/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
with zipfile.ZipFile(O.parent/'leaf-heat-rev-g3-lodding-bilder-til-adi.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for f in sorted(O.iterdir()):
        if f.suffix in {'.png','.txt','.json'}:
            archive.write(f, f.name)
print(json.dumps(manifest, ensure_ascii=False, indent=2))

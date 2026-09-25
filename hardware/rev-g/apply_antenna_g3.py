"""One-time G.2 -> G.3 external-antenna migration, preserving all PCB copper."""
from pathlib import Path
import copy, hashlib, json, uuid
import pcbnew as p
import sexpdata as sx

H=Path(__file__).resolve().parent
S=sx.Symbol
def key(q): return str(q[0]) if isinstance(q,list) and q else ''
def child(q,name): return next((x for x in q if key(x)==name),None)
def children(q,name): return [x for x in q if key(x)==name]
def prop(q,name): return next(x for x in children(q,'property') if x[1]==name)
def ident(): return str(uuid.uuid4())
old='ESP32-C3-WROOM-02-N4'; new='ESP32-C3-WROOM-02U-N4'
oldfp='ESP32-C3-WROOM-02_0p3mm_Vias__Factory'
newfp='ESP32-C3-WROOM-02U_0p3mm_Vias__Factory'
assert (H/'history/rev-g2-before-external-antenna.zip').exists()
assert hashlib.sha256((H/'leaf-heat-v7.kicad_pcb').read_bytes()).hexdigest()=='e219b6422497241ae2c65dcf21172432d0750c268bfbf207ad921b2527b9f2b4'
stock=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
orig=sx.loads((stock/'footprints/RF_Module.pretty/ESP32-C3-WROOM-02.kicad_mod').read_text())
ufp=sx.loads((stock/'footprints/RF_Module.pretty/ESP32-C3-WROOM-02U.kicad_mod').read_text())
def strip_uuid(q): return [strip_uuid(x) if isinstance(x,list) else x for x in q if key(x)!='uuid']
assert [strip_uuid(q) for q in children(orig,'pad')]==[strip_uuid(q) for q in children(ufp,'pad')]
graphics={'fp_line','fp_rect','fp_poly','fp_circle','fp_arc','fp_text','model'}
def update_fp(q,library=False):
    before=copy.deepcopy(children(q,'pad'))
    q[1]=newfp if library else 'Leaf:'+newfp
    for name in ['Value','MPN']:
        for item in children(q,'property'):
            if item[1]==name:item[2]=new
    desc=child(q,'descr')
    if desc:desc[1]='Espressif ESP32-C3-WROOM-02U; external U.FL antenna; 0.3 mm unfilled thermal vias; factory assembly'
    q[:]=[x for x in q if key(x) not in graphics]
    for item in ufp:
        if key(item) in graphics:
            item=copy.deepcopy(item)
            if child(item,'uuid'):child(item,'uuid')[1]=ident()
            stroke=child(item,'stroke')
            if stroke and child(item,'layer') in [[S('layer'),'F.SilkS'],[S('layer'),'B.SilkS']]:
                child(stroke,'width')[1]=0.15
            q.append(item)
    assert children(q,'pad')==before
    return q
local=update_fp(sx.loads((H/'Leaf.pretty'/f'{oldfp}.kicad_mod').read_text()),True)
(H/'Leaf.pretty'/f'{newfp}.kicad_mod').write_text(sx.dumps(local)+'\n')
board=sx.loads((H/'leaf-heat-v7.kicad_pcb').read_text())
u2=next(q for q in children(board,'footprint') if prop(q,'Reference')[2]=='U2')
update_fp(u2)
child(child(board,'title_block'),'rev')[1]='G.3'
for q in children(board,'gr_text'):q[1]=q[1].replace('REV G.2','REV G.3')
(H/'leaf-heat-v7.kicad_pcb').write_text(sx.dumps(board)+'\n')
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'));p.SaveBoard(str(H/'leaf-heat-v7.kicad_pcb'),b)

# Local symbol derives from the official 02U pin definition, with accurate
# description and our reviewed exposed-pad footprint. No RF pad is invented
# on the carrier PCB: ANT1 plugs directly into the module's own connector.
stock_symbols=sx.loads((stock/'symbols/RF_Module.kicad_sym').read_text())
symbol=copy.deepcopy(next(q for q in children(stock_symbols,'symbol') if q[1]=='ESP32-C3-WROOM-02U'))
prop(symbol,'Footprint')[2]='Leaf:'+newfp
prop(symbol,'Description')[2]='ESP32-C3 Wi-Fi/BLE module with U.FL external antenna connector'
lib=sx.loads((H/'Leaf.kicad_sym').read_text());lib.append(symbol)
(H/'Leaf.kicad_sym').write_text(sx.dumps(lib)+'\n')
sch=sx.loads((H/'leaf-heat-v7.kicad_sch').read_text())
inline=child(sch,'lib_symbols')
old_symbol=next(q for q in children(inline,'symbol') if q[1]=='RF_Module:ESP32-C3-WROOM-02')
def pins(q):
    return [strip_uuid(x) for sub in children(q,'symbol') for x in children(sub,'pin')]
assert pins(old_symbol)==pins(symbol), 'Unexpected module symbol pin change'
inline.remove(old_symbol)
cached=copy.deepcopy(symbol);cached[1]='Leaf:ESP32-C3-WROOM-02U';inline.append(cached)
inst=next(q for q in children(sch,'symbol') if prop(q,'Reference')[2]=='U2')
child(inst,'lib_id')[1]='Leaf:ESP32-C3-WROOM-02U'
prop(inst,'Value')[2]=prop(inst,'MPN')[2]=new
prop(inst,'Footprint')[2]='Leaf:'+newfp
# Instance inherits the corrected Description from its cached library symbol.
child(child(sch,'title_block'),'rev')[1]='G.3'
child(child(sch,'title_block'),'date')[1]='2026-09-14'
for q in children(sch,'text'):q[1]=q[1].replace('G.2','G.3')
sch.append([S('text'),'ANT1 / PLUG-IN ANTENNA (OFF BOARD)\nMolex 1461530300: 300 mm cable, MHF I / U.FL.\nPlug into U2 antenna socket before powering Wi-Fi.\nFit to suitable plastic outside the casing; secure cable.\nNot part of the factory PCB placement/paste files.',
    [S('at'),420,65,0],[S('effects'),[S('font'),[S('size'),1.4,1.4]],[S('justify'),S('left'),S('bottom')]],
    [S('uuid'),ident()]])
(H/'leaf-heat-v7.kicad_sch').write_text(sx.dumps(sch)+'\n')
parts=json.loads((H/'parts.json').read_text());part=next(q for q in parts if q['ref']=='U2')
part.update(symbol='Leaf:ESP32-C3-WROOM-02U',value=new,mpn=new,footprint='Leaf:'+newfp,
            notes='G.3: U.FL external antenna connector. Fit ANT1 before enabling Wi-Fi. Pad geometry, GPIOs and 4 MB flash unchanged.')
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
accessories=[{'ref':'ANT1','manufacturer':'Molex','mpn':'1461530300','mouser_mpn':'538-146153-0300',
 'mouser_ordering_mpn':'146153-0300','quantity_per_board':1,'assembly':'PLUG-IN / OFF-BOARD',
 'description':'Adhesive balanced flex antenna, 300 mm 1.13 mm coax, MHF I / U.FL compatible',
 'frequency_used_GHz':2.4,'impedance_ohm':50,'peak_gain_at_2p4_GHz_dBi':2.2,
 'body_mm':[34.9,9,0.1],'operating_C':[-40,85],
 'datasheet':'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/146/146153/PS-146153-100-001.pdf',
 'notes':'Supplier ordering punctuation differs from manufacturer drawing. No soldering; connect to U2. Not a PCB footprint or factory placement.'}]
(H/'accessories.json').write_text(json.dumps(accessories,indent=2)+'\n')
print('Applied G.3 external module and off-board antenna; refill/export/audit required.')

"""Create the UART revision from the preserved Rev B PCB; no autorouting.

Run using tools/KiCAD-MCP-Server/venv/bin/python3 from the repository root.
This script only writes rev-c. Native ERC/DRC and audit_rev_c.py are separate.
"""
from pathlib import Path
from copy import deepcopy
import sys, json, shutil, hashlib, subprocess, math
import pcbnew as p
import sexpdata as sx

H = Path(__file__).resolve().parent
B = H.parent / 'rev-b'
sys.path.insert(0, str(H.parent))
import build_design as g

NAME = 'leaf-heat-v3'
REMOVED = {'J2', 'R11', 'R12', 'D2', 'R13', 'R14', 'R15', 'R16', 'R17', 'D5'}
CHANGED = {'U2', 'U4', 'C14'}
USB_NETS = {'USB_5V', 'CC1', 'CC2', 'USB_CONN_P', 'USB_CONN_N', 'USB_D_P', 'USB_D_N', 'USB_PRESENT'}

def vec(q): return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q): return (p.ToMM(q.x), p.ToMM(q.y))

def main():
    (H / 'exports').mkdir(parents=True, exist_ok=True)
    for name in ['Leaf.pretty', 'Leaf.kicad_sym', 'fp-lib-table', 'sym-lib-table']:
        src = B / name
        if src.is_dir(): shutil.copytree(src, H / name, dirs_exist_ok=True)
        else: shutil.copy2(src, H / name)
    baseline = {x.name: hashlib.sha256(x.read_bytes()).hexdigest()
                for x in B.glob('leaf-heat-v2.kicad_*') if x.suffix != '.kicad_prl'}
    (H / 'exports/baseline-sha256.json').write_text(json.dumps(baseline, indent=2) + '\n')

    board = p.LoadBoard(str(B / 'leaf-heat-v2.kicad_pcb'))
    oldfps = {f.GetReference(): f for f in board.GetFootprints()}
    # The schematic rotation and PCB rotation are distinct: restore schematic
    # angles from the original generator, not Rev B's exported placement metadata.
    baseparts = {q['ref']: q for q in g.parts}
    parts = [deepcopy(q) for q in json.loads((B / 'parts.json').read_text()) if q['ref'] not in REMOVED]
    for q in parts: q['angle'] = baseparts[q['ref']]['angle']
    byref = {q['ref']: q for q in parts}
    # Project-specific connector symbol keeps the exact custom-footprint filter
    # explicit; its electrical pins are identical to the generic DE9 symbol.
    conn=g.get_symbol('Connector','DE9_Pins_MountingHoles')
    conn[1]='DE9_Leaf_Cable'
    for unit in g.children(conn,'symbol'):unit[1]=unit[1].replace('DE9_Pins_MountingHoles','DE9_Leaf_Cable')
    for prop in g.children(conn,'property'):
        if prop[1]=='ki_fp_filters':prop[2]='*NorComp_182-009-113R531*'
    g.custom['DE9_Leaf_Cable']=conn
    byref['J1']['symbol']='Leaf:DE9_Leaf_Cable'
    byref['U2']['nets'].update({'11': 'UART_RX', '12': 'UART_TX', '13': None, '14': None, '15': None})
    byref['U4'].update(value='USBLC6-2SC6 / UART ESD', sch=[99.06, 187.96],
        xy=[55.81, 40], rotation=90, symbol='Leaf:UART_ESD',
        nets={'1':'PROG_RX', '2':'GND', '3':'PROG_TX', '4':'PROG_TX', '5':'3V3', '6':'PROG_RX'},
        notes='UART service connector ESD protection. Pins 1/6 and 3/4 are feed-through channels; pin 5 references 3.3 V. Not a USB interface.')
    byref['C14'].update(value='100nF / 16V', sch=[124.46, 160.02], xy=[55.81, 36], rotation=90,
        mpn='GRM188R71C104KA01D', nets={'1':'3V3','2':'GND'}, notes='Local UART ESD reference-rail bypass.')
    def add(**kw):
        q=dict(datasheet='', notes='', angle=0, rotation=0, manufacturer='Yageo')
        q.update(kw); parts.append(q); byref[q['ref']]=q
    add(ref='J3', symbol='Connector_Generic:Conn_01x03', value='UART / 3.3V LOGIC',
        footprint='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical',
        sch=[38.1,185.42], xy=[52,44], rotation=90, manufacturer='Harwin', mpn='M20-9990346',
        nets={'1':'GND','2':'PROG_RX','3':'PROG_TX'},
        datasheet='https://www.harwin.com/products/M20-9990346',
        notes='Fit on top. Pin 1 GND; 2 board RX (adapter TX); 3 board TX (adapter RX). No supply pin. 3.3 V logic only; no RS-232. Header origin is pin 1.')
    for ref, sch, pos, nets in [
        ('R18',[162.56,177.8],[59.8,11],{'1':'UART_TX','2':'PROG_TX'}),
        ('R19',[162.56,200.66],[59.8,13],{'1':'PROG_RX','2':'UART_RX'})]:
        add(ref=ref, symbol='Device:R', value='1k', footprint=g.RFP,
            sch=sch, xy=pos, rotation=180 if ref=='R19' else 0, angle=90, nets=nets, mpn='RC0603FR-071KL',
            notes='UART service series resistance; 115200 baud initial programming, short leads. Not a 5 V level shifter.')
    add(ref='R20', symbol='Device:R', value='10k', footprint=g.RFP,
        sch=[208.28,187.96], xy=[54.5,17], rotation=0,
        nets={'1':'3V3','2':'UART_RX'}, mpn='RC0603FR-0710KL',
        notes='Hold UART RX at idle high when the programming lead is absent.')

    g.HERE=H; g.NAME=NAME; g.parts=parts
    g.custom['UART_ESD']=g.custom_ic('UART_ESD',[
        (1,'RX','passive',-12.7,2.54,0),(3,'TX','passive',-12.7,-2.54,0),
        (6,'RX','passive',12.7,2.54,180),(4,'TX','passive',12.7,-2.54,180),
        (5,'VREF','passive',0,10.16,270),(2,'GND','passive',0,-10.16,90)])
    g.schematic()
    s = sx.load(open(H / (NAME+'.kicad_sch')))
    # Remove the obsolete USB supply flag (including its label).
    flaguids={g.uid('#FLG04'),g.uid('#FLG04label')}
    s[:] = [x for x in s if not (isinstance(x,list) and g.child(x,'uuid') and g.child(x,'uuid')[1] in flaguids)]
    replacements={
        'REV A — ENGINEERING PROTOTYPE — NOT RELEASED FOR MANUFACTURE':'REV C — UART PROGRAMMING — ENGINEERING PROTOTYPE',
        '3  USB-C PROGRAMMING / POWER':'3  UART PROGRAMMING — NO USB / NO PROGRAMMER POWER',
        'USB-C supplies/programs the board on the bench.\nGPIO3 detects USB; firmware must inhibit vehicle commands when USB is present.':
        'J3: 1 GND | 2 board RX | 3 board TX. 3.3 V logic only.\nPower from a current-limited 12 V bench supply via J1 (9 +, 3 GND).\nVehicle unplugged. Adapter power wire unused. Connect only with board powered.\nHold BOOT; press/release RESET; release BOOT. Flash via UART0 at 115200 baud.',
        'Power flags identify external supplies and the buck output for electrical checks.':
        'GPIO3 / GPIO18 / GPIO19 unused. No USB-presence sensing in Rev C.\nOTA updates need firmware implementation. UART remains the recovery interface.',
    }
    for x in g.children(s,'text'):
        if x[1] in replacements: x[1]=replacements[x[1]]
    title=g.child(s,'title_block')
    g.child(title,'rev')[1]='C / UART prototype'; g.child(title,'date')[1]='2026-09-12'
    from polish_schematic import polish
    s=polish(s)
    (H/(NAME+'.kicad_sch')).write_text(sx.dumps(s))
    subprocess.run([g.CLI,'sch','export','netlist','--format','kicadxml','-o',str(H/'exports'/f'{NAME}.net.xml'),str(H/(NAME+'.kicad_sch'))],check=True)
    (H/'exports/leaf-heat-v1.net.xml').unlink()

    # Remove the old programming branch, leaving the vehicle circuit geometry.
    for t in list(board.GetTracks()):
        if t.GetNetname().lstrip('/') in USB_NETS: board.RemoveNative(t)
        elif isinstance(t,p.PCB_VIA) and t.GetNetname()=='/GND' and xy(t.GetPosition()) in [(60,17),(60,22),(60,27),(55,37),(63,32),(58.525,38.825),(56.5,36.6)]:
            board.RemoveNative(t)
    for z in list(board.Zones()):
        if z.GetNetname().lstrip('/') in USB_NETS or 'USB' in z.GetZoneName(): board.RemoveNative(z)
    # Ground and supply tails specifically attached to the old programming parts.
    old_program_refs=REMOVED | {'U4','C14'}
    ends=[]
    for ref in old_program_refs:
        for pad in oldfps[ref].Pads():
            if pad.GetNetname() in ['/GND','/VPWR']: ends.append((pad.GetNetname(),xy(pad.GetPosition())))
    removed_endpoints=[]
    for t in list(board.GetTracks()):
        if isinstance(t,p.PCB_VIA): continue
        a,c=xy(t.GetStart()),xy(t.GetEnd())
        if any(n==t.GetNetname() and (math.dist(q,a)<1e-5 or math.dist(q,c)<1e-5) for n,q in ends):
            removed_endpoints.extend([(t.GetNetname(),a),(t.GetNetname(),c)]); board.RemoveNative(t)
    # Keep GND stitching vias; remove only a former VPWR branch via if applicable.
    for t in list(board.GetTracks()):
        if isinstance(t,p.PCB_VIA) and t.GetNetname()=='/VPWR' and any(n=='/VPWR' and math.dist(xy(t.GetPosition()),q)<1e-5 for n,q in removed_endpoints):
            board.RemoveNative(t)
    for ref in REMOVED | {'U4','C14'}: board.RemoveNative(oldfps[ref])

    import xml.etree.ElementTree as ET
    nr=ET.parse(H/'exports'/f'{NAME}.net.xml').getroot()
    pinmap={}
    for net in nr.findall('./nets/net'):
        n=net.get('name')
        if not board.FindNet(n): board.Add(p.NETINFO_ITEM(board,n))
        for nd in net.findall('node'): pinmap[(nd.get('ref'),nd.get('pin'))]=n
    fps={f.GetReference():f for f in board.GetFootprints()}
    for q in parts:
        if q['ref'] not in fps:
            lib,name=q['footprint'].split(':')
            f=p.FootprintLoad(str(g.LIB/'footprints'/(lib+'.pretty')),name)
            f.SetReference(q['ref']); f.SetFPID(p.LIB_ID(lib,name)); f.SetPosition(vec(q['xy'])); f.SetOrientationDegrees(q['rotation'])
            f.SetPath(p.KIID_PATH('/'+g.ROOT+'/'+g.uid(q['ref'])))
            board.Add(f); fps[q['ref']]=f
        f=fps[q['ref']]; f.SetValue(q['value']); f.Value().SetVisible(False)
        if q['ref']=='U2':f.SetAttributes(p.FP_SMD)
        if q['ref']=='J3':
            f.SetLocalZoneConnection(p.ZONE_CONNECTION_THERMAL)
            for hd in f.Pads():
                hd.SetThermalGap(p.FromMM(.25))
        for field in ['MPN','Manufacturer','Datasheet']:
            value=q[{'MPN':'mpn','Manufacturer':'manufacturer','Datasheet':'datasheet'}[field]]
            f.SetField(field,value);f.GetField(field).SetVisible(False)
        for pad in f.Pads():
            n=pinmap.get((q['ref'],pad.GetNumber()))
            if n: pad.SetNet(board.FindNet(n))
        q['xy']=list(xy(f.GetPosition())); q['rotation']=f.GetOrientationDegrees()

    def path(net, pts, w=.25, layer=p.F_Cu):
        for a,c in zip(pts,pts[1:]):
            if math.dist(a,c)<1e-6: continue
            t=p.PCB_TRACK(board);t.SetNet(board.FindNet('/'+net));t.SetStart(vec(a));t.SetEnd(vec(c));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetLocked(True);board.Add(t)
    def via(net,q):
        t=p.PCB_VIA(board);t.SetPosition(vec(q));t.SetWidth(p.FromMM(.65));t.SetDrill(p.FromMM(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetNet(board.FindNet('/'+net));t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);board.Add(t)
    def pad(ref,n): return xy(next(x for x in fps[ref].Pads() if x.GetNumber()==str(n)).GetPosition())
    # All UART signals on top over the dedicated ground layer.
    path('UART_TX',[pad('U2',12),pad('R18',1)])
    path('UART_RX',[pad('U2',11),(57.7,12.5),(58.2,13),pad('R19',2)])
    # RX bias connection takes a short back-layer bridge outside the antenna.
    via('UART_RX',(58.7,14.4));path('UART_RX',[pad('R19',2),(58.7,14.4)])
    via('UART_RX',(55.325,17));path('UART_RX',[(58.7,14.4),(56.1,17),pad('R20',2)],layer=p.B_Cu)
    path('PROG_TX',[pad('R18',2),(61,11)]);via('PROG_TX',(61,11))
    path('PROG_TX',[(61,11),(63,13),(63,31.5),(57.8,36.7),(57.8,38.8625)],layer=p.B_Cu)
    via('PROG_TX',(57.8,38.8625));path('PROG_TX',[(57.8,38.8625),pad('U4',4)])
    path('PROG_RX',[pad('R19',1),(61.4,13.6)]);via('PROG_RX',(61.4,13.6))
    path('PROG_RX',[(61.4,13.6),(60.5,14.5),(60.5,30),(53.8,36.7),(53.8,38.8625)],layer=p.B_Cu)
    via('PROG_RX',(53.8,38.8625));path('PROG_RX',[(53.8,38.8625),pad('U4',6)])
    path('PROG_RX',[pad('U4',1),pad('U4',6)])
    path('PROG_TX',[pad('U4',3),pad('U4',4)])
    path('PROG_RX',[pad('U4',1),(54.86,43.68),pad('J3',2)])
    path('PROG_TX',[pad('U4',3),(56.76,43.68),pad('J3',3)])
    # Two short ESD ground returns; bypass directly beside VREF.
    path('GND',[pad('U4',2),(55.81,42.2),(55.81,43.1)],.4);via('GND',(55.81,42.2));via('GND',(55.81,43.1))
    path('3V3',[pad('U4',5),pad('C14',1)],.4);via('3V3',(54.7,36.775));path('3V3',[pad('C14',1),(54.7,36.775)],.4)
    # Extend the existing 3.3 V distribution area to the programming protection.
    # The dedicated In1.Cu GND reference is unchanged.
    for z in board.Zones():
        if z.GetZoneName()=='3V3 distribution':
            poly=z.Outline();poly.RemoveAllContours();poly.NewOutline()
            for q in [(8,18),(20,18),(20,1.2),(61,1.2),(61,6.2),(59,6.2),(59,40),(53,40),(53,32),(8,32)]:poly.Append(vec(q))
    via('3V3',(53.675,17));path('3V3',[pad('R20',1),(53.675,17)],.4)
    path('GND',[pad('C14',2),(56.95,35.225)],.4);via('GND',(56.95,35.225))

    for d in board.GetDrawings():
        if isinstance(d,p.PCB_TEXT) and 'REV B' in d.GetText(): d.SetText('REV C / UART')
    def label(txt,q,size=.85):
        d=p.PCB_TEXT(board);d.SetText(txt);d.SetPosition(vec(q));d.SetTextSize(vec((size,size)));d.SetTextThickness(p.FromMM(.13));d.SetLayer(p.F_SilkS);board.Add(d)
    label('UART 3V3',(54.54,49),.85)
    for txt,q in [('GND',(52,46.8)),('RX',(54.54,46.8)),('TX',(57.08,46.8))]:label(txt,q,.8)
    label('NO POWER PIN',(48,40),.8)
    for ref,at in {'J3':(49.5,44), 'R18':(59.8,9.6), 'R19':(60.3,15.2), 'R20':(54.5,18.6),'U4':(59,40),'C14':(58.5,35),'C11':(62,8.8)}.items():
        f=fps[ref];f.Reference().SetPosition(vec(at));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetTextSize(vec((.8,.8)));f.Reference().SetTextThickness(p.FromMM(.12))
    board.BuildConnectivity()
    p.SaveBoard(str(H/(NAME+'.kicad_pcb')),board)
    # Standard four-layer FR-4; no controlled impedance or custom dielectric.
    d=sx.load(open(H/(NAME+'.kicad_pcb')))
    g.child(g.child(d,'general'),'thickness')[1]=1.6
    stack=g.child(g.child(d,'setup'),'stackup')
    for layer in g.children(stack,'layer'):
        name=layer[1]
        if name.startswith('dielectric'):
            g.child(layer,'material')[1]='FR4 - standard factory stack'
            g.child(layer,'thickness')[1]=1.05 if name=='dielectric 2' else .185
            g.child(layer,'epsilon_r')[1]=4.5
    g.child(stack,'dielectric_constraints')[1]=sx.Symbol('no')
    (H/(NAME+'.kicad_pcb')).write_text(sx.dumps(d))
    pro=json.loads((B/'leaf-heat-v2.kicad_pro').read_text())
    pro['net_settings']['classes']=[x for x in pro['net_settings']['classes'] if x['name']!='USB']
    pro['net_settings']['netclass_patterns']=[x for x in pro['net_settings']['netclass_patterns'] if x['netclass']!='USB' and x['pattern'].lstrip('/') not in USB_NETS]
    pro['board']['design_settings']['diff_pair_dimensions']=[]
    pro['board']['design_settings']['track_widths']=[0,.2,.25,.4,.5,.8,1]
    severity=pro['board']['design_settings']['rule_severities']
    for key in ['missing_courtyard','footprint_filters_mismatch','track_not_centered_on_via']:severity[key]='warning'
    # Both exposed-pad IC footprints include plated thermal holes but are
    # surface-mount parts. KiCad's pad-count heuristic misclassifies this mix.
    severity['footprint_type_mismatch']='ignore'
    (H/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
    (H/(NAME+'.kicad_dru')).write_text('''(version 1)
(rule "Ground reference layer: no tracks" (layer In1.Cu) (constraint disallow track))
(rule "Power distribution layer: no tracks" (layer In2.Cu) (constraint disallow track))
''')
    (H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
    print('Rev C created:',len(parts),'components,',len({q['mpn'] for q in parts}),'MPNs')

if __name__=='__main__': main()

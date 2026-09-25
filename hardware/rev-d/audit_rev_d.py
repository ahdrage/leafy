"""Independent native-file audit; does not import the CAD generator."""
from pathlib import Path
import collections,json,hashlib,math,csv,xml.etree.ElementTree as ET
import pcbnew as p
H=Path(__file__).resolve().parent;E=H/'exports';C=H.parent/'rev-c'
checks=[]
def check(ok,why):
    if not ok:raise AssertionError(why)
    checks.append(why)
def xy(q):return (p.ToMM(q.x),p.ToMM(q.y))
def vec(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
b=p.LoadBoard(str(H/'leaf-heat-v4.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
parts=json.loads((H/'parts.json').read_text());meta={q['ref']:q for q in parts};old={q['ref']:q for q in json.loads((C/'parts.json').read_text())}
tests=json.loads((H/'testpoints.json').read_text());factory={'U1','U2','U4','L1'}
baseline=json.loads((E/'baseline-sha256.json').read_text())
check(all(hashlib.sha256((C/n).read_bytes()).hexdigest()==sha for n,sha in baseline.items()),'Rev C native project is preserved byte-for-byte')
check(set(meta)==set(old) and len(parts)==41,'All 41 circuit components retained; no circuit parts removed')
check({q['ref'] for q in parts if q['assembly']=='FACTORY'}==factory,'Exactly U1 U2 U4 L1 assigned to factory assembly')
check(sum(q['assembly']=='HAND' for q in parts)==37,'Exactly 37 components assigned to hand soldering')
check(set(fps)==set(meta)|{q['ref'] for q in tests}|{'H1','H2','H3','H4'},'Only seven bare test holes and four mounting holes supplement the full BOM')
def netlist(path):
    root=ET.parse(path).getroot();pins={};nets=collections.defaultdict(set)
    for n in root.findall('./nets/net'):
        for q in n.findall('node'):
            key=(q.get('ref'),q.get('pin'));pins[key]=n.get('name');nets[n.get('name')].add(key)
    return root,pins,nets
root,pins,nets=netlist(E/'leaf-heat-v4.net.xml');_,cpins,cnets=netlist(C/'exports/leaf-heat-v3.net.xml')
check(all(pins[k]==n for k,n in cpins.items() if k[0] in meta),'Every original schematic pin retains its Rev C net')
for q in parts:
    ref=q['ref'];f=fps[ref]
    check(q['nets']==old[ref]['nets'],f'{ref} electrical connections unchanged')
    check(f.GetFieldText('MPN')==q['mpn'] and f.GetFieldText('Manufacturer')==q['manufacturer'],f'{ref} PCB purchasing fields match BOM')
    check(f.GetValue()==q['value'],f'{ref} PCB value matches BOM')
    footprint_id = str(f.GetFPID().GetLibNickname()) + ':' + str(f.GetFPID().GetLibItemName())
    check(footprint_id==q['footprint'],f'{ref} assigned footprint matches BOM')
    check(f.GetFieldText('Assembly')==q['assembly'],f'{ref} assembly ownership agrees')
    for pad in f.Pads():
        if pad.GetNumber():check(pad.GetNetname()==pins[(ref,pad.GetNumber())],f'{ref}.{pad.GetNumber()} PCB net matches schematic')
    if q['assembly']=='HAND':
        check(all(p.F_Paste not in list(pad.GetLayerSet().Seq()) and p.B_Paste not in list(pad.GetLayerSet().Seq()) for pad in f.Pads()),f'{ref} has no factory stencil apertures')
        check(f.GetLocalZoneConnection()==p.ZONE_CONNECTION_THERMAL,f'{ref} uses hand-solder thermal reliefs')
    if ref.startswith('R'):
        check(q['mpn']==old[ref]['mpn'].replace('RC0603','RC1206') and q['value']==old[ref]['value'],f'{ref} is the same 1% resistance in 1206')
        check('1206' in q['footprint'] and 'HandSolder' in q['footprint'],f'{ref} uses extended 1206 pads')
    if ref.startswith('C'):
        check(any(n in q['footprint'] for n in ['1206','1210']) and 'HandSolder' in q['footprint'],f'{ref} uses a large hand-solder capacitor footprint')
        check(q['value'].split('/')[0].strip()==old[ref]['value'].split('/')[0].strip(),f'{ref} nominal capacitance retained')
        vr=lambda s:float(s.split('/')[1].strip().rstrip('V'))
        check(vr(q['value'])>=vr(old[ref]['value']),f'{ref} capacitor voltage rating retained or increased')
for ref in factory|{'J1','J3','D1','D3','D4','F1','U3','C1','C5','C6','C7'}:
    check(meta[ref]['mpn']==old[ref]['mpn'],f'{ref} exact original component retained')
expected_caps={'C2':'C1206C224K1RACTU','C3':'C1206C105K3RACTU','C8':'C1206C105K3RACTU','C9':'C1206C106K4RACTU'}
expected_caps.update({r:'C1206C104K5RACTU' for r in ['C4','C10','C11','C12','C13','C14']})
check(all(meta[r]['mpn']==mpn for r,mpn in expected_caps.items()),'All new capacitors match the independently researched KEMET MPNs')
check(meta['D6']['mpn']=='LTST-C150KGKT','1206 green LED uses the selected Lite-On MPN')
for ref in ['SW1','SW2']:
    pads=list(fps[ref].Pads());points={xy(q.GetPosition()) for q in pads}
    check(meta[ref]['mpn']=='B3F-1000' and len(pads)==4 and all(q.GetAttribute()==p.PAD_ATTRIB_PTH for q in pads),f'{ref} is a four-leg through-hole B3F-1000')
    xx={a[0] for a in points};yy={a[1] for a in points}
    check(len(xx)==len(yy)==2 and abs(max(xx)-min(xx)-6.5)<1e-6 and abs(max(yy)-min(yy)-4.5)<1e-6,f'{ref} hole pattern is 6.5 x 4.5 mm')
    check(all(abs(p.ToMM(q.GetDrillSize().x)-1.1)<1e-6 for q in pads),f'{ref} uses 1.1 mm finished holes')
for q in tests:
    check(pins[(q['ref'],'1')]=='/'+q['value'],f'{q["ref"]} test hole exposes {q["value"]}')
    pad=list(fps[q['ref']].Pads())[0]
    check(xy(pad.GetSize())==(3,3) and xy(pad.GetDrillSize())==(1.5,1.5),f'{q["ref"]} is a 3 mm pad / 1.5 mm hole')
components={c.get('ref'):c for c in root.findall('./components/comp')}
for q in parts:check(components[q['ref']].findtext('value')==q['value'],f'{q["ref"]} exported schematic value matches BOM')
check(b.GetCopperLayerCount()==4,'Four copper layers retained')
outline=[d for d in b.GetDrawings() if d.GetLayer()==p.Edge_Cuts]
corners={xy(q) for d in outline for q in [d.GetStart(),d.GetEnd()]}
check(len(outline)==4 and corners=={(0,0),(150,0),(150,150),(0,150)},'Board outline is exactly 150 x 150 mm')
check(xy(b.GetDesignSettings().GetAuxOrigin())==(0,150),'Manufacturing origin is the lower-left corner')
check(all(f.GetLayer()==p.F_Cu for f in fps.values()),'All components mount on the top')
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)];vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
check(not any(t.GetLayer() in [p.In1_Cu,p.In2_Cu] for t in tracks),'Both internal layers contain no routed tracks')
check(min(p.ToMM(t.GetWidth()) for t in tracks)>=.25,'All routes at least 0.25 mm wide')
check(all(p.FromMM(.3)<=t.GetDrill() for t in vias),'Separate signal/ground vias have drills of at least 0.30 mm')
gnd=[z for z in b.Zones() if z.GetLayer()==p.In1_Cu and z.GetNetname()=='/GND' and not z.GetIsRuleArea()]
check(len(gnd)==1,'One dedicated internal ground reference plane')
miss=[]
# Test the interior of the 108..136 mm rule area. Polygon edge ownership
# at exactly x=136 is numerically ambiguous in HitTestFilledArea.
for x in [108.1,*range(109,136),135.9]:
    for y in [.4,.6,.8]:
        for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
            if any(not z.GetIsRuleArea() and z.GetLayer()==layer and z.HitTestFilledArea(layer,vec((x,y))) for z in b.Zones()):miss.append((x,y,layer))
check(not miss,'All sampled interior points of the antenna clearance contain no poured copper on any layer')
check(any(z.GetIsRuleArea() and {p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu}.issubset(set(z.GetLayerSet().Seq())) for z in fps['U2'].Zones()),'Antenna rule area applies to every copper layer')
before=p.LoadBoard(str(E/'before-router.kicad_pcb'));bt={t.m_Uuid.AsString():t for t in before.GetTracks()};now={t.m_Uuid.AsString():t for t in b.GetTracks()}
check(set(bt).issubset(now),'All manually placed critical copper items remain present')
for uid,t in bt.items():
    q=now[uid]
    if isinstance(t,p.PCB_VIA):
        same_size=isinstance(q,p.PCB_VIA) and q.GetDrill()==t.GetDrill() and all(q.GetWidth(layer)==t.GetWidth(layer) for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu])
    else:
        same_size=not isinstance(q,p.PCB_VIA) and q.GetWidth()==t.GetWidth() and q.GetLayer()==t.GetLayer()
    check(q.GetNetname()==t.GetNetname() and xy(q.GetStart())==xy(t.GetStart()) and xy(q.GetEnd())==xy(t.GetEnd()) and same_size,'Preserved critical copper geometry/net '+uid)
paste={f.GetReference() for f in fps.values() if any(p.F_Paste in list(pad.GetLayerSet().Seq()) for pad in f.Pads())}
check(paste==factory,'Stencil includes exactly the four factory parts')
for name,col in [('BOM-FACTORY-PCBWay.csv','Designator'),('BOM-FACTORY-JLCPCB.csv','Designator'),('placements-FACTORY.csv','Ref'),('CPL-FACTORY-JLCPCB.csv','Designator')]:
    rows=list(csv.DictReader((E/name).open()));check(len(rows)==4 and {q[col] for q in rows}==factory,name+' contains exactly four intended references')
hand_rows=list(csv.DictReader((E/'BOM-HAND.csv').open()))
check(sum(int(q['Qty for ONE board']) for q in hand_rows)==37 and sum(int(q['Qty for TWO boards']) for q in hand_rows)==74,'Hand shopping quantities cover one or two boards exactly')
check({r for q in hand_rows for r in q['References'].split(',')}==set(meta)-factory,'Hand shopping list covers every hand-fitted reference once')
settings=json.loads((H/'leaf-heat-v4.kicad_pro').read_text());check(not settings['board']['design_settings']['drc_exclusions'],'No individual DRC exclusions')
drc=json.loads((E/'drc-final.json').read_text());check(all(not drc[k] for k in ['violations','unconnected_items','schematic_parity']),'Native DRC, connectivity and schematic parity all pass')
erc=json.loads((E/'erc.json').read_text());check(not any(s.get('violations') for s in erc.get('sheets',[])),'Native ERC passes')
def net(r,n):return pins[(r,str(n))].lstrip('/')
check([net('J1',n) for n in [9,3,7,2]]==['CAR_12V','GND','CAN_H','CAN_L'],'Nissan DB9 pinout retained')
check([net('J3',n) for n in [1,2,3]]==['GND','PROG_RX','PROG_TX'],'UART header exposes no supply pin')
check([net('U2',n) for n in [3,4,7,8,11,12,17]]==['CAN_TX','CAN_RX','BOOT_IO8','BOOT_IO9','UART_RX','UART_TX','CAN_STB'],'Firmware GPIO assignments retained')
check(not any({q['nets'].get('1'),q['nets'].get('2')}=={'CAN_H','CAN_L'} and q['ref'].startswith('R') for q in parts),'No CAN termination resistor added')
vnom=1+100/43.2;vmin=.985*(1+100*.99/(43.2*1.01));vmax=1.015*(1+100*1.01/(43.2*.99));adc=65*47*1.01/(1000*.99+47*1.01)
check(3<vmin<vnom<vmax<3.6,'Static feedback/reference tolerance range remains within MCU/CAN supply limits')
check(adc<3,'ADC divider worst 1% tolerance at 65 V protected input stays below 3 V; not a sustained input rating')
report={'revision':'D','board_mm':[150,150],'checks_passed':len(checks),'factory_refs':sorted(factory),'factory_count':4,'hand_count':37,'bare_testpoints':7,'mounting_holes':4,
 'component_count':41,'unique_mpns':len({q['mpn'] for q in parts}),'preserved_critical_copper_items':len(bt),
 'ground_vias':sum(t.GetNetname()=='/GND' for t in vias),'tracks_per_layer':dict(collections.Counter(b.GetLayerName(t.GetLayer()) for t in tracks)),
 'dc_estimates':{'output_nominal_V':vnom,'output_static_min_V':vmin,'output_static_max_V':vmax,'adc_at_65V_V':adc},
 'board_sha256':hashlib.sha256((H/'leaf-heat-v4.kicad_pcb').read_bytes()).hexdigest(),
 'schematic_sha256':hashlib.sha256((H/'leaf-heat-v4.kicad_sch').read_bytes()).hexdigest(),
 'limitations':'CAD and static checks only: physical assembly, thermal, startup, ripple, UART, Wi-Fi, EMC/transients, parked current and vehicle operation remain untested.',
 'checks':checks}
(E/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))

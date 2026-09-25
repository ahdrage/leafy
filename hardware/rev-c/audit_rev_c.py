"""Independent saved-file electrical, geometry, and preservation checks.

This audit reads the native schematic netlist, PCB, and purchasing metadata.
It does not import the generation script or rely on ERC alone.
"""
from pathlib import Path
import collections, hashlib, json, math, xml.etree.ElementTree as ET
import pcbnew as p
import heapq

H=Path(__file__).resolve().parent; B=H.parent/'rev-b'
def xy(q): return (p.ToMM(q.x),p.ToMM(q.y))
def v(q): return p.VECTOR2I(*(p.FromMM(x) for x in q))
def check(ok,message):
    if not ok: raise AssertionError(message)
    checks.append(message)
checks=[]
baseline=json.loads((H/'exports/baseline-sha256.json').read_text())
check(all(hashlib.sha256((B/name).read_bytes()).hexdigest()==sha for name,sha in baseline.items()),'Rev B native project files remain byte-for-byte unchanged')
b=p.LoadBoard(str(H/'leaf-heat-v3.kicad_pcb'))
old=p.LoadBoard(str(B/'leaf-heat-v2.kicad_pcb'))
parts=json.loads((H/'parts.json').read_text()); oldparts=json.loads((B/'parts.json').read_text())
metadata={q['ref']:q for q in parts}; oldmeta={q['ref']:q for q in oldparts}
fps={f.GetReference():f for f in b.GetFootprints()}; oldfps={f.GetReference():f for f in old.GetFootprints()}
removed={'J2','D2','D5','R11','R12','R13','R14','R15','R16','R17'}
added={'J3','R18','R19','R20'}
check(set(metadata)==(set(oldmeta)-removed)|added,'Exactly the intended ten removals and four additions are populated')
check(len(parts)==41 and len({q['mpn'] for q in parts})==25,'BOM has 41 components and 25 unique manufacturer parts')
check(set(fps)==set(metadata)|{'H1','H2','H3'},'PCB population matches BOM; only the three mounting holes are excluded')
check(all(q['mpn'] and q['manufacturer'] for q in parts),'Every populated component has manufacturer and exact part number')
nr=ET.parse(H/'exports/leaf-heat-v3.net.xml').getroot()
pinmap={}; netmap=collections.defaultdict(set)
for n in nr.findall('./nets/net'):
    for node in n.findall('node'):
        key=(node.get('ref'),node.get('pin'));pinmap[key]=n.get('name');netmap[n.get('name')].add(key)
def net(ref,pin): return pinmap[(ref,str(pin))].lstrip('/')
for q in parts:
    for pin,n in q['nets'].items():
        if n is not None:
            # USB-C grouped contacts are gone; all current net entries correspond
            # to explicit schematic pins, including the DB9 shell.
            check(net(q['ref'],pin)==n,f"Schematic pin {q['ref']}.{pin} = {n}")
    for pad in fps[q['ref']].Pads():
        if pad.GetNumber():
            check(pad.GetNetname()==pinmap.get((q['ref'],pad.GetNumber())),f"PCB pad {q['ref']}.{pad.GetNumber()} matches exported schematic")
    check(fps[q['ref']].GetFieldText('MPN')==q['mpn'],f"PCB MPN for {q['ref']} matches purchasing list")
unchanged=set(oldmeta)-removed-{'U2','U4','C14'}
for ref in unchanged:
    for key in ['nets','mpn','value','footprint']:
        check(metadata[ref][key]==oldmeta[ref][key],f"Preserved {ref} {key}")
    check(xy(fps[ref].GetPosition())==xy(oldfps[ref].GetPosition()) and fps[ref].GetOrientationDegrees()==oldfps[ref].GetOrientationDegrees(),f"Preserved {ref} physical placement")
for pin in ['1','2','3','4','5','6','7','8','9','10','16','17','18','19']:
    check(metadata['U2']['nets'][pin]==oldmeta['U2']['nets'][pin],f"Preserved controller pin {pin}")
expected={('U2','11'):'UART_RX',('U2','12'):'UART_TX',('J3','1'):'GND',('J3','2'):'PROG_RX',('J3','3'):'PROG_TX',
 ('R18','1'):'UART_TX',('R18','2'):'PROG_TX',('R19','1'):'PROG_RX',('R19','2'):'UART_RX',('R20','1'):'3V3',('R20','2'):'UART_RX',
 ('U4','1'):'PROG_RX',('U4','6'):'PROG_RX',('U4','3'):'PROG_TX',('U4','4'):'PROG_TX',('U4','2'):'GND',('U4','5'):'3V3',
 ('C14','1'):'3V3',('C14','2'):'GND'}
check(all(net(*k)==value for k,value in expected.items()),'Independent UART/ESD pin map matches component datasheets and intended adapter direction')
check(all(net('U2',n).startswith('unconnected-') for n in [13,14,15]),'Former USB data and sense pins are explicitly unconnected')
check(all(not name.startswith('/USB') and name not in ['/CC1','/CC2'] for name in netmap),'No USB data, supply, CC, or detection nets remain')
check({net('J3',n) for n in [1,2,3]}=={'GND','PROG_RX','PROG_TX'},'Programming connector exposes no power rail')
check(net('SW1',1)=='ESP_EN' and net('SW1',2)=='GND' and net('SW2',1)=='BOOT_IO9' and net('SW2',2)=='GND','Manual reset/download controls retained')
check(all(net(r,1)=='3V3' and metadata[r]['mpn']=='RC0603FR-0710KL' for r in ['R3','R4','R5','R6','R10','R20']),'Enable, boot straps, CAN standby and UART idle have external 10k pull-ups')
check(net('J1',9)=='CAR_12V' and net('F1',1)=='CAR_12V' and net('F1',2)=='CAR_FUSED' and net('D1',2)=='CAR_FUSED' and net('D1',1)=='VPWR','Vehicle/bench input passes through fuse then reverse-blocking diode')
check(net('J1',7)=='CAN_H' and net('J1',2)=='CAN_L' and net('J1',3)=='GND','DB9 vehicle pinout remains 9 power / 3 ground / 7 H / 2 L')
check(not any({q['nets'].get('1'),q['nets'].get('2')}=={'CAN_H','CAN_L'} and q['ref'].startswith('R') for q in parts),'No extra CAN bus termination added')
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
oldtracks={t.m_Uuid.AsString():t for t in old.GetTracks()}
preserved=0
for t in b.GetTracks():
    ot=oldtracks.get(t.m_Uuid.AsString())
    if ot:
        check(t.GetNetname()==ot.GetNetname(),'Surviving original copper keeps its original net '+t.m_Uuid.AsString())
        check(xy(t.GetStart())==xy(ot.GetStart()) and xy(t.GetEnd())==xy(ot.GetEnd()),'Surviving original route geometry is unchanged '+t.m_Uuid.AsString())
        preserved+=1
check(b.GetCopperLayerCount()==4,'Four copper layers retained')
check(not any(t.GetLayer() in [p.In1_Cu,p.In2_Cu] for t in tracks),'Neither internal copper layer has routed tracks')
gnd=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='/GND' and z.GetLayer()==p.In1_Cu]
check(len(gnd)==1,'Dedicated In1.Cu ground plane retained')
antenna=[]
for x in range(35,62):
 for y in [.35,.6,.85]:
  for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
   if any(z.GetLayer()==layer and not z.GetIsRuleArea() and z.HitTestFilledArea(layer,v((x,y))) for z in b.Zones()):antenna.append((x,y,layer))
check(not antenna,'No filled copper beneath the antenna overhang on any copper layer')
uart={'/UART_RX','/UART_TX','/PROG_RX','/PROG_TX'}
miss=[];samples=0
for t in tracks:
 if t.GetNetname() not in uart or t.GetLayer()!=p.F_Cu:continue
 a,c=xy(t.GetStart()),xy(t.GetEnd());L=math.dist(a,c)
 for i in range(max(1,math.ceil(L/.1))+1):
  q=(a[0]+(c[0]-a[0])*i/max(1,math.ceil(L/.1)),a[1]+(c[1]-a[1])*i/max(1,math.ceil(L/.1)))
  samples+=1
  if not gnd[0].HitTestFilledArea(p.In1_Cu,v(q)):
   # Non-ground through holes have intentional plane clearances.
   near_via=any(math.dist(q,xy(t.GetPosition()))<.55 for t in vias if t.GetNetname()!='/GND')
   near_pad=any(pad.GetAttribute()==p.PAD_ATTRIB_PTH and pad.GetNetname()!='/GND' and math.dist(q,xy(pad.GetPosition()))<max(xy(pad.GetSize()))/2+.21 for f in fps.values() for pad in f.Pads())
   if not near_via and not near_pad:miss.append(q)
check(not miss,'Top UART routing has adjacent ground except intentional plated-hole clearances')
def padxy(ref,num):return xy(next(x for x in fps[ref].Pads() if x.GetNumber()==str(num)).GetPosition())
def copper_distance(name,start,end):
    graph=collections.defaultdict(list)
    def pt(q):return tuple(round(x,6) for x in q)
    for t in tracks:
        if t.GetNetname()!=name:continue
        a,c=pt(xy(t.GetStart())),pt(xy(t.GetEnd()));length=p.ToMM(t.GetLength())
        graph[a].append((c,length));graph[c].append((a,length))
    queue=[(0,pt(start))];seen=set()
    while queue:
        distance,at=heapq.heappop(queue)
        if at==pt(end):return distance
        if at in seen:continue
        seen.add(at)
        for q,length in graph[at]:heapq.heappush(queue,(distance+length,q))
    raise AssertionError('Missing expected copper path')
esd_paths={n:copper_distance('/PROG_'+n,padxy('J3',j),padxy('U4',u)) for n,j,u in [('RX',2,1),('TX',3,3)]}
check(all(x<3.1 for x in esd_paths.values()),'Both header-to-ESD copper paths are approximately 3 mm')
header=sorted(fps['J3'].Pads(),key=lambda x:x.GetNumber())
check([x.GetNumber() for x in header]==['1','2','3'],'Header has exactly three numbered contacts')
check(all(abs(math.dist(xy(a.GetPosition()),xy(c.GetPosition()))-2.54)<1e-6 for a,c in zip(header,header[1:])),'Header pitch is 2.54 mm')
check(all(xy(a.GetDrillSize())==(1.,1.) for a in header),'Header holes are 1.00 mm for 0.64 mm square contacts')
check(all(f.GetLayer()==p.F_Cu for f in fps.values()),'All populated components mount on top')
check(all(fps[r].GetAttributes() & p.FP_SMD for r in ['U1','U2','U3','U4']),'Integrated circuits are correctly classified for surface-mount assembly')
check(fps['J3'].GetLocalZoneConnection()==p.ZONE_CONNECTION_THERMAL,'Programming header uses solderable ground thermal reliefs')
settings=json.loads((H/'leaf-heat-v3.kicad_pro').read_text())
check(not settings['board']['design_settings']['drc_exclusions'],'No DRC exclusions are present')
check(all(x['name']!='USB' for x in settings['net_settings']['classes']),'Obsolete USB net class removed')
check('USB' not in (H/'leaf-heat-v3.kicad_dru').read_text(),'Obsolete differential impedance rules removed')
# Independent corner calculations; these are static calculations, not measurements.
vnom=1+100/43.2
vmin=.985*(1+100*.99/(43.2*1.01));vmax=1.015*(1+100*1.01/(43.2*.99))
check(3.0<vmin<vnom<vmax<3.6,'Feedback-reference and 1% resistor corner voltages stay within ESP32/CAN supply range')
adc_at_65=65*(47*1.01)/(1000*.99+47*1.01)
check(adc_at_65<3.0,'Battery divider worst 1% corner remains below 3.0 V at 65 V protected-input voltage')
rx_low=(.4/1010+vmax/9900)/(1/1010+1/9900)
check(rx_low<.25*vmin,'RX low-level margin holds with a 0.4 V adapter low and worst resistor/supply corners')
rc_us=1010*100e-12*1e6
check(2.2*rc_us<.1*(1e6/115200),'With 100 pF total cable/input load, estimated UART edge time is under 10% of a bit at 115200 baud')
report={'board':'leaf-heat-v3','checks_passed':len(checks),'component_count':len(parts),'unique_mpns':len({q['mpn'] for q in parts}),
 'removed_references':sorted(removed),'added_references':sorted(added),'modified_circuits':['U2 UART connections','U4 UART ESD wiring/placement','C14 100nF UART ESD bypass'],
 'preserved_original_copper_items':preserved,'tracks_per_layer':dict(collections.Counter(b.GetLayerName(t.GetLayer()) for t in tracks)),
 'ground_through_vias':sum(t.GetNetname()=='/GND' for t in vias),'uart_top_ground_samples':samples,'unexplained_ground_gaps':miss,'header_to_esd_copper_mm':esd_paths,
 'dc_calculations':{'output_nominal_V':vnom,'output_min_V':vmin,'output_max_V':vmax,'adc_at_65V_worst_V':adc_at_65,'uart_rx_low_worst_V':rx_low,'uart_estimated_10_90_rise_us_at_100pF':2.2*rc_us},
 'limitations':'Saved-file and static arithmetic checks only. No physical, transient, thermal, EMC, firmware, or vehicle validation implied. UART margin assumes compliant 3.3 V adapter and total load <=100 pF.',
 'checks':checks}
(H/'exports/independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))

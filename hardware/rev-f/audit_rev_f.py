"""Independent circuit, regression and manufacturing checks of final Rev F.

Does not import the board generator. An explicit datasheet pin map is checked
in both native representations, along with the narrowly allowed Rev E delta.
"""
from pathlib import Path
import collections
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
import pcbnew as p
import sexpdata as sx

H = Path(__file__).resolve().parent
E = H / 'exports'
OLD = H.parent / 'rev-e'
checks = []
def check(ok, description):
    checks.append({'check': description, 'pass': bool(ok)})
def sha(q): return hashlib.sha256(q.read_bytes()).hexdigest()
def xy(v): return (round(p.ToMM(v.x), 6), round(p.ToMM(v.y), 6))
def norm(n): return None if not n or n.startswith('unconnected-') else n.lstrip('/')
def pins(path):
    root = ET.parse(path).getroot()
    result = {(q.get('ref'), q.get('pin')): norm(n.get('name'))
              for n in root.findall('./nets/net') for q in n.findall('node')}
    return root, result

# Manufacturer pin functions, with the intentional Rev F SHDN connection.
expected = {
 'J1': dict(zip(['1','2','3','4','5','6','7','8','9','SH'],
               [None,'CAN_L','GND',None,None,None,'CAN_H',None,'CAR_12V','GND'])),
 'J3': {'1':'GND','2':'PROG_RX','3':'PROG_TX'},
 'U1': dict(zip(map(str,range(1,10)),
               ['GND','VPWR','VPWR',None,'BUCK_FB','BUCK_VCC','BUCK_BOOT','BUCK_SW','GND'])),
 'U2': dict(zip(map(str,range(1,20)),
               ['3V3','ESP_EN','CAN_TX','CAN_RX',None,'STATUS_LED','BOOT_IO8','BOOT_IO9',
                'GND',None,'UART_RX','UART_TX',None,None,None,'BOOT_IO2','CAN_STB','BAT_SENSE','GND'])),
 'U3': dict(zip(map(str,range(1,9)),
               ['CAN_TX','GND','3V3','CAN_RX','GND','CAN_L','CAN_H','CAN_STB'])),
 'U4': dict(zip(map(str,range(1,7)),['PROG_RX','GND','PROG_TX','PROG_TX','3V3','PROG_RX'])),
 'D4': {'1':'CAN_L','2':'CAN_H','3':'GND'},
}
two = {
 'F1':('CAR_12V','CAR_FUSED'), 'D1':('VPWR','CAR_FUSED'), 'D3':('VPWR','GND'),
 'L1':('BUCK_SW','3V3'), 'C1':('VPWR','GND'), 'C2':('VPWR','GND'),
 'C3':('BUCK_VCC','GND'), 'C4':('BUCK_BOOT','BUCK_SW'),
 'R1':('3V3','BUCK_FB'), 'R2':('BUCK_FB','GND'), 'R3':('3V3','ESP_EN'),
 'C8':('ESP_EN','GND'), 'R4':('3V3','BOOT_IO2'), 'R5':('3V3','BOOT_IO8'),
 'R6':('3V3','BOOT_IO9'), 'SW1':('ESP_EN','GND'), 'SW2':('BOOT_IO9','GND'),
 'R7':('VPWR','BAT_SENSE'), 'R8':('BAT_SENSE','GND'), 'C11':('BAT_SENSE','GND'),
 'R9':('STATUS_LED','LED_A'), 'D6':('GND','LED_A'), 'R10':('3V3','CAN_STB'),
 'R18':('UART_TX','PROG_TX'), 'R19':('PROG_RX','UART_RX'), 'R20':('3V3','UART_RX'),
}
for ref in ['C5','C6','C7','C9','C10','C12','C13','C14']: two[ref] = ('3V3','GND')
for ref, nets in two.items(): expected[ref] = dict(zip(['1','2'],nets))
for i,n in enumerate(['GND','CAR_12V','VPWR','3V3','CAN_H','CAN_L','ESP_EN'],1):
    expected['TP'+str(i)] = {'1':n}

root, schematic = pins(E / 'leaf-heat-v6.net.xml')
_, previous = pins(OLD / 'exports/leaf-heat-v5.net.xml')
b = p.LoadBoard(str(H / 'leaf-heat-v6.kicad_pcb'))
old_b = p.LoadBoard(str(OLD / 'leaf-heat-v5.kicad_pcb'))
fps = {f.GetReference():f for f in b.GetFootprints()}
old_fps = {f.GetReference():f for f in old_b.GetFootprints()}
parts = {q['ref']:q for q in json.loads((H / 'parts.json').read_text())}
old_parts = {q['ref']:q for q in json.loads((OLD / 'parts.json').read_text())}
check(set(fps)==set(expected)|{'H1','H2','H3','H4'}, 'All circuit parts and bare features accounted for')
check(set(parts)==set(old_parts) and len(parts)==41, 'All 41 circuit components retained')
check(set(schematic)==set(previous), 'Schematic pin membership unchanged')
delta = {k:(previous[k],schematic[k]) for k in schematic if k in previous and previous[k]!=schematic[k]}
check(delta=={('U3','5'):('3V3','GND')}, 'Only electrical net change is U3.5: 3V3 to GND')
for ref, pinmap in expected.items():
    f = fps[ref]
    check({q.GetNumber() for q in f.Pads() if q.GetNumber()}==set(pinmap), ref+' package pin numbers')
    for num, net in pinmap.items():
        check((ref,num) in schematic and schematic[(ref,num)]==net, ref+'.'+num+' schematic pin map')
        check(all(norm(q.GetNetname())==net for q in f.Pads() if q.GetNumber()==num), ref+'.'+num+' PCB pin map')
check(next(q for q in fps['U3'].Pads() if q.GetNumber()=='5').GetPinType()=='input', 'SHDN represented as a digital input')

allowed_mpns = {'U3':'TCAN3404DRQ1','J1':'182-009-113R561',
                'C5':'C1210C226K3RAC7210','C6':'C1210C226K3RAC7210','C7':'C1210C226K3RAC7210'}
components = {q.get('ref'):q for q in root.findall('./components/comp')}
factory = {'U1':'LMR36510ADDAR','U2':'ESP32-C3-WROOM-02-N4','U4':'USBLC6-2SC6','L1':'SRN6045TA-220M'}
check({r for r,q in parts.items() if q['assembly']=='FACTORY'}==set(factory), 'Four factory parts retained')
for ref, q in parts.items():
    f = fps[ref]
    check(q['mpn']==allowed_mpns.get(ref,old_parts[ref]['mpn']), ref+' exact approved part number')
    fields = {v.get('name'):v.text for v in components[ref].findall('./fields/field')}
    check(fields['MPN']==q['mpn']==f.GetFieldText('MPN'), ref+' MPN agrees across schematic/PCB/BOM')
    check(fields['Manufacturer']==q['manufacturer']==f.GetFieldText('Manufacturer'), ref+' manufacturer agrees')
    check(components[ref].findtext('value')==q['value']==f.GetValue(), ref+' value agrees')
    check(str(f.GetFPID().GetLibNickname())+':'+str(f.GetFPID().GetLibItemName())==q['footprint'],ref+' footprint agrees')
    check(f.GetFieldText('Assembly')==q['assembly'],ref+' assembly ownership agrees')
    if q['assembly']=='HAND':
        check(f.GetLocalZoneConnection()==p.ZONE_CONNECTION_THERMAL,ref+' thermal reliefs retained')
        check(all(p.F_Paste not in z.GetLayerSet().Seq() and p.B_Paste not in z.GetLayerSet().Seq() for z in f.Pads()),ref+' has no factory stencil apertures')

def pad_geometry(f):
    return sorted((q.GetNumber(),xy(q.GetPosition()),xy(q.GetSize()),xy(q.GetDrillSize()),
                   int(q.GetShape()),int(q.GetAttribute()),round(q.GetOrientationDegrees(),6),
                   tuple(q.GetLayerSet().Seq())) for q in f.Pads())
for ref, f in fps.items():
    check(xy(f.GetPosition())==xy(old_fps[ref].GetPosition()) and
          f.GetOrientationDegrees()==old_fps[ref].GetOrientationDegrees(), ref+' location/orientation retained')
    check(pad_geometry(f)==pad_geometry(old_fps[ref]),ref+' all pad/drill geometry retained')
    check(f.GetLayer()==p.F_Cu,ref+' top-side assembly')
# Independent manufacturer-pattern dimensions, not just matching the old board.
j = fps['J1'];jp={q.GetNumber():q for q in j.Pads() if q.GetNumber()!='SH'}
check(all(abs(xy(jp[str(i+1)].GetPosition())[0]-xy(jp[str(i)].GetPosition())[0]-2.77)<1e-5 for i in range(1,5)), 'NorComp 2.77 mm column pitch')
check(abs(xy(jp['6'].GetPosition())[1]-xy(jp['1'].GetPosition())[1]-2.84)<1e-5, 'NorComp 2.84 mm row pitch')
anchors=[q for q in j.Pads() if q.GetNumber()=='SH']
check(abs(abs(xy(anchors[0].GetPosition())[0]-xy(anchors[1].GetPosition())[0])-24.99)<1e-5, 'NorComp 24.99 mm anchor spacing')
check(all(xy(q.GetDrillSize())==(3.2,3.2) for q in anchors), 'NorComp 3.2 mm fork-boardlock holes')
check(all(xy(q.GetDrillSize())==(1.2,1.2) for q in jp.values()), 'NorComp 1.2 mm contact holes')

# Every signal and critical power route outside the explicitly reviewed delta
# must remain identical to Rev E. UUIDs are fixed evidence, not generator data.
removed={'243053fc-629b-45c1-bffd-34a2012ad1f7','919d2525-9790-49f4-a8cd-d172c1a4fce9','e4352eb1-c995-4b55-932a-45f484173721'}
regrounded={'b0a7b973-c068-4f43-b110-33e82b02df7d','07170d68-d4c3-413c-a34c-8b5e1a07d958'}
before={q.m_Uuid.AsString():q for q in old_b.GetTracks()}
after={q.m_Uuid.AsString():q for q in b.GetTracks()}
check(set(before)-set(after)==removed and not set(after)-set(before), 'Exactly three obsolete VIO branch segments removed; no unrelated copper additions/deletions')
for uid, t in after.items():
    old=before[uid]
    geom=type(t)==type(old) and xy(t.GetStart())==xy(old.GetStart()) and xy(t.GetEnd())==xy(old.GetEnd())
    if isinstance(t,p.PCB_VIA):
        geom=geom and t.GetDrill()==old.GetDrill() and all(t.GetWidth(l)==old.GetWidth(l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu])
    else: geom=geom and t.GetLayer()==old.GetLayer() and t.GetWidth()==old.GetWidth()
    check(geom, 'Copper geometry retained '+uid)
    check(t.GetNetname()==('/GND' if uid in regrounded else old.GetNetname()),'Copper net checked '+uid)
check(b.GetCopperLayerCount()==4,'Four copper layers')
check(xy(b.GetDesignSettings().GetAuxOrigin())==(0,100),'Lower-left fabrication origin')
check({xy(v) for q in b.GetDrawings() if q.GetLayer()==p.Edge_Cuts for v in [q.GetStart(),q.GetEnd()]}=={(0,0),(100,0),(100,100),(0,100)},'100 x 100 mm outline')
check(not any(not isinstance(t,p.PCB_VIA) and t.GetLayer() in [p.In1_Cu,p.In2_Cu] for t in after.values()),'No tracks interrupt the inner plane layers')
check(sum(z.GetLayer()==p.In1_Cu and z.GetNetname()=='/GND' and not z.GetIsRuleArea() for z in b.Zones())==1,'Dedicated inner ground plane retained')

def zone_defs(path):
    tree=sx.load(open(path))
    return [sx.dumps([c for c in z if not(isinstance(c,list) and c and str(c[0]) in {'filled_polygon','fill_segments'})])
            for z in tree if isinstance(z,list) and z and str(z[0])=='zone']
check(zone_defs(H/'leaf-heat-v6.kicad_pcb')==zone_defs(OLD/'leaf-heat-v5.kicad_pcb'),'Plane outlines, nets, clearances and thermal rules retained')
for x in [59.1,65,75,85,86.9]:
    for y in [.4,.6,.8]:
        point=p.VECTOR2I(p.FromMM(x),p.FromMM(y))
        check(not any(not z.GetIsRuleArea() and z.HitTestFilledArea(z.GetLayer(),point) for z in b.Zones()),'Antenna clearance sample '+str((x,y)))
check(any(z.GetIsRuleArea() and {p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu}.issubset(set(z.GetLayerSet().Seq())) for z in fps['U2'].Zones()),'Antenna keepout applies to all copper layers')
check(not any(r.startswith('R') and {q['nets'].get('1'),q['nets'].get('2')}=={'CAN_H','CAN_L'} for r,q in parts.items()),'No CAN termination added')
check(parts['R10']['mpn']=='RC1206FR-0710KL' and expected['R10']=={'1':'3V3','2':'CAN_STB'},'Reset-safe CAN standby pull-up retained')

for name in ['BOM-FACTORY-PCBWay.csv','BOM-FACTORY-JLCPCB.csv']:
    rows=list(csv.DictReader((E/name).open()))
    check(len(rows)==4 and {q['Designator']:q['Manufacturer Part Number'] for q in rows}==factory,name+' exact factory membership')
for row in csv.DictReader((E/'CPL-FACTORY-JLCPCB.csv').open()):
    f=fps[row['Designator']]
    check(abs(float(row['Mid X'])-xy(f.GetPosition())[0])<1e-6 and abs(float(row['Mid Y'])-(100-xy(f.GetPosition())[1]))<1e-6 and
          abs(float(row['Rotation'])-f.GetOrientationDegrees())<1e-6 and row['Layer']=='Top',row['Designator']+' placement coordinate check')
hand=list(csv.DictReader((E/'BOM-HAND.csv').open()))
refs=[r for q in hand for r in q['References'].split(',')]
check(len(refs)==len(set(refs))==37 and set(refs)==set(parts)-set(factory),'Hand BOM covers every remaining part once')
check(len(hand)==21,'21 hand-shopping lines')
for row in hand:
    rr=row['References'].split(',')
    check(int(row['Qty for ONE board'])==len(rr) and int(row['Qty for TWO boards'])==2*len(rr),row['References']+' quantities')
    check(all(parts[r]['mpn']==row['MPN'] for r in rr),row['References']+' purchasing MPN')
paste={r for r,f in fps.items() if any(p.F_Paste in q.GetLayerSet().Seq() for q in f.Pads())}
check(paste==set(factory),'Stencil includes exactly four factory components')
manufacturing=json.loads((E/'manufacturing-audit.json').read_text())
check(manufacturing['board_sha256']==sha(H/'leaf-heat-v6.kicad_pcb'),'Exports belong to current PCB')
for name,digest in manufacturing['fabrication_files'].items():check(sha(E/'fabrication'/name)==digest,name+' export hash')
drc=json.loads((E/'drc-final.json').read_text())
check(all(not drc[k] for k in ['violations','unconnected_items','schematic_parity']),'KiCad DRC/connectivity/schematic parity pass')
erc=json.loads((E/'erc.json').read_text())
check(not any(q.get('violations') for q in erc.get('sheets',[])),'KiCad ERC passes')
settings=json.loads((H/'leaf-heat-v6.kicad_pro').read_text())
old_settings=json.loads((OLD/'leaf-heat-v5.kicad_pro').read_text())
check(settings['board']['design_settings']==old_settings['board']['design_settings'],'Design-rule settings unchanged; no new waivers')
check(not settings['board']['design_settings']['drc_exclusions'],'No individual DRC exclusions')
baseline=json.loads((E/'baseline-rev-e-sha256.json').read_text())
check(all(sha(OLD/n)==digest for n,digest in baseline.items()),'Source Rev E preserved byte-for-byte')

failed=[q['check'] for q in checks if not q['pass']]
report={'revision':'F','board_sha256':sha(H/'leaf-heat-v6.kicad_pcb'),'schematic_sha256':sha(H/'leaf-heat-v6.kicad_sch'),
        'factory_refs':sorted(factory),'hand_count':37,'component_count':41,'hand_bom_lines':21,
        'checks_passed':len(checks)-len(failed),'failed':failed,
        'electrical_delta':{'U3.5':['3V3','GND']},
        'limitations':'Static CAD and manufacturer-data review only. Physical power integrity, loop stability, RF, CAN, vehicle operation, EMI and environmental performance remain untested. No heater firmware supplied.',
        'checks':checks}
(E/'independent-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
raise SystemExit(bool(failed))

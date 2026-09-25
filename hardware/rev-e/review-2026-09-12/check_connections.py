"""Read-only review of native CAD against an explicitly reviewed circuit pin map.

Run with the KiCad Python environment. Does not import the board generator or
compare to a previous revision. This is static verification, not a functional test.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import xml.etree.ElementTree as ET
import zipfile
import pcbnew as p

HERE = Path(__file__).resolve().parent
BOARD_DIR = HERE.parent
EXPORTS = BOARD_DIR / 'exports'
results = []


def check(condition, description):
    results.append({'check': description, 'pass': bool(condition)})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(name):
    return None if not name or name.startswith('unconnected-') else name.lstrip('/')


# Independently transcribed from reviewed datasheet functions and circuit intent.
# U1: TI LMR36510 section 5; U2: Espressif module Table 3-1;
# U3: TI TCAN3403-Q1 Table 5-1; U4: ST USBLC6-2 Figure 1.
expected = {
    'J1': dict(zip(['1','2','3','4','5','6','7','8','9','SH'],
                   [None,'CAN_L','GND',None,None,None,'CAN_H',None,'CAR_12V','GND'])),
    'J3': {'1':'GND','2':'PROG_RX','3':'PROG_TX'},
    'U1': dict(zip(map(str,range(1,10)),
                   ['GND','VPWR','VPWR',None,'BUCK_FB','BUCK_VCC','BUCK_BOOT','BUCK_SW','GND'])),
    'U2': dict(zip(map(str,range(1,20)),
                   ['3V3','ESP_EN','CAN_TX','CAN_RX',None,'STATUS_LED','BOOT_IO8',
                    'BOOT_IO9','GND',None,'UART_RX','UART_TX',None,None,None,
                    'BOOT_IO2','CAN_STB','BAT_SENSE','GND'])),
    'U3': dict(zip(map(str,range(1,9)),
                   ['CAN_TX','GND','3V3','CAN_RX','3V3','CAN_L','CAN_H','CAN_STB'])),
    'U4': dict(zip(map(str,range(1,7)),
                   ['PROG_RX','GND','PROG_TX','PROG_TX','3V3','PROG_RX'])),
    'D4': {'1':'CAN_L','2':'CAN_H','3':'GND'},
}
two_terminal = {
    'F1':('CAR_12V','CAR_FUSED'), 'D1':('VPWR','CAR_FUSED'),
    'D3':('VPWR','GND'), 'L1':('BUCK_SW','3V3'),
    'C1':('VPWR','GND'), 'C2':('VPWR','GND'), 'C3':('BUCK_VCC','GND'),
    'C4':('BUCK_BOOT','BUCK_SW'),
    'R1':('3V3','BUCK_FB'), 'R2':('BUCK_FB','GND'),
    'R3':('3V3','ESP_EN'), 'C8':('ESP_EN','GND'),
    'R4':('3V3','BOOT_IO2'), 'R5':('3V3','BOOT_IO8'), 'R6':('3V3','BOOT_IO9'),
    'SW1':('ESP_EN','GND'), 'SW2':('BOOT_IO9','GND'),
    'R7':('VPWR','BAT_SENSE'), 'R8':('BAT_SENSE','GND'), 'C11':('BAT_SENSE','GND'),
    'R9':('STATUS_LED','LED_A'), 'D6':('GND','LED_A'),
    'R10':('3V3','CAN_STB'), 'R18':('UART_TX','PROG_TX'),
    'R19':('PROG_RX','UART_RX'), 'R20':('3V3','UART_RX'),
}
for ref in ['C5','C6','C7','C9','C10','C12','C13','C14']:
    two_terminal[ref] = ('3V3','GND')
for ref, nets in two_terminal.items():
    expected[ref] = dict(zip(['1','2'], nets))
for i, name in enumerate(['GND','CAR_12V','VPWR','3V3','CAN_H','CAN_L','ESP_EN'],1):
    expected[f'TP{i}'] = {'1':name}

root = ET.parse(HERE/'netlist-fresh.xml').getroot()
schematic_pins = {}
for net in root.findall('./nets/net'):
    for node in net.findall('node'):
        schematic_pins[(node.get('ref'),node.get('pin'))] = norm(net.get('name'))
board = p.LoadBoard(str(BOARD_DIR/'leaf-heat-v5.kicad_pcb'))
footprints = {f.GetReference():f for f in board.GetFootprints()}
check(set(footprints) == set(expected)|{'H1','H2','H3','H4'}, 'All 41 circuit parts, 7 test holes and 4 mounting holes accounted for')
for ref, pins in expected.items():
    fp = footprints[ref]
    check({pad.GetNumber() for pad in fp.Pads() if pad.GetNumber()} == set(pins), ref+' physical pad numbers match reviewed pin map')
    for num, net in pins.items():
        check((ref,num) in schematic_pins and schematic_pins[(ref,num)] == net,
              f'{ref}.{num} schematic connection = {net or "intentional NC"}')
        matching = [pad for pad in fp.Pads() if pad.GetNumber()==num]
        check(bool(matching) and all(norm(pad.GetNetname())==net for pad in matching),
              f'{ref}.{num} all physical pads connected to {net or "intentional NC"}')

parts = {part['ref']:part for part in json.loads((BOARD_DIR/'parts.json').read_text())}
check(parts['D1']['mpn']=='B1100-13-F' and parts['D1']['manufacturer']=='Diodes Incorporated', 'D1 uses the manufacturer-verified SMA ordering code')
components = {comp.get('ref'):comp for comp in root.findall('./components/comp')}
for ref, part in parts.items():
    fields = {f.get('name'):f.text for f in components[ref].findall('./fields/field')}
    check(fields.get('MPN')==part['mpn']==footprints[ref].GetFieldText('MPN'), ref+' exact MPN agrees in schematic, PCB and part list')
    check(components[ref].findtext('value')==part['value']==footprints[ref].GetValue(), ref+' value agrees across files')
factory = {'U1':'LMR36510ADDAR','U2':'ESP32-C3-WROOM-02-N4','U4':'USBLC6-2SC6','L1':'SRN6045TA-220M'}
check({ref for ref,part in parts.items() if part['assembly']=='FACTORY'}==set(factory), 'Exactly four intended factory placements')
for filename in ['BOM-FACTORY-PCBWay.csv','BOM-FACTORY-JLCPCB.csv']:
    rows = list(csv.DictReader((EXPORTS/filename).open()))
    check(len(rows)==4 and {r['Designator']:r['Manufacturer Part Number'] for r in rows}==factory, filename+' exact factory MPNs')
hand = list(csv.DictReader((EXPORTS/'BOM-HAND.csv').open()))
refs = [ref for row in hand for ref in row['References'].split(',')]
check(len(refs)==len(set(refs))==37 and set(refs)==set(parts)-set(factory), 'Hand BOM includes every remaining part once')
for row in hand:
    check(int(row['Qty for ONE board'])==len(row['References'].split(',')) and
          int(row['Qty for TWO boards'])==2*int(row['Qty for ONE board']), row['References']+' hand quantity')
    check(all(parts[ref]['mpn']==row['MPN'] for ref in row['References'].split(',')), row['References']+' hand MPN')
paste_refs = {ref for ref,fp in footprints.items() if any(p.F_Paste in list(pad.GetLayerSet().Seq()) for pad in fp.Pads())}
check(paste_refs==set(factory), 'Top stencil contains only U1, U2, U4 and L1')
for row in csv.DictReader((EXPORTS/'CPL-FACTORY-JLCPCB.csv').open()):
    fp=footprints[row['Designator']]; pos=fp.GetPosition()
    check(abs(float(row['Mid X'])-p.ToMM(pos.x))<1e-6 and
          abs(float(row['Mid Y'])-(100-p.ToMM(pos.y)))<1e-6 and
          abs(float(row['Rotation'])-fp.GetOrientationDegrees())<1e-6 and row['Layer']=='Top',
          row['Designator']+' JLC placement equals native KiCad origin/rotation (vendor preview still required)')
manufacturing = json.loads((EXPORTS/'manufacturing-audit.json').read_text())
check(manufacturing['board_sha256']==sha(BOARD_DIR/'leaf-heat-v5.kicad_pcb'), 'Manufacturing export audit belongs to current PCB')
for name, digest in manufacturing['fabrication_files'].items():
    check(sha(EXPORTS/'fabrication'/name)==digest, name+' fabrication content matches audited export')
with zipfile.ZipFile(BOARD_DIR/'deliverables/leaf-heat-rev-e-gerbers.zip') as z:
    check(set(z.namelist())==set(manufacturing['fabrication_files']), 'Gerber ZIP has exactly audited fabrication files')
    check(all(z.read(name)==(EXPORTS/'fabrication'/name).read_bytes() for name in z.namelist()), 'Gerber ZIP content byte-identical to audited exports')
with zipfile.ZipFile(BOARD_DIR/'deliverables/leaf-heat-rev-e-factory-assembly.zip') as z:
    for name in ['BOM-FACTORY-PCBWay.csv','BOM-FACTORY-JLCPCB.csv','CPL-FACTORY-JLCPCB.csv','placements-FACTORY.csv']:
        check(z.read(name)==(EXPORTS/name).read_bytes(), name+' inside factory package matches current export')
    check(z.read('leaf-heat-rev-e-gerbers.zip')==(BOARD_DIR/'deliverables/leaf-heat-rev-e-gerbers.zip').read_bytes(), 'Factory package contains current Gerber archive')

for name in ['drc-fresh.json','erc-fresh.json']:
    report=json.loads((HERE/name).read_text())
    if name.startswith('drc'):
        for key in ['violations','unconnected_items','schematic_parity']:
            check(not report[key], 'Fresh native '+key+' empty')
    else:
        check(not any(sheet.get('violations') for sheet in report.get('sheets',[])), 'Fresh native ERC has no reported violations')

vout=1+100/43.2
calculations = {
    'vout_nominal_v':vout,
    'vout_static_ref_resistor_min_v':.985*(1+99/43.632),
    'vout_static_ref_resistor_max_v':1.015*(1+101/42.768),
    'vout_pfm_system_and_resistor_upper_estimate_v':1.025*(1+101/42.768),
    'battery_adc_nominal_at_vpwr_12v':12*47/(1000+47),
    'battery_adc_max_at_vpwr_65v_resistors_1pct':65*47.47/(990+47.47),
    'battery_adc_filter_time_constant_ms':(1e6*47e3/(1e6+47e3))*100e-9*1000,
    'reset_rc_time_constant_ms':1e4*1e-6*1000,
}
out={'date':'2026-09-12','kicad_version':p.GetBuildVersion(),
     'board_sha256':sha(BOARD_DIR/'leaf-heat-v5.kicad_pcb'),
     'schematic_sha256':sha(BOARD_DIR/'leaf-heat-v5.kicad_sch'),
     'scope':'Static pin-map, purchasing, assembly and fabrication consistency; no physical functional proof',
     'passed':sum(r['pass'] for r in results),'failed':[r for r in results if not r['pass']],
     'calculations':calculations,'checks':results}
(HERE/'connections-and-packages.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
raise SystemExit(bool(out['failed']))

"""Rebuild the Leaf Heat Rev A engineering prototype in native KiCad formats.

Run with KiCad's bundled Python (the project MCP venv includes it).
The exported schematic netlist is the authority for PCB net assignments.
"""
from pathlib import Path
from copy import deepcopy
import csv, json, math, subprocess, uuid, os
import sexpdata as sx
import pcbnew as pcb

HERE = Path(__file__).resolve().parent
LIB = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NAME = 'leaf-heat-v1'
os.environ['FONTCONFIG_FILE']=str(HERE/'fontconfig.xml')
S = sx.Symbol
def node(name,*args): return [S(name),*args]
def key(x,k): return isinstance(x,list) and len(x)>0 and str(x[0])==k
def child(x,k): return next((t for t in x if key(t,k)),None)
def children(x,k): return [t for t in x if key(t,k)]
def uid(tag): return str(uuid.uuid5(uuid.NAMESPACE_URL,'leaf-heat-reva/'+tag))
ROOT = uid('schematic')
def effects(size=1.0,hide=False,justify=None):
    t=node('effects',node('font',node('size',size,size)))
    if hide:t.append(node('hide',S('yes')))
    if justify:t.append(node('justify',S(justify)))
    return t
def prop(name,value,x,y,hide=False,size=1.0,angle=0,justify=None):
    return node('property',name,str(value),node('at',x,y,angle),effects(size,hide,justify))
cache={}
def get_symbol(lib,name):
    if lib not in cache:
        data=sx.load(open(LIB/'symbols'/f'{lib}.kicad_sym'))
        cache[lib]={t[1]:t for t in data if key(t,'symbol')}
    obj=deepcopy(cache[lib][name])
    ext=child(obj,'extends')
    if ext:
        parent=get_symbol(lib,ext[1]); parentname=parent[1]
        # Inherited graphical units plus this symbol's property overrides.
        units=children(parent,'symbol')
        for u in units:u[1]=u[1].replace(parentname+'_',name+'_',1)
        obj.remove(ext); obj.extend(units)
    return obj

def custom_ic(name,pins):
    obj=node('symbol',name,node('pin_names',node('offset',0.5)),
        node('in_bom',S('yes')),node('on_board',S('yes')),
        prop('Reference','U',0,12),prop('Value',name,0,9))
    body=node('symbol',name+'_0_1',node('rectangle',node('start',-10.16,7.62),node('end',10.16,-7.62),node('stroke',node('width',0.254),node('type',S('default'))),node('fill',node('type',S('background')))))
    unit=node('symbol',name+'_1_1')
    for num,label,typ,x,y,angle in pins:
        unit.append(node('pin',S(typ),S('line'),node('at',x,y,angle),node('length',2.54),node('name',label,effects()),node('number',str(num),effects())))
    obj.extend([body,unit]); return obj

custom={
 'TCAN3403DRQ1':custom_ic('TCAN3403DRQ1',[
 (1,'TXD','input',-12.7,5.08,0),(2,'GND','power_in',0,-10.16,90),
 (3,'VCC','power_in',-2.54,10.16,270),(4,'RXD','output',-12.7,0,0),
 (5,'VIO','power_in',2.54,10.16,270),(6,'CANL','bidirectional',12.7,-2.54,180),
 (7,'CANH','bidirectional',12.7,2.54,180),(8,'STB','input',-12.7,-5.08,0)]),
 'PESD2CAN':custom_ic('PESD2CAN',[(1,'CANL','passive',-12.7,2.54,0),(2,'CANH','passive',-12.7,-2.54,0),(3,'GND','passive',12.7,0,180)]),
 'USBLC6-2SC6':custom_ic('USBLC6-2SC6',[(1,'D+','passive',-12.7,2.54,0),(3,'D-','passive',-12.7,-2.54,0),(6,'D+','passive',12.7,2.54,180),(4,'D-','passive',12.7,-2.54,180),(5,'VBUS','passive',0,10.16,270),(2,'GND','passive',0,-10.16,90)])
}

parts=[]
def add(ref,libsym,value,fp,sch,xy,nets,mpn='',maker='',angle=0,rot=0,datasheet='',notes=''):
    parts.append(dict(ref=ref,symbol=libsym,value=value,footprint=fp,sch=list(sch),xy=list(xy),nets={str(k):v for k,v in nets.items()},mpn=mpn,manufacturer=maker,angle=angle,rotation=rot,datasheet=datasheet,notes=notes))
RFP='Resistor_SMD:R_0603_1608Metric'; CFP='Capacitor_SMD:C_0603_1608Metric'
def resistor(ref,value,sch,xy,a,b,mpn,angle=0,rot=0):
    add(ref,'Device:R',value,RFP,sch,xy,{1:a,2:b},mpn,'Yageo',angle,rot)
def cap(ref,value,sch,xy,a,b='GND',fp=CFP,mpn='',rot=0):
    add(ref,'Device:C',value,fp,sch,xy,{1:a,2:b},mpn,'Murata',rot=rot)

# Power input and 3.3 V buck. Values follow TI's 400 kHz, 3.3 V reference.
add('J1','Connector:DE9_Pins_MountingHoles','NISSAN LEAF CABLE','Leaf:NorComp_182-009-113R531',(38.1,55.88),(10,39),{1:None,2:'CAN_L',3:'GND',4:None,5:None,6:None,7:'CAN_H',8:None,9:'CAR_12V','SH':'GND'},'182-009-113R531','NorComp',datasheet='https://content.norcomp.net/rohspdfs/Connectors/18Y/182/182-yyy-113Ryy1.pdf',notes='Male DB9; only the specified Nissan OVMS cable pinout. Shell grounded. Mechanical mating review required.')
add('F1','Device:Fuse','1A / 125V','Fuse:Fuse_Littelfuse-NANO2-451_453',(68.58,43.18),(24,36),{1:'CAR_12V',2:'CAR_FUSED'},'0451001.MRL','Littelfuse',angle=90)
add('D1','Device:D_Schottky','SS110 / 100V','Diode_SMD:D_SMA',(93.98,43.18),(31,36),{1:'VPWR',2:'CAR_FUSED'},'SS110-13-F','Diodes Incorporated',angle=180)
add('D3','Device:D_TVS','SMBJ24CA','Diode_SMD:D_SMB',(116.84,55.88),(10,16),{1:'VPWR',2:'GND'},'SMBJ24CA','Littelfuse',angle=90,rot=90)
add('U1','Regulator_Switching:LMR36510ADDA','LMR36510ADDAR','Package_SO:Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias',(157.48,73.66),(19,12),{1:'GND',2:'VPWR',3:'VPWR',4:None,5:'BUCK_FB',6:'BUCK_VCC',7:'BUCK_BOOT',8:'BUCK_SW',9:'GND'},'LMR36510ADDAR','Texas Instruments',datasheet='https://www.ti.com/lit/ds/symlink/lmr36510.pdf')
cap('C1','2.2uF / 100V',(127,78.74),(12,10),'VPWR',fp='Capacitor_SMD:C_1210_3225Metric',mpn='GRM32ER72A225KA35L',rot=90)
cap('C2','220nF / 100V',(127,104.14),(14,12),'VPWR',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR72A224KAC4L',rot=90)
cap('C3','1uF / 16V',(152.4,114.3),(24.2,16.5),'BUCK_VCC',mpn='GRM188R71C105KA12D',rot=90)
cap('C4','100nF / 16V',(177.8,43.18),(24,12.5),'BUCK_BOOT','BUCK_SW',mpn='GRM188R71C104KA01D',rot=90)
add('L1','Device:L','22uH / 3.3A sat','Inductor_SMD:L_Bourns_SRN6045TA',(193.04,68.58),(27,7),{1:'BUCK_SW',2:'3V3'},'SRN6045TA-220M','Bourns',angle=90,datasheet='https://www.bourns.com/docs/Product-Datasheets/SRN6045TA.pdf')
for ref,sch,xy in [('C5',(198.12,101.6),(33,7)),('C6',(218.44,101.6),(33,11)),('C7',(238.76,101.6),(33,15))]:
    cap(ref,'22uF / 25V',sch,xy,'3V3',fp='Capacitor_SMD:C_1210_3225Metric',mpn='GRM32ER71E226KE15L',rot=90)
resistor('R1','100k / 1%',(180.34,109.22),(27,18),'3V3','BUCK_FB','RC0603FR-07100KL')
resistor('R2','43.2k / 1%',(180.34,129.54),(27,21),'BUCK_FB','GND','RC0603FR-0743K2L')

# Wi-Fi module and boot/reset. No external RF matching or crystal is needed.
add('U2','RF_Module:ESP32-C3-WROOM-02','ESP32-C3-WROOM-02-N4','RF_Module:ESP32-C3-WROOM-02',(322.58,83.82),(48,8),{1:'3V3',2:'ESP_EN',3:'CAN_TX',4:'CAN_RX',5:None,6:'STATUS_LED',7:'BOOT_IO8',8:'BOOT_IO9',9:'GND',10:None,11:None,12:None,13:'USB_DM',14:'USB_DP',15:'USB_PRESENT',16:'BOOT_IO2',17:'CAN_STB',18:'BAT_SENSE',19:'GND'},'ESP32-C3-WROOM-02-N4','Espressif',datasheet='https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.html')
resistor('R3','10k',(269.24,45.72),(36,4),'3V3','ESP_EN','RC0603FR-0710KL')
cap('C8','1uF / 16V',(269.24,71.12),(36,7),'ESP_EN',mpn='GRM188R71C105KA12D')
cap('C9','10uF / 16V',(297.18,35.56),(34.5,2.5),'3V3',fp='Capacitor_SMD:C_0805_2012Metric',mpn='GRM21BR71C106KE51L')
cap('C10','100nF / 16V',(320.04,35.56),(37,1.8),'3V3',mpn='GRM188R71C104KA01D')
resistor('R4','10k',(266.7,104.14),(60.5,5),'3V3','BOOT_IO2','RC0603FR-0710KL')
resistor('R5','10k',(287.02,132.08),(36,12),'3V3','BOOT_IO8','RC0603FR-0710KL')
resistor('R6','10k',(312.42,132.08),(36,16),'3V3','BOOT_IO9','RC0603FR-0710KL')
add('SW1','Switch:SW_Push','RESET','Button_Switch_SMD:SW_SPST_TL3342',(266.7,129.54),(31,28),{1:'ESP_EN',2:'GND'},'TL3342F160QG','E-Switch')
add('SW2','Switch:SW_Push','BOOT','Button_Switch_SMD:SW_SPST_TL3342',(340.36,132.08),(39,28),{1:'BOOT_IO9',2:'GND'},'TL3342F160QG','E-Switch')
resistor('R7','1M / 1%',(373.38,48.26),(60,2.5),'VPWR','BAT_SENSE','RC0603FR-071ML')
resistor('R8','47k / 1%',(373.38,71.12),(62,7.5),'BAT_SENSE','GND','RC0603FR-0747KL')
cap('C11','100nF / 16V',(393.7,71.12),(62,10.5),'BAT_SENSE',mpn='GRM188R71C104KA01D')
resistor('R9','1k',(373.38,99.06),(28,26),'STATUS_LED','LED_A','RC0603FR-071KL')
add('D6','Device:LED','GREEN / status','LED_SMD:LED_0603_1608Metric',(373.38,116.84),(27,28.5),{1:'GND',2:'LED_A'},'LTST-C190KGKT','Lite-On',angle=90)

# Vehicle CAN. External pull-up keeps standby asserted through reset.
add('U3','Leaf:TCAN3403DRQ1','TCAN3403DRQ1','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',(322.58,198.12),(16,27),{1:'CAN_TX',2:'GND',3:'3V3',4:'CAN_RX',5:'3V3',6:'CAN_L',7:'CAN_H',8:'CAN_STB'},'TCAN3403DRQ1','Texas Instruments',datasheet='https://www.ti.com/lit/gpn/TCAN3403-Q1')
resistor('R10','10k',(274.32,187.96),(11,24),'3V3','CAN_STB','RC0603FR-0710KL')
cap('C12','100nF / 16V',(297.18,167.64),(11,28),'3V3',mpn='GRM188R71C104KA01D',rot=90)
cap('C13','100nF / 16V',(345.44,167.64),(21,29.5),'3V3',mpn='GRM188R71C104KA01D')
add('D4','Leaf:PESD2CAN','PESD2CAN','Package_TO_SOT_SMD:SOT-23',(375.92,198.12),(16,33),{1:'CAN_L',2:'CAN_H',3:'GND'},'PESD2CAN,215','Nexperia',datasheet='https://assets.nexperia.com/documents/data-sheet/PESD2CAN.pdf')

# USB-C: USB and car power are diode-ORed before the buck.
add('J2','Connector:USB_C_Receptacle_USB2.0_16P','USB-C PROGRAM','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',(38.1,190.5),(56,47),{'A1':'GND','A4':'USB_5V','A5':'CC1','A6':'USB_CONN_DP','A7':'USB_CONN_DM','A8':None,'A9':'USB_5V','A12':'GND','B1':'GND','B4':'USB_5V','B5':'CC2','B6':'USB_CONN_DP','B7':'USB_CONN_DM','B8':None,'B9':'USB_5V','B12':'GND','S1':'GND','SH':'GND'},'USB4105-GF-A','GCT',datasheet='https://gct.co/files/drawings/usb4105.pdf')
resistor('R11','5.1k / 1%',(71.12,177.8),(50.5,41),'CC1','GND','RC0603FR-075K1L')
resistor('R12','5.1k / 1%',(71.12,200.66),(61,41),'CC2','GND','RC0603FR-075K1L')
add('D2','Device:D_Schottky','PMEG6030EP / 60V','Diode_SMD:D_SOD-128',(76.2,154.94),(47.5,36),{1:'VPWR',2:'USB_5V'},'PMEG6030EP,115','Nexperia',angle=180,datasheet='https://assets.nexperia.com/documents/data-sheet/PMEG6030EP_.pdf',notes='Low-drop USB blocking diode; qualify USB startup at minimum VBUS.')
cap('C14','1uF / 16V',(99.06,167.64),(52,38),'USB_5V',mpn='GRM188R71C105KA12D')
add('U4','Power_Protection:USBLC6-2SC6','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',(124.46,193.04),(56,35),{1:'USB_CONN_DP',2:'GND',3:'USB_CONN_DM',4:'USB_CONN_DM',5:'USB_5V',6:'USB_CONN_DP'},'USBLC6-2SC6','STMicroelectronics',datasheet='https://www.st.com/resource/en/datasheet/usblc6-2.pdf')
resistor('R13','22R',(170.18,185.42),(59,19),'USB_CONN_DM','USB_DM','RC0603FR-0722RL',angle=90,rot=90)
resistor('R14','22R',(170.18,200.66),(61.5,19),'USB_CONN_DP','USB_DP','RC0603FR-0722RL',angle=90,rot=90)
resistor('R15','100k',(218.44,170.18),(61,29),'USB_5V','USB_PRESENT','RC0603FR-07100KL')
resistor('R16','100k',(218.44,193.04),(61,32),'USB_PRESENT','GND','RC0603FR-07100KL')
resistor('R17','10k',(190.5,160.02),(52,31),'USB_5V','GND','RC0603FR-0710KL')
add('D5','Device:D_Zener','5.6V / 2%','Diode_SMD:D_SOD-123',(88.9,200.66),(48,31),{1:'USB_5V',2:'GND'},'BZT52-B5V6X','Nexperia',angle=90,datasheet='https://assets.nexperia.com/documents/data-sheet/BZT52-B_SER.pdf',notes='Limits USB rail rise from the reverse leakage of D2 when car-powered; R17 discharges the rail.')

# Placement refined against native courtyard and electrical clearances.
positions={'J1':(11,39),'F1':(24,33),'D1':(36.5,34),'D3':(7.5,16),
 'C1':(11.5,7),'C2':(12.5,11.4),'L1':(25,5.5),
 'C5':(31.5,5.5),'C6':(31.5,9.5),'C7':(31.5,13.5),
 'C9':(35.5,2.2),'C10':(36,4.5),'R3':(36,6.8),'C8':(36,9.1),
 'R5':(36,11.5),'R6':(36,14),'R10':(10,23),'C13':(22,29.5),
 'SW1':(31,26),'SW2':(42,26),'R9':(35,20),'D6':(39,20),
 'C4':(25,10.4),'C3':(25.5,13),'R1':(23,17.5),'R2':(23,20.5),
 'C14':(52,39),'U4':(56,39)}
for p in parts:
 if p['ref'] in positions:p['xy']=list(positions[p['ref']])
 if p['ref'] in ['C1','C2']:p['rotation']=180
 if p['ref'] in ['C5','C6','C7']:p['rotation']=0
 if p['ref']=='C3':p['rotation']=0
 if p['ref']=='C4':p['rotation']=180
 if p['ref']=='U4':p['rotation']=90
 if p['ref']=='U4':p['symbol']='Leaf:USBLC6-2SC6'
 if p['ref']=='U2':p['footprint']='Leaf:ESP32-C3-WROOM-02_0p3mm_Vias'
 if p['ref']=='F1':p['sch']=[63.5,43.18]
 if p['ref']=='L1':p['sch']=[198.12,83.82]

def load_def(libsym):
    lib,name=libsym.split(':',1)
    return deepcopy(custom[name]) if lib=='Leaf' else get_symbol(lib,name)

def schematic():
    syms={}; placed=[]; wires=[]; labels=[]; ncs=[]; seen=set()
    for part in parts:
        libsym=part['symbol']; src=load_def(libsym)
        if libsym not in syms:
            src[1]=libsym; syms[libsym]=deepcopy(src)
        x,y=part['sch']; angle=part['angle']; ar=math.radians(angle)
        def tr(px,py):return (round(x+px*math.cos(ar)-py*math.sin(ar),5),round(y-px*math.sin(ar)-py*math.cos(ar),5))
        inst=node('symbol',node('lib_id',libsym),node('at',x,y,angle),node('unit',1),node('in_bom',S('yes')),node('on_board',S('yes')),node('dnp',S('no')),node('uuid',uid(part['ref'])))
        isbig=part['ref'][0] in 'UJ'; vx,vy=(x,y-13.97) if isbig else (x+4.4,y-1.27)
        if part['ref']=='U2':vx,vy=x+22.86,y-30.48
        if part['ref']=='U3':vx,vy=x,y-22.86
        if part['ref']=='U4':vx,vy=x+15.24,y-16.51
        if part['ref']=='J2':vx,vy=x,y-22.86
        if part['ref']=='J1':vx,vy=x,y-21.59
        if not isbig and ((libsym in ['Device:R','Device:L','Device:Fuse'] and angle==90) or (libsym=='Device:D_Schottky' and angle in (0,180))):vx,vy=x,y-6.35
        if part['ref'].startswith('SW'):vx,vy=x,y-6.35
        just='left' if not isbig and vx>x else None
        if part['ref'] in ['D3','D5','D6']:vx,vy,just=x+10.16,y-1.27,None
        field_angle=90 if angle==90 else 0
        inst.extend([prop('Reference',part['ref'],vx,vy,size=1.27,angle=field_angle,justify=just),prop('Value',part['value'],vx,vy+2.54,size=1.0,angle=field_angle,justify=just),prop('Footprint',part['footprint'],x,y,True),prop('Datasheet',part['datasheet'],x,y,True),prop('MPN',part['mpn'],x,y,True),prop('Manufacturer',part['manufacturer'],x,y,True)])
        inst.append(node('instances',node('project',NAME,node('path','/'+ROOT,node('reference',part['ref']),node('unit',1)))))
        placed.append(inst)
        pins=[p for u in children(src,'symbol') for p in children(u,'pin')]
        for pin in pins:
            num=child(pin,'number')[1]; pa=child(pin,'at'); px,py=tr(pa[1],pa[2]); net=part['nets'].get(str(num))
            # A grouped pin can have more than one physical number at one coordinate.
            if (px,py,net) in seen:continue
            seen.add((px,py,net))
            if net is None:
                ncs.append(node('no_connect',node('at',px,py),node('uuid',uid(part['ref']+'-nc-'+str(num)))))
                continue
            # One continuous fused-input connection avoids two overlapping local labels.
            if part['ref']=='D1' and str(num)=='2':continue
            out=(pa[3]+angle+180)%360
            length=5.08
            ex=round(px+length*math.cos(math.radians(out)),5); ey=round(py-length*math.sin(math.radians(out)),5)
            if part['ref']=='F1' and str(num)=='2':ex=90.17
            wires.append(node('wire',node('pts',node('xy',px,py),node('xy',ex,ey)),node('stroke',node('width',0),node('type',S('default'))),node('uuid',uid(part['ref']+'-wire-'+str(num)))))
            label_angle=0 if out in (90,270) else out
            if part['ref']=='F1' and str(num)=='2':ex=73.66
            labels.append(node('label',net,node('at',ex,ey,label_angle),effects(.95,justify='left' if label_angle==0 else 'right'),node('uuid',uid(part['ref']+'-label-'+str(num)))))
    # Explicit power-source flags; do not weaken ERC rules.
    flag=get_symbol('power','PWR_FLAG'); flag[1]='power:PWR_FLAG'; syms['power:PWR_FLAG']=flag
    for i,net in enumerate(['GND','VPWR','3V3','USB_5V']):
        x=27.94+i*27.94; y=241.3; ref=f'#FLG0{i+1}'
        placed.append(node('symbol',node('lib_id','power:PWR_FLAG'),node('at',x,y,0),node('unit',1),node('in_bom',S('no')),node('on_board',S('yes')),node('dnp',S('no')),node('uuid',uid(ref)),prop('Reference',ref,x,y,True),prop('Value','PWR_FLAG',x,y-4,True),node('instances',node('project',NAME,node('path','/'+ROOT,node('reference',ref),node('unit',1))))))
        labels.append(node('label',net,node('at',x,y,0),effects(.95,justify='left'),node('uuid',uid(ref+'label'))))
    texts=[]
    for txt,x,y,size in [
      ('LEAF HEAT / Wi-Fi + one CAN channel',20.32,15.24,2.54),
      ('REV A — ENGINEERING PROTOTYPE — NOT RELEASED FOR MANUFACTURE',20.32,22.86,1.27),
      ('1  VEHICLE POWER / 3.3 V SUPPLY',20.32,30.48,1.52),
      ('2  Wi-Fi / BOOT / BATTERY SENSE',261.62,22.86,1.52),
      ('3  USB-C PROGRAMMING / POWER',20.32,142.24,1.52),
      ('4  VEHICLE CAN — NO TERMINATION',261.62,152.4,1.52),
      ('J1 pin 9: +12 V  |  pin 3: ground  |  pin 7: CAN-H  |  pin 2: CAN-L\nOnly use the Nissan ZE0/e-NV200 OVMS cable. Generic OBD cables differ.',20.32,92.71,1.02),
      ('65 V buck with input fuse, reverse blocking and 24 V TVS.\nTransient energy, cold operation and parked draw require physical tests.',20.32,115.57,1.02),
      ('USB-C supplies/programs the board on the bench.\nGPIO3 detects USB; firmware must inhibit vehicle commands when USB is present.',20.32,220.98,1.02),
      ('CAN TX: GPIO4  |  RX: GPIO5  |  STB: GPIO1\nSTB is pulled high during reset. Drive low only for a requested action.\n500 kbit/s, standard 11-bit frames; 2013–2015 Leaf profile to be confirmed.',261.62,223.52,1.02),
      ('Voltage sense is after the input diode: calibration required.\nSoftware low-battery sleep is required; there is no hardware battery disconnect.',261.62,241.3,1.02),
      ('Power flags identify external supplies and the buck output for electrical checks.',20.32,252.73,1.02),
    ]:texts.append(node('text',txt,node('at',x,y,0),effects(size,justify='left'),node('uuid',uid(txt))))
    data=node('kicad_sch',node('version',20260101),node('generator','eeschema'),node('generator_version','10.0'),node('uuid',ROOT),node('paper','A3'),node('title_block',node('title','Leaf Heat — Wi-Fi climate control'),node('date','2026-09-11'),node('rev','A / prototype'),node('company','DIY Leaf project'),node('comment',1,'Engineering review and vehicle tests required before release')),node('lib_symbols',*syms.values()),*wires,*labels,*ncs,*texts,*placed,node('sheet_instances',node('path','/',node('page','1'))),node('embedded_fonts',S('no')))
    (HERE/(NAME+'.kicad_sch')).write_text(sx.dumps(data))
    (HERE/'Leaf.kicad_sym').write_text(sx.dumps(node('kicad_symbol_lib',node('version',20241209),node('generator','kicad_symbol_editor'),*custom.values())))
    (HERE/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Leaf") (type "KiCad") (uri "${KIPRJMOD}/Leaf.kicad_sym") (options "") (descr "Project-specific CAN parts")))')
    subprocess.run([CLI,'sch','export','netlist','--format','kicadxml','-o',str(HERE/'exports'/'leaf-heat-v1.net.xml'),str(HERE/(NAME+'.kicad_sch'))],check=True)

def project_footprints():
    dest=HERE/'Leaf.pretty'; dest.mkdir(exist_ok=True)
    for part in parts:
        lib,name=part['footprint'].split(':',1)
        if lib=='Leaf':continue
        path=LIB/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')
        if not path.exists():raise FileNotFoundError(path)
    # Connector copper geometry follows the NorComp drawing; its 3D model is approximate.
    base='DSUB-9_Pins_Horizontal_P2.77x2.84mm_EdgePinOffset7.70mm_Housed_MountingHolesOffset9.12mm'
    f=pcb.FootprintLoad(str(LIB/'footprints'/'Connector_Dsub.pretty'),base)
    f.SetFPID(pcb.LIB_ID('Leaf','NorComp_182-009-113R531'))
    f.SetValue('182-009-113R531')
    for pad in f.Pads():
        if pad.GetNumber()=='SH':
            pad.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(3.2),pcb.FromMM(3.2)))
            x=5.54+(-12.495 if pcb.ToMM(pad.GetPosition().x)<5.54 else 12.495)
            pad.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(1.42)))
        elif pad.GetNumber():pad.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(1.2),pcb.FromMM(1.2)))
    plugin=pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.KICAD_SEXP)
    plugin.FootprintSave(str(dest),f)
    f=pcb.FootprintLoad(str(LIB/'footprints'/'RF_Module.pretty'),'ESP32-C3-WROOM-02')
    f.SetFPID(pcb.LIB_ID('Leaf','ESP32-C3-WROOM-02_0p3mm_Vias'))
    for pad in f.Pads():
        if pad.GetNumber()=='19' and pad.GetAttribute()==pcb.PAD_ATTRIB_PTH:
            pad.SetDrillSize(pcb.VECTOR2I(pcb.FromMM(.3),pcb.FromMM(.3)))
            pad.SetSize(pcb.VECTOR2I(pcb.FromMM(.65),pcb.FromMM(.65)))
    plugin.FootprintSave(str(dest),f)
    (HERE/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Leaf") (type "KiCad") (uri "${KIPRJMOD}/Leaf.pretty") (options "") (descr "Leaf custom connector footprint")))')

def board():
    import xml.etree.ElementTree as ET
    netroot=ET.parse(HERE/'exports'/'leaf-heat-v1.net.xml').getroot()
    pinmap={}
    board=pcb.BOARD(); board.SetFileName(str(HERE/(NAME+'.kicad_pcb')))
    nets={}
    for n in netroot.findall('./nets/net'):
        name=n.get('name'); nobj=pcb.NETINFO_ITEM(board,name); board.Add(nobj); nets[name]=nobj
        for nd in n.findall('node'):pinmap[(nd.get('ref'),nd.get('pin'))]=name
    for part in parts:
        lib,name=part['footprint'].split(':',1)
        root=HERE/'Leaf.pretty' if lib=='Leaf' else LIB/'footprints'/(lib+'.pretty')
        fp=pcb.FootprintLoad(str(root),name)
        if fp is None:raise ValueError(part['footprint'])
        fp.SetReference(part['ref']); fp.SetValue(part['value']); fp.SetFPID(pcb.LIB_ID(lib,name))
        fp.SetPath(pcb.KIID_PATH('/'+ROOT+'/'+uid(part['ref'])))
        fp.SetPosition(pcb.VECTOR2I(pcb.FromMM(part['xy'][0]),pcb.FromMM(part['xy'][1])))
        fp.SetOrientationDegrees(part['rotation']); board.Add(fp)
        fp.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(.85),pcb.FromMM(.85))); fp.Reference().SetTextThickness(pcb.FromMM(.13))
        fp.Value().SetVisible(False)
        for pad in fp.Pads():
            num=pad.GetNumber()
            # KiCad connector symbols use pin 0 for the shell; USB footprint uses SH.
            lookup=num
            net=pinmap.get((part['ref'],lookup))
            if net:pad.SetNet(nets[net])
            elif num and num not in part['nets']:print('Unmapped footprint pad',part['ref'],num)
        for model in fp.Models():
            # Keep standard KiCad environment references for portability.
            pass
    for (x1,y1),(x2,y2) in [((0,0),(65,0)),((65,0),(65,50)),((65,50),(0,50)),((0,50),(0,0))]:
        e=pcb.PCB_SHAPE(); e.SetShape(pcb.SHAPE_T_SEGMENT); e.SetStart(pcb.VECTOR2I(pcb.FromMM(x1),pcb.FromMM(y1))); e.SetEnd(pcb.VECTOR2I(pcb.FromMM(x2),pcb.FromMM(y2))); e.SetLayer(pcb.Edge_Cuts); e.SetWidth(pcb.FromMM(.05)); board.Add(e)
    for i,(x,y) in enumerate([(4,4),(39,46),(61,25)]):
        f=pcb.FootprintLoad(str(LIB/'footprints'/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5'); f.SetReference('H'+str(i+1)); f.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))); f.Value().SetVisible(False); f.Reference().SetVisible(False); board.Add(f)
    for text,x,y,size in [('LEAF HEAT',12,5,1.3),('Wi-Fi / CAN',11,20,1),('REV A PROTOTYPE',36,43,1),('NISSAN CABLE',15,47,1),('USB',56,40,1),('NO 120R',16,22,0.85)]:
        t=pcb.PCB_TEXT(board); t.SetText(text); t.SetPosition(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))); t.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size),pcb.FromMM(size))); t.SetTextThickness(pcb.FromMM(.15)); t.SetLayer(pcb.F_SilkS); board.Add(t)
    settings=board.GetDesignSettings(); settings.SetCopperLayerCount(2); settings.SetBoardThickness(pcb.FromMM(1.6))
    settings.SetAuxOrigin(pcb.VECTOR2I(0,pcb.FromMM(50)))
    pcb.SaveBoard(str(HERE/(NAME+'.kicad_pcb')),board)
    pro=json.loads((HERE/(NAME+'.kicad_pro')).read_text())
    pro['sheets']=[[ROOT,'Leaf Heat']]
    cl=pro['net_settings']['classes'][0]; cl.update(clearance=.2,track_width=.25,via_diameter=.65,via_drill=.3)
    pro['net_settings']['classes']=[cl]; pro['net_settings']['netclass_patterns']=[]
    for cname,width,names in [('Power',.6,['VPWR','CAR_12V','CAR_FUSED','3V3','USB_5V']),('Switch',.6,['BUCK_SW']),('USB',.2,['USB_DM','USB_DP','USB_CONN_DM','USB_CONN_DP'])]:
        c=deepcopy(cl);c['name']=cname;c['track_width']=width;pro['net_settings']['classes'].append(c)
        for n in names:pro['net_settings']['netclass_patterns'].append({'netclass':cname,'pattern':'/'+n})
    pro['board']['design_settings']={'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.3,'min_hole_clearance':.15}}
    (HERE/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2))

if __name__=='__main__':
    (HERE/'exports').mkdir(exist_ok=True)
    schematic(); project_footprints(); board()
    (HERE/'parts.json').write_text(json.dumps(parts,indent=2))
    with open(HERE/'exports'/'BOM.csv','w') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','Footprint','Manufacturer','MPN','Quantity','Notes'])
        for p in parts:w.writerow([p['ref'],p['value'],p['footprint'],p['manufacturer'],p['mpn'],1,p['notes']])
    print(f'Created schematic and PCB with {len(parts)} populated components')

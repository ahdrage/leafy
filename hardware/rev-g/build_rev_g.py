"""Generate Rev G from the archived Rev F native design. Run in the KiCad venv.

Generated CAD is not a vehicle qualification. See VALIDATION.md before ordering.
"""
from pathlib import Path
import copy, hashlib, json, math, shutil, subprocess, sys, uuid
import sexpdata as sx
import pcbnew as p
H=Path(__file__).resolve().parent; OLD=H.parent/'rev-f'; E=H/'exports'
NAME='leaf-heat-v7'; K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
sys.path.insert(0,str(H.parent)); import build_design as g
node,child,children=g.node,g.child,g.children
def uid(tag):return str(uuid.uuid5(uuid.NAMESPACE_URL,'leaf-heat-revg/'+tag))
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q):return p.ToMM(q.x),p.ToMM(q.y)
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
E.mkdir(exist_ok=True)
baseline={n:sha(OLD/n) for n in ['leaf-heat-v6.kicad_pcb','leaf-heat-v6.kicad_sch','parts.json']}
(E/'baseline-rev-f-sha256.json').write_text(json.dumps(baseline,indent=2)+'\n')
shutil.copytree(OLD/'Leaf.pretty',H/'Leaf.pretty',dirs_exist_ok=True)
for n in ['fp-lib-table','sym-lib-table','testpoints.json']:shutil.copy2(OLD/n,H/n)
for ext in ['kicad_pro','kicad_dru']:shutil.copy2(OLD/('leaf-heat-v6.'+ext),H/(NAME+'.'+ext))
parts=json.loads((OLD/'parts.json').read_text()); meta={q['ref']:q for q in parts}
RFP=meta['R1']['footprint']; CFP=meta['C3']['footprint']
def add(ref,symbol,value,footprint,sch,pos,nets,mpn,maker,assembly='HAND',rotation=0,datasheet='',notes=''):
    q=dict(ref=ref,symbol=symbol,value=value,footprint=footprint,sch=list(sch),xy=list(pos),nets={str(k):n for k,n in nets.items()},mpn=mpn,manufacturer=maker,assembly=assembly,angle=0,rotation=rotation,datasheet=datasheet,notes=notes)
    parts.append(q);meta[ref]=q
def resistor(ref,value,sch,pos,a,b,mpn,rotation=0):
    add(ref,'Device:R',value,RFP,sch,pos,{1:a,2:b},mpn,'Yageo',rotation=rotation,datasheet='https://www.yageogroup.com/component-documentation/download/specsheet/'+mpn)
def cap(ref,value,sch,pos,a,mpn,rotation=0):
    add(ref,'Device:C',value,CFP,sch,pos,{1:a,2:'GND'},mpn,'KEMET',rotation=rotation)
meta['U1']['nets']['3']='BUCK_EN'
for ref in ['R7','R8','C11']:
    meta[ref]['nets']={k:('BAT_DIV' if n=='BAT_SENSE' else n) for k,n in meta[ref]['nets'].items()}
meta['R7']['notes']='Protected VPWR divider; TMUX1511 isolates it from the unpowered MCU. ADC multiplier includes R26.'
for ref in ['SW1','SW2']:
    meta[ref].update(mpn='PTS645SL43-2 LFS',manufacturer='C&K / Littelfuse',datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',notes='Straight THT, 4.3 mm actuator, 6.5 x 4.5 mm contact centres. Current manufacturer series sheet specifies -40 to +85 C; confirm supplied variant against that sheet because distributor metadata differs.')
add('C15','Device:C_Polarized','47uF / 63V', 'Leaf:CP_Radial_D6.3mm_P2.50mm__Hand',(35.56,317.5),(11,32),{1:'BULK_DAMPED',2:'GND'},'EEU-FR1J470','Panasonic',datasheet='https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1J470',notes='Positive lead pad 1. 6.3 mm diameter, 11.2 mm maximum height; 105 C. R21 is in this branch only.')
add('R21','Device:R','1R / 1.5W', 'Leaf:R_2512_Hand',(35.56,292.1),(11,25),{1:'VPWR',2:'BULK_DAMPED'},'CRCW25121R00FKEGHP','Vishay',datasheet='https://www.vishay.com/docs/20043/crcwhpe3.pdf',notes='Pulse-capable 2512 damping resistor; not in series with the main supply.')
u5names={1:'VDD',2:'NC',3:'SENSE',4:'NC',5:'NC',6:'RESET_N',7:'NC',8:'GND',9:'CTR_MR',10:'CTS',11:'NC',12:'NC',13:'GND',14:'NC'}
u5nets={1:'VPWR',2:None,3:'UV_SENSE',4:None,5:None,6:'BUCK_EN',7:None,8:'GND',9:'UV_CTR',10:'UV_CTS',11:None,12:None,13:'GND',14:None}
add('U5','Leaf:TPS3760A012DYYR','TPS3760A012DYYR','Leaf:TI_DYY0014A__Factory',(106.68,317.5),(17,43),u5nets,'TPS3760A012DYYR','Texas Instruments','FACTORY',datasheet='https://www.ti.com/lit/gpn/tps3760',notes='Exact A012 UV, 0.8 V, 2% hysteresis, active-low open drain, NON-latching variant. Factory fit. Rev G.1: Catalog grade, not AEC-Q100; 65 V operating maximum, no Q1 70 V/50 ms operating allowance. User-approved prototype substitution.')
resistor('R22','680k / 1%',(71.12,292.1),(9,40),'VPWR','UV_SENSE','RC1206FR-07680KL',90)
resistor('R23','47k / 1%',(71.12,337.82),(9,47),'UV_SENSE','GND','RC1206FR-0747KL',90)
resistor('R24','10M / 1%',(152.4,317.5),(25,41),'BUCK_EN','UV_SENSE','RC1206FR-0710ML',90)
resistor('R25','470k / 1%',(152.4,292.1),(25,34),'VPWR','BUCK_EN','RC1206FR-07470KL',90)
cap('C16','220nF / 100V',(106.68,358.14),(17,36),'VPWR','C1206C224K1RACTU')
cap('C17','100nF / 50V',(71.12,358.14),(9,54),'UV_SENSE','C1206C104K5RACTU',90)
cap('C18','1uF / 25V',(137.16,358.14),(25,49),'UV_CTS','C1206C105K3RACTU')
cap('C19','1uF / 25V',(167.64,358.14),(17,53),'UV_CTR','C1206C105K3RACTU')
u6names={1:'SEL1',2:'S1',3:'D1',4:'SEL2',5:'S2',6:'D2',7:'GND',8:'D3',9:'S3',10:'SEL3',11:'D4',12:'S4',13:'SEL4',14:'VDD'}
u6nets={1:'3V3',2:'BAT_DIV',3:'BAT_SENSE',4:'GND',5:'GND',6:'GND',7:'GND',8:'GND',9:'GND',10:'GND',11:'GND',12:'GND',13:'GND',14:'3V3'}
add('U6','Leaf:TMUX1511PWR','TMUX1511PWR','Leaf:TSSOP-14_4.4x5mm_P0.65mm__Factory',(243.84,317.5),(79,26),u6nets,'TMUX1511PWR','Texas Instruments','FACTORY',datasheet='https://www.ti.com/lit/ds/symlink/tmux1511.pdf',notes='Channel 1 isolates battery ADC. Powered-off I/O protection to 3.6 V. All unused channels grounded. Factory fit.')
resistor('R26','100k / 1%',(287.02,317.5),(74,32),'BAT_SENSE','GND','RC1206FR-07100KL')
cap('C20','100nF / 50V',(243.84,358.14),(85,22.5),'3V3','C1206C104K5RACTU',90)
custom={}
for part,names in [(meta['U5'],u5names),(meta['U6'],u6names)]:
    pins=[]
    for i in range(1,15):
        side=0 if i<=7 else 1; y=(4-i)*2.54 if i<=7 else (i-11)*2.54
        name=names[i]
        typ='no_connect' if name=='NC' else ('power_in' if name in ('VDD','GND') else ('open_collector' if name=='RESET_N' else ('input' if name in ('SENSE','SEL1','SEL2','SEL3','SEL4') else 'passive')))
        pins.append((i,name,typ,-12.7 if not side else 12.7,y,0 if not side else 180))
    s=g.custom_ic(part['mpn'],pins)
    rect=child(children(s,'symbol')[0],'rectangle');child(rect,'start')[2]=10.16;child(rect,'end')[2]=-10.16
    custom[part['symbol']]=s

# Clone the existing schematic and change only affected labels/fields; append
# the protection circuits below it on A2. Existing symbols retain UUIDs.
sch=sx.load(open(OLD/'leaf-heat-v6.kicad_sch')); ROOT=child(sch,'uuid')[1]
lib=sx.load(open(OLD/'Leaf.kicad_sym'))
for libsym,s in custom.items():
    lib.append(copy.deepcopy(s));s=copy.deepcopy(s);s[1]=libsym;child(sch,'lib_symbols').append(s)
for libsym in ['Device:C_Polarized']:
    s=g.get_symbol(*libsym.split(':'));s[1]=libsym;child(sch,'lib_symbols').append(s)
for inst in children(sch,'symbol'):
    props={q[1]:q for q in children(inst,'property')};ref=props['Reference'][2]
    if ref in meta:
        for field,key in [('MPN','mpn'),('Manufacturer','manufacturer'),('Datasheet','datasheet')]:
            if field in props:props[field][2]=meta[ref][key]
    for project in children(child(inst,'instances') or [],'project'):project[1]=NAME
targets={g.uid('U1-label-3'):'BUCK_EN'}
for ref,pin in [('R7',2),('R8',1),('C11',1)]:targets[g.uid(f'{ref}-label-{pin}')]='BAT_DIV'
seen=set()
for t in children(sch,'label'):
    tid=child(t,'uuid')[1]
    if tid in targets:t[1]=targets[tid];seen.add(tid)
assert seen==set(targets),('Missing schematic edits',set(targets)-seen)
for q in parts[41:]:
    src=next(s for s in children(child(sch,'lib_symbols'),'symbol') if s[1]==q['symbol'])
    x,y=q['sch'];ref=q['ref'];isbig=ref.startswith('U')
    inst=node('symbol',node('lib_id',q['symbol']),node('at',x,y,0),node('unit',1),node('in_bom',sx.Symbol('yes')),node('on_board',sx.Symbol('yes')),node('dnp',sx.Symbol('no')),node('uuid',uid(ref)))
    inst.extend([g.prop('Reference',ref,x+(0 if isbig else 4.4),y-(15.24 if isbig else 1.27)),g.prop('Value',q['value'],x+(0 if isbig else 4.4),y-(12.7 if isbig else -1.27),size=.95)])
    inst.extend(g.prop(field,q[key],x,y,True) for field,key in [('Footprint','footprint'),('Datasheet','datasheet'),('MPN','mpn'),('Manufacturer','manufacturer'),('Assembly','assembly')])
    inst.append(node('instances',node('project',NAME,node('path','/'+ROOT,node('reference',ref),node('unit',1)))))
    sch.append(inst)
    for unit in children(src,'symbol'):
        for pin in children(unit,'pin'):
            num=child(pin,'number')[1];at=child(pin,'at');px=x+at[1];py=y-at[2];net=q['nets'][num]
            if net is None:sch.append(node('no_connect',node('at',px,py),node('uuid',uid(ref+'-nc-'+num))));continue
            a=(at[3]+180)%360;ex=round(px+5.08*math.cos(math.radians(a)),5);ey=round(py-5.08*math.sin(math.radians(a)),5)
            sch.append(node('wire',node('pts',node('xy',px,py),node('xy',ex,ey)),node('stroke',node('width',0),node('type',sx.Symbol('default'))),node('uuid',uid(ref+'-wire-'+num))))
            ang=0 if a in (90,270) else a
            sch.append(node('label',net,node('at',ex,ey,ang),g.effects(.95,justify='left' if ang==0 else 'right'),node('uuid',uid(ref+'-label-'+num))))
child(sch,'paper')[1]='A2';title=child(sch,'title_block');child(title,'rev')[1]='G / prototype';child(title,'date')[1]='2026-09-13'
for t in children(sch,'text'):
    t[1]=t[1].replace('REV F','REV G').replace('Rev F','Rev G')
    if 'Software low-battery' in t[1] or 'there is no hardware battery' in t[1]:t[1]='Rev G: independent UV monitor controls buck EN; no scheduled Wi-Fi disconnect.\nVoltage measurement is after D1 and includes R26: calibrate on the bench.'
for txt,x,y,size in [('5  INPUT DAMPING / INDEPENDENT BATTERY PROTECTION',20.32,269.24,1.52),('6  POWERED-OFF ADC ISOLATION',208.28,269.24,1.52),('UV monitor is non-latching. Low battery disables the regulator, including Wi-Fi.\nDelay and hysteresis prevent rapid restart cycling. See protection calculations.',20.32,383.54,1.1),('Factory fits U1 U2 U4 U5 U6 L1. All other parts hand fitted.\nPrototype: bench, assembly-process and vehicle validation required.',208.28,383.54,1.1)]:sch.append(node('text',txt,node('at',x,y,0),g.effects(size,justify='left'),node('uuid',uid(txt))))
(H/'Leaf.kicad_sym').write_text(sx.dumps(lib));(H/(NAME+'.kicad_sch')).write_text(sx.dumps(sch))
subprocess.run([K,'sch','export','netlist','--format','kicadxml','-o',str(E/(NAME+'.net.xml')),str(H/(NAME+'.kicad_sch'))],check=True)

# Local libraries: manufacturer DYY land pattern, standard TSSOP14, hand pads.
plugin=p.PCB_IO_MGR.FindPlugin(p.PCB_IO_MGR.KICAD_SEXP)
for source,name,hand in [('Capacitor_THT:CP_Radial_D6.3mm_P2.50mm','CP_Radial_D6.3mm_P2.50mm__Hand',True),('Resistor_SMD:R_2512_6332Metric_Pad1.40x3.35mm_HandSolder','R_2512_Hand',True),('Package_SO:TSSOP-14_4.4x5mm_P0.65mm','TSSOP-14_4.4x5mm_P0.65mm__Factory',False)]:
    libname,src=source.split(':');fp=p.FootprintLoad(str(LIB/'footprints'/(libname+'.pretty')),src);fp.SetFPID(p.LIB_ID('Leaf',name))
    if hand:
        for pad in fp.Pads():
            ls=pad.GetLayerSet();ls.RemoveLayer(p.F_Paste);pad.SetLayerSet(ls)
    plugin.FootprintSave(str(H/'Leaf.pretty'),fp)
fp=p.FOOTPRINT(None);fp.SetFPID(p.LIB_ID('Leaf','TI_DYY0014A__Factory'));fp.SetAttributes(p.FP_SMD)
fp.SetLibDescription('TI DYY0014A, drawing 4224643/D July 2024. 14 pads 1.05 x 0.30 mm; x +/-1.5 mm, pitch 0.5 mm. No exposed pad.')
for i in range(1,15):
    pad=p.PAD(fp);pad.SetNumber(str(i));pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_ROUNDRECT);pad.SetRoundRectRadiusRatio(.15);pad.SetSize(v((1.05,.30)));pad.SetPosition(v((-1.5,(i-4)*.5) if i<=7 else (1.5,(11-i)*.5)))
    ls=p.LSET();ls.AddLayer(p.F_Cu);ls.AddLayer(p.F_Mask);ls.AddLayer(p.F_Paste);pad.SetLayerSet(ls);fp.Add(pad)
for layer,w,box in [(p.F_Fab,.1,(-1,-2.1,1,2.1)),(p.F_CrtYd,.05,(-2.28,-2.35,2.28,2.35))]:
    x1,y1,x2,y2=box
    for a,c in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:
        t=p.PCB_SHAPE(fp);t.SetShape(p.SHAPE_T_SEGMENT);t.SetStart(v(a));t.SetEnd(v(c));t.SetLayer(layer);t.SetWidth(p.FromMM(w));fp.Add(t)
for a,c in [((-1,-2.2),(1,-2.2)),((-1,2.2),(1,2.2)),((-2.2,-1.85),(-2.2,-1.35))]:
    t=p.PCB_SHAPE(fp);t.SetShape(p.SHAPE_T_SEGMENT);t.SetStart(v(a));t.SetEnd(v(c));t.SetLayer(p.F_SilkS);t.SetWidth(p.FromMM(.12));fp.Add(t)
plugin.FootprintSave(str(H/'Leaf.pretty'),fp)

import xml.etree.ElementTree as ET
netroot=ET.parse(E/(NAME+'.net.xml')).getroot();pinmap={};types={};nets={}
b=p.LoadBoard(str(OLD/'leaf-heat-v6.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
for n in netroot.findall('./nets/net'):
    name=n.get('name');net=b.FindNet(name)
    if net is None:net=p.NETINFO_ITEM(b,name);b.Add(net)
    nets[name]=net
    for nd in n.findall('node'):pinmap[(nd.get('ref'),nd.get('pin'))]=name;types[(nd.get('ref'),nd.get('pin'))]=(nd.get('pinfunction',''),nd.get('pintype','passive'))
for q in parts[41:]:
    libname,name=q['footprint'].split(':');fp=p.FootprintLoad(str(H/'Leaf.pretty'),name);fp.SetReference(q['ref']);fp.SetPath(p.KIID_PATH('/'+ROOT+'/'+uid(q['ref'])));b.Add(fp);fps[q['ref']]=fp
positions={'C1':(12,18.3,90),'C2':(17,18.365,180),'C3':(29.5,22.9,270),'C4':(31,17.5,90),'R1':(20.2,26,0),'R2':(25.7,26,270)}
for ref,values in positions.items():meta[ref]['xy']=list(values[:2]);meta[ref]['rotation']=values[2]
for q in parts:
    fp=fps[q['ref']];fp.SetFPID(p.LIB_ID(*q['footprint'].split(':')));fp.SetValue(q['value']);fp.SetPosition(v(q['xy']));fp.SetOrientationDegrees(q['rotation']);fp.Value().SetVisible(False)
    for field,key in [('MPN','mpn'),('Manufacturer','manufacturer'),('Datasheet','datasheet'),('Assembly','assembly')]:fp.SetField(field,q[key])
    for field in fp.GetFields():
        if field.GetName()!='Reference':field.SetVisible(False)
    for pad in fp.Pads():
        key=(q['ref'],pad.GetNumber())
        if key in pinmap:
            pad.SetNet(nets[pinmap[key]]);fn,typ=types[key];pad.SetPinFunction(fn);pad.SetPinType(typ)
        elif pad.GetNumber() in q['nets'] and q['nets'][pad.GetNumber()] is None:pad.SetNetCode(0)

# Remove local regulator routes and battery ADC signal copper for fresh routing.
# All CAN, UART and module routes outside these explicit regions remain intact.
removed=[]
for t in list(b.GetTracks()):
    a=xy(t.GetStart());c=xy(t.GetEnd());n=t.GetNetname()
    local=(a[0]<39 and a[1]<32 and c[0]<39 and c[1]<37)
    if local or n=='/BAT_SENSE' or n in {'/BUCK_BOOT','/BUCK_VCC','/BUCK_FB'} or (n=='/3V3' and min(a[1],c[1])>=29 and max(a[1],c[1])<=36.1 and min(a[0],c[0])<40):
        removed.append(t.m_Uuid.AsString());b.RemoveNative(t)
for z in list(b.Zones()):
    if z.GetZoneName()=='Input bypass copper':b.RemoveNative(z)
def pt(ref,num):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition())
def path(n,pts,w=.3,layer=p.F_Cu):
    for a,c in zip(pts,pts[1:]):
        if math.dist(a,c)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(nets['/'+n]);t.SetLocked(True);b.Add(t)
def via(n,at):
    t=p.PCB_VIA(b);t.SetPosition(v(at));t.SetWidth(p.FromMM(.7));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(nets['/'+n]);t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
path('VPWR',[pt('C2',1),pt('U1',2)],.5)
path('VPWR',[pt('C1',1),(15,19.8625),(17.065,19.8625),pt('C2',1)],.6)
via('VPWR',(15,20.8));path('VPWR',[(15,20.8),(15,19.8625)],.6)
via('GND',(15.4375,16));path('GND',[pt('C2',2),(15.4375,16)],.5)
via('GND',(20,15.5));path('GND',[(20,15.5),(20,15.97),pt('U1',1)],.5)
via('GND',(12,15));path('GND',[(12,15),pt('C1',2)],.5)
path('BUCK_SW',[pt('U1',8),(28,15.97),(28,11.075),pt('L1',1)],.8)
path('BUCK_SW',[pt('U1',8),(29,17.095),(30.1575,15.9375),pt('C4',2)],.4)
path('BUCK_BOOT',[pt('U1',7),(29.3025,18.365),pt('C4',1)],.35)
path('BUCK_VCC',[pt('U1',6),(28.4375,19.635),pt('C3',2)],.35)
# C3 pin 1 is VCC: turn this capacitor so its upper pad faces the VCC pin.
# Native C footprints use pad 1 at negative X before rotation.
for t in list(b.GetTracks()):
    if t.GetNetname()=='/BUCK_VCC':b.RemoveNative(t)
meta['C3']['rotation']=270;fps['C3'].SetOrientationDegrees(270)
path('BUCK_VCC',[pt('U1',6),(28.4375,19.635),pt('C3',1)],.35)
path('BUCK_FB',[pt('U1',5),(26.5,21.28),(26.5,23.65),pt('R2',1)],.3)
path('BUCK_FB',[pt('R1',2),(22.2,26),(23.75,24.45),pt('R2',1)],.3)
path('BULK_DAMPED',[pt('R21',2),(14.5,29),(11,29),pt('C15',1)],.6)
b.GetTitleBlock().SetRevision('G / prototype')
fps['TP1'].SetPosition(v((4,34)))
tests=json.loads((H/'testpoints.json').read_text());next(q for q in tests if q['ref']=='TP1')['xy']=[4,34]
(H/'testpoints.json').write_text(json.dumps(tests,indent=2)+'\n')
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT):
        s=t.GetText().replace('REV F','REV G').replace('FACTORY: U1 U2 U4 L1','FACTORY: U1 U2 U4 U5 U6 L1').replace('FACTORY FITS U1 U2 U4 L1 ONLY','FACTORY: U1 U2 U4 U5 U6 L1')
        t.SetText(s)
        if s=='GND' and xy(t.GetPosition())==(8.0,45.3):t.SetPosition(v((4,37)))
        if 'FACTORY:' in s:t.SetTextSize(v((.8,.8)))
for q in parts[41:]:
    t=fps[q['ref']].Reference();t.SetVisible(True);t.SetTextSize(v((.9,.9)));t.SetTextThickness(p.FromMM(.14));t.SetPosition(v((q['xy'][0],q['xy'][1]-3.1)));t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
fps['C15'].Reference().SetPosition(v((17,30.5)));fps['U6'].Reference().SetPosition(v((79,22)))
b.BuildConnectivity();p.SaveBoard(str(H/(NAME+'.kicad_pcb')),b)
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n')
(E/'intended-changes.json').write_text(json.dumps({'source_revision':'F','revision':'G','removed_copper_uuids':removed,'added_refs':[q['ref'] for q in parts[41:]],'factory_refs':sorted(q['ref'] for q in parts if q['assembly']=='FACTORY')},indent=2)+'\n')
assert all(sha(OLD/n)==digest for n,digest in baseline.items())
print('Rev G created:',len(parts),'parts. Local routing/DRC still required.')

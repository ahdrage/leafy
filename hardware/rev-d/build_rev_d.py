"""Rev D hand-solder prototype. Preserve Rev C, make native KiCad files."""
from pathlib import Path
from copy import deepcopy
import sys, json, shutil, hashlib, math, subprocess
import pcbnew as p
import sexpdata as sx
H=Path(__file__).resolve().parent; C=H.parent/'rev-c'; E=H/'exports'; E.mkdir(exist_ok=True)
sys.path.insert(0,str(H.parent)); import build_design as g
NAME='leaf-heat-v4'; FACTORY={'U1','U2','U4','L1'}; W=150; HT=150
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q):return tuple(p.ToMM(x) for x in (q.x,q.y))
# Spread the functional groups across the requested 150 mm square. Preserve
# local component/pad spacing and critical high-frequency loops within groups.
def expand(q):return (q[0]+(50 if q[0]>=48 else 0),q[1]+(70 if q[1]>=37.5 else 0))
def compact(q):return (q[0]-(50 if q[0]>=98 else 0),q[1]-(70 if q[1]>=107.5 else 0))
copper_layers=p.LSET()
for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:copper_layers.AddLayer(layer)
for n in ['Leaf.pretty','Leaf.kicad_sym','fp-lib-table','sym-lib-table']:
    if (C/n).is_dir():shutil.copytree(C/n,H/n,dirs_exist_ok=True)
    else:shutil.copy2(C/n,H/n)
(E/'baseline-sha256.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in C.glob('leaf-heat-v3.kicad_*') if x.suffix!='.kicad_prl'},indent=2)+'\n')
parts=json.loads((C/'parts.json').read_text()); meta={q['ref']:q for q in parts}
RFP='Resistor_SMD:R_1206_3216Metric_Pad1.30x1.75mm_HandSolder'
CFP='Capacitor_SMD:C_1206_3216Metric_Pad1.33x1.80mm_HandSolder'
CFPL='Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder'
caps={'GRM21BR72A224KAC4L':('C1206C224K1RACTU','220nF / 100V'),
      'GRM188R71C105KA12D':('C1206C105K3RACTU','1uF / 25V'),
      'GRM188R71C104KA01D':('C1206C104K5RACTU','100nF / 50V'),
      'GRM21BR71C106KE51L':('C1206C106K4RACTU','10uF / 16V')}
for q in parts:
    q['assembly']='FACTORY' if q['ref'] in FACTORY else 'HAND'
    if q['ref'].startswith('R'):
        q['footprint']=RFP; q['mpn']=q['mpn'].replace('RC0603','RC1206')
        q['datasheet']='https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L'
    if q['ref'].startswith('C'):
        if q['mpn'] in caps:
            q['mpn'],q['value']=caps[q['mpn']];q['manufacturer']='KEMET';q['footprint']=CFP
            q['datasheet']='https://search.kemet.com/component-documentation/download/specsheet/'+q['mpn']
        else:q['footprint']=CFPL
    if q['ref'] in {'SW1','SW2'}:
        q.update(footprint='Button_Switch_THT:SW_PUSH_6mm_H4.3mm',manufacturer='Omron',mpn='B3F-1000',
                 datasheet='https://components.omron.com/sites/default/files/datasheet_pdf/A070-E1.pdf',
                 notes='Through-hole 6 x 6 mm, 4.3 mm height. Paired legs share contact 1 or 2. Fit last; do not wash switch.')
    if q['ref']=='D6':q.update(footprint='LED_SMD:LED_1206_3216Metric_Pad1.42x1.75mm_HandSolder',mpn='LTST-C150KGKT',notes='1206 green LED. Cathode is pad 1 / GND; match package cathode mark to K on board.')
    if q['ref']=='D4':q['footprint']='Package_TO_SOT_SMD:SOT-23_Handsoldering'
    if q['ref']=='U3':q['footprint']='Leaf:SOIC8_Hand_Access'
    if q['ref'] in {'J1','J3'}:q['notes']=q['notes'].replace('Fit on top.','Hand solder on top.').replace('Fit on top','Hand solder on top')
    if q['ref']=='J3':q['symbol']='Leaf:UART_Header'

# Widen only the exposed outer toes of the SOIC8 lands, preserving heel spacing.
f=p.FootprintLoad(str(g.LIB/'footprints/Package_SO.pretty'),'SOIC-8_3.9x4.9mm_P1.27mm')
f.SetFPID(p.LIB_ID('Leaf','SOIC8_Hand_Access'))
for pad in f.Pads():
    pos=xy(pad.GetPosition());size=xy(pad.GetSize())
    pad.SetPosition(v((pos[0]+math.copysign(.35,pos[0]),pos[1])));pad.SetSize(v((size[0]+.7,size[1])))
for d in f.GraphicalItems():
    if d.GetLayer()==p.F_CrtYd:
        a=xy(d.GetStart());b=xy(d.GetEnd());d.SetStart(v((math.copysign(abs(a[0])+.7,a[0]),a[1])));d.SetEnd(v((math.copysign(abs(b[0])+.7,b[0]),b[1])))
p.FootprintSave(str(H/'Leaf.pretty'),f)

# Project libraries encode the intentional paste/thermal variants, so library
# comparisons remain meaningful instead of suppressing mismatch warnings.
for q in parts:
    lib,base=q['footprint'].split(':');folder=H/'Leaf.pretty' if lib=='Leaf' else g.LIB/'footprints'/(lib+'.pretty')
    f=p.FootprintLoad(str(folder),base);name=base+('__Factory' if q['ref'] in FACTORY else '__Hand')
    f.SetFPID(p.LIB_ID('Leaf',name))
    if q['ref'] in {'U1','U2'}:f.SetAttributes(p.FP_SMD)
    f.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL if q['ref'] in FACTORY else p.ZONE_CONNECTION_THERMAL)
    for pad in f.Pads():
        pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL if q['ref'] in FACTORY else p.ZONE_CONNECTION_THERMAL)
        pad.SetThermalGap(p.FromMM(.3))
        if q['ref']=='U2' and pad.GetAttribute()==p.PAD_ATTRIB_PTH:
            ls=pad.GetLayerSet();ls.AddLayer(p.B_Mask);pad.SetLayerSet(ls)
        if q['ref'] not in FACTORY:
            ls=pad.GetLayerSet();ls.RemoveLayer(p.F_Paste);ls.RemoveLayer(p.B_Paste);pad.SetLayerSet(ls)
    for z in f.Zones():
        if z.GetIsRuleArea():z.SetLayerSet(copper_layers)
    p.FootprintSave(str(H/'Leaf.pretty'),f);q['footprint']='Leaf:'+name

# Bare plated test holes require no purchased component.
tf=p.FOOTPRINT(None);tf.SetFPID(p.LIB_ID('Leaf','TestPoint_3mm_Hole1.5mm'))
tf.SetReference('TP');tf.SetValue('BARE TEST HOLE');tf.SetAttributes(p.FP_THROUGH_HOLE|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
pad=p.PAD(tf);pad.SetNumber('1');pad.SetAttribute(p.PAD_ATTRIB_PTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(v((3,3)));pad.SetDrillSize(v((1.5,1.5)))
ls=p.LSET.AllCuMask();ls.AddLayer(p.F_Mask);ls.AddLayer(p.B_Mask);pad.SetLayerSet(ls);tf.Add(pad)
for layer,radius,width in [(p.F_CrtYd,1.75,.05),(p.F_SilkS,1.8,.15)]:
    d=p.PCB_SHAPE(tf);d.SetShape(p.SHAPE_T_CIRCLE);d.SetCenter(v((0,0)));d.SetEnd(v((radius,0)));d.SetWidth(p.FromMM(width));d.SetLayer(layer);tf.Add(d)
p.FootprintSave(str(H/'Leaf.pretty'),tf)
tests=[('TP1','GND',(10,35)),('TP2','CAR_12V',(44,69)),('TP3','VPWR',(10,43)),('TP4','3V3',(45,35)),('TP5','CAN_H',(12,59)),('TP6','CAN_L',(12,53)),('TP7','ESP_EN',(53,43))]
extras=[]
for i,(ref,n,pos) in enumerate(tests):
    extras.append(dict(ref=ref,value=n,footprint='Leaf:TestPoint_3mm_Hole1.5mm',symbol='Connector:TestPoint',sch=[154.94+i*12.7,266.7],xy=list(pos),rotation=0,angle=0,nets={'1':n},mpn='',manufacturer='',datasheet='',notes='Bare plated test hole; no component to purchase or fit.',assembly='BARE'))

# Start with the already polished Rev C schematic; modify purchasing fields only.
s=sx.load(open(C/'leaf-heat-v3.kicad_sch'))
header=g.get_symbol('Connector_Generic','Conn_01x03');header[1]='UART_Header'
for unit in g.children(header,'symbol'):unit[1]=unit[1].replace('Conn_01x03','UART_Header')
for prop in g.children(header,'property'):
    if prop[1]=='ki_fp_filters':prop[2]='*PinHeader_1x03*'
lib=sx.load(open(H/'Leaf.kicad_sym'));lib.append(deepcopy(header));(H/'Leaf.kicad_sym').write_text(sx.dumps(lib))
header[1]='Leaf:UART_Header';g.child(s,'lib_symbols').append(header)
for inst in g.children(s,'symbol'):
    props={q[1]:q for q in g.children(inst,'property')};ref=props.get('Reference',[None,None,''])[2]
    for prj in g.children(g.child(inst,'instances') or [],'project'):prj[1]=NAME
    if ref in meta:
        q=meta[ref]
        g.child(inst,'lib_id')[1]=q['symbol']
        for field,key in [('Value','value'),('Footprint','footprint'),('MPN','mpn'),('Manufacturer','manufacturer'),('Datasheet','datasheet')]:props[field][2]=q[key]
        at=g.child(inst,'at');inst.append(g.prop('Assembly',q['assembly'],at[1],at[2],True))
tpdef=g.get_symbol('Connector','TestPoint');tpdef[1]='Connector:TestPoint';g.child(s,'lib_symbols').append(tpdef)
for q in extras:
    x,y=q['sch'];inst=g.node('symbol',g.node('lib_id',q['symbol']),g.node('at',x,y,0),g.node('unit',1),g.node('in_bom',sx.Symbol('no')),g.node('on_board',sx.Symbol('yes')),g.node('dnp',sx.Symbol('no')),g.node('uuid',g.uid(q['ref'])))
    inst.extend([g.prop('Reference',q['ref'],x,y-7,size=1),g.prop('Value',q['value'],x,y-4.5,size=.9),g.prop('Footprint',q['footprint'],x,y,True),g.prop('Datasheet','',x,y,True)])
    inst.append(g.node('instances',g.node('project',NAME,g.node('path','/'+g.ROOT,g.node('reference',q['ref']),g.node('unit',1)))))
    s.append(inst);s.append(g.node('label',q['value'],g.node('at',x,y,0),g.effects(.85,justify='left'),g.node('uuid',g.uid(q['ref']+'label'))))
for t in g.children(s,'text'):
    t[1]=t[1].replace('REV C — UART PROGRAMMING — ENGINEERING PROTOTYPE','REV D — HAND-SOLDER PROTOTYPE — FACTORY: U1 / U2 / U4 / L1').replace('in Rev C','in Rev D')
title=g.child(s,'title_block');g.child(title,'rev')[1]='D';g.child(title,'date')[1]='2026-09-12'
(H/(NAME+'.kicad_sch')).write_text(sx.dumps(s))
subprocess.run([g.CLI,'sch','export','netlist','--format','kicadxml','-o',str(E/(NAME+'.net.xml')),str(H/(NAME+'.kicad_sch'))],check=True)

b=p.LoadBoard(str(C/'leaf-heat-v3.kicad_pcb'))
for t in list(b.GetTracks()):b.RemoveNative(t)
for z in list(b.Zones()):b.RemoveNative(z)
for d in list(b.GetDrawings()):b.RemoveNative(d)
oldfps={f.GetReference():f for f in b.GetFootprints()}
positions={
 'U1':(24,19,0),'L1':(30,11,0),'C1':(11.5,21,90),'C2':(18,17.7,90),
 'C3':(33,25,0),'C4':(32,18,90),'C5':(40,11,0),'C6':(40,18,0),'C7':(40,25,0),
 'R1':(22,29,90),'R2':(27,29,0),'F1':(38,58,90),'D1':(38,47,270),'D3':(18,42,90),
 'J1':(15,69,0),'U3':(26,48,270),'C12':(25.365,41,90),'C13':(21,54,180),'R10':(33,54,0),'D4':(23,61,90),
 'U2':(72,8,0),'C9':(55,8,180),'C10':(59.5,3,180),'R3':(56,16,0),'C8':(56,22,0),
 'R5':(64,26,0),'R6':(74,26,0),'R4':(88,14,90),'R7':(88,3,0),'R8':(95,7,90),'C11':(88,8,0),
 'R18':(88,21,0),'R19':(88,27,180),'R20':(77,32,0),'R9':(59,34,0),'D6':(68,34,180),
 'SW1':(57,44,0),'SW2':(72,44,0),'J3':(81,71,90),'U4':(84.81,67,90),'C14':(84.81,60,90),
 'H1':(4,4,0),'H2':(96,76,0),'H3':(45,76,0)}
import xml.etree.ElementTree as ET
pinmap={}
for n in ET.parse(E/(NAME+'.net.xml')).getroot().findall('./nets/net'):
    if not b.FindNet(n.get('name')):b.Add(p.NETINFO_ITEM(b,n.get('name')))
    for q in n.findall('node'):pinmap[(q.get('ref'),q.get('pin'))]=n.get('name')
fps={}
for q in parts+extras:
    ref=q['ref'];old=oldfps.get(ref);lib,name=q['footprint'].split(':')
    folder=H/'Leaf.pretty' if lib=='Leaf' else g.LIB/'footprints'/(lib+'.pretty')
    f=p.FootprintLoad(str(folder),name);assert f is not None,q['footprint']
    f.SetFPID(p.LIB_ID(lib,name));f.SetReference(ref);f.SetValue(q['value']);f.SetPath(old.GetPath() if old else p.KIID_PATH('/'+g.ROOT+'/'+g.uid(ref)))
    x,y,ang=positions.get(ref,(*q['xy'],q['rotation']));x,y=expand((x,y));f.SetPosition(v((x,y)));f.SetOrientationDegrees(ang)
    if old:b.RemoveNative(old)
    b.Add(f);fps[ref]=f;q['xy']=[x,y];q['rotation']=ang
    for field,key in [('MPN','mpn'),('Manufacturer','manufacturer'),('Datasheet','datasheet'),('Assembly','assembly')]:
        f.SetField(field,q[key]);f.GetField(field).SetVisible(False)
    f.Value().SetVisible(False)
    if ref in {'U1','U2'}:f.SetAttributes(p.FP_SMD)
    f.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL if ref in FACTORY else p.ZONE_CONNECTION_THERMAL)
    for pad in f.Pads():
        if pad.GetNumber():pad.SetNet(b.FindNet(pinmap[(ref,pad.GetNumber())]))
        pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL if ref in FACTORY else p.ZONE_CONNECTION_THERMAL)
        pad.SetThermalGap(p.FromMM(.3))
        if ref not in FACTORY:
            ls=pad.GetLayerSet();ls.RemoveLayer(p.F_Paste);ls.RemoveLayer(p.B_Paste);pad.SetLayerSet(ls)
    for z in f.Zones():
        if z.GetIsRuleArea():z.SetLayerSet(copper_layers)
for ref in ['H1','H2','H3']:
    f=oldfps[ref];x,y,a=positions[ref];f.SetPosition(v(expand((x,y))));fps[ref]=f
    f.Reference().SetVisible(False);f.Value().SetVisible(False)
for a,c in [((0,0),(W,0)),((W,0),(W,HT)),((W,HT),(0,HT)),((0,HT),(0,0))]:
    d=p.PCB_SHAPE(b);d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(v(a));d.SetEnd(v(c));d.SetWidth(p.FromMM(.05));d.SetLayer(p.Edge_Cuts);b.Add(d)
b.GetDesignSettings().SetAuxOrigin(v((0,HT)))
b.GetTitleBlock().SetRevision('D');b.GetTitleBlock().SetTitle('Leaf Heat — hand-solder prototype')
def pt(ref,num):return compact(xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition()))
def path(n,pts,w=.3,layer=p.F_Cu,physical=False):
    if not physical:pts=[expand(q) for q in pts]
    for a,c in zip(pts,pts[1:]):
        if math.dist(a,c)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);b.Add(t)
def via(n,at,physical=False):
    if not physical:at=expand(at)
    t=p.PCB_VIA(b);t.SetPosition(v(at));t.SetWidth(p.FromMM(.7));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
def zone(n,layer,points,name,priority=1):
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/'+n));z.SetLocalClearance(p.FromMM(.25));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.2));z.SetAssignedPriority(priority);z.SetZoneName(name)
    poly=z.Outline();poly.NewOutline()
    for q in points:poly.Append(v(expand(q)))
    b.Add(z)
# Keep switch-current paths local even on the larger prototype.
path('VPWR',[pt('C2',1),(20,19.5375),(20,18.365),pt('U1',2)],.5)
path('VPWR',[pt('U1',2),pt('U1',3)],.5)
path('GND',[pt('C2',2),(20,15.8625),pt('U1',1)],.5)
path('BUCK_SW',[pt('U1',8),(28,15.97),(28,11.075),pt('L1',1)],.8)
path('BUCK_SW',[pt('U1',8),(29,17.095),(29.9325,16.1625),pt('C4',2)],.5)
path('BUCK_BOOT',[pt('U1',7),(29,18.365),(30.4725,19.8375),pt('C4',1)],.5)
path('BUCK_VCC',[pt('U1',6),(29,19.635),(30,20.635),(30,23.5625),pt('C3',1)],.4)
path('BUCK_FB',[pt('U1',5),(26.875,25.3),(25.175,27),pt('R2',1)],.3)
path('BUCK_FB',[pt('R2',1),(23.825,29),pt('R1',2)],.3)
path('3V3',[pt('C7',1),(37,26.1625),(37,34),(22,34),pt('R1',1)],.3)
path('CAR_12V',[pt('J1',9),(27,74.145),(38,74.145),(38,69),pt('TP2',1)],1,p.B_Cu)
via('CAR_12V',(38,63));path('CAR_12V',[(38,69),(38,63)],1,p.B_Cu);path('CAR_12V',[(38,63),pt('F1',1)],1)
path('CAR_FUSED',[pt('F1',2),pt('D1',2)],1)
zone('VPWR',p.In2_Cu,[(7,13),(21,13),(21,17),(23,17),(23,24),(21,26),(21,46),(35,46),(35,40),(42,40),(42,49),(7,49)],'Protected input distribution',4)
zone('VPWR',p.F_Cu,[(10,21),(14,21),(18,18.9),(20.4,18.9),(20.4,21),(16,23.6),(10,23.6)],'Input bypass copper',5)
zone('3V3',p.F_Cu,[(31.8,8.5),(38.8,8.5),(38.8,26.4),(36.8,26.4),(36.8,14),(31.8,14)],'Buck output capacitor bank',5)
zone('3V3',p.In2_Cu,[(1,1),(99,1),(99,79),(1,79)],'3V3 distribution',2)
# CAN protection is on the short connector-to-transceiver path.
path('CAN_L',[pt('J1',2),(17.77,66.78),pt('D4',1),(21.3,61.75),(21.3,58.5),(25.365,54.435),pt('U3',6)],.3)
path('CAN_H',[pt('J1',7),(19.155,67.84),(23.95,63.045),pt('D4',2),(23.95,59.185),(26.635,56.5),pt('U3',7)],.3)
path('CAN_L',[pt('TP6',1),(24.365,53),(25.365,54)],.3,p.B_Cu);via('CAN_L',(25.365,54))
path('CAN_H',[pt('TP5',1),(22.45,59),(23.95,60.5)],.3,p.B_Cu);via('CAN_H',(23.95,60.5))
# Header and ESD placement use the validated Rev C ordering.
for n,u,j in [('PROG_RX',1,2),('PROG_TX',3,3)]:
    path(n,[pt('U4',u),pt('U4',7-u)])
    a=pt('U4',u);z=pt('J3',j);path(n,[a,(a[0],z[1]-abs(a[0]-z[0])),z])
path('3V3',[pt('C14',1),pt('U4',5)],.4)
path('UART_TX',[pt('U2',12),(83,11),(85,13),(85,21),pt('R18',1)])
path('UART_RX',[pt('U2',11),(82.5,12.5),(84,14),(84,25.675),pt('R19',2)])
# Short local bypasses at U2 and U3.
path('3V3',[pt('C10',1),pt('U2',1)],.5)
path('3V3',[pt('C9',1),(59,8),(61,6),(61,2),pt('U2',1)],.5)
path('3V3',[pt('C12',1),pt('U3',3)],.4)
path('3V3',[pt('C13',1),(24.095,54),(24.095,50.825),pt('U3',5)],.4)

# Place plane vias outside component lands and clear of existing critical copper.
def rect(q):
    r=q.GetBoundingBox();return (p.ToMM(r.GetLeft()),p.ToMM(r.GetTop()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))
def dist_rect(at,r):return math.hypot(max(r[0]-at[0],0,at[0]-r[2]),max(r[1]-at[1],0,at[1]-r[3]))
def dist_seg(q,a,c):
    dx=c[0]-a[0];dy=c[1]-a[1];l=dx*dx+dy*dy;t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/l)) if l else 0
    return math.dist(q,(a[0]+t*dx,a[1]+t*dy))
def free(at,n):
    if not(1<at[0]<W-1 and 1.5<at[1]<HT-1):return False
    for f in fps.values():
        for pad in f.Pads():
            if dist_rect(at,rect(pad))<.65:return False
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):
            if math.dist(at,xy(t.GetPosition()))<1:return False
        elif t.GetNetname()!='/'+n and dist_seg(at,xy(t.GetStart()),xy(t.GetEnd()))<.35+p.ToMM(t.GetWidth())/2+.25:return False
    return True
def drop(ref,num,n):
    pad=next(q for q in fps[ref].Pads() if q.GetNumber()==str(num));a=xy(pad.GetPosition());r=rect(pad)
    cand=[(r[0]-.7,a[1]),(r[2]+.7,a[1]),(a[0],r[1]-.7),(a[0],r[3]+.7)]
    for rad in [1.5,1.8,2.1,2.5,3]:
        for deg in range(0,360,45):cand.append((a[0]+rad*math.cos(math.radians(deg)),a[1]+rad*math.sin(math.radians(deg))))
    for z in cand:
        if not free(z,n):continue
        clear=True
        for k in range(1,25):
            q=(a[0]+(z[0]-a[0])*k/24,a[1]+(z[1]-a[1])*k/24)
            for f in fps.values():
                for other in f.Pads():
                    if other.GetNetname()!='/'+n and dist_rect(q,rect(other))<.4:clear=False
            for t in b.GetTracks():
                if t.GetNetname()=='/'+n:continue
                if isinstance(t,p.PCB_VIA):
                    if math.dist(q,xy(t.GetPosition()))<.75:clear=False
                elif t.GetLayer()==p.F_Cu and dist_seg(q,xy(t.GetStart()),xy(t.GetEnd()))<.2+p.ToMM(t.GetWidth())/2+.25:clear=False
        if clear:path(n,[a,z],.4,physical=True);via(n,z,physical=True);return
    raise RuntimeError(('No plane via',ref,num,n))
seen=set()
for ref,f in fps.items():
    for pad in f.Pads():
        key=(ref,pad.GetNumber());n=pad.GetNetname().lstrip('/')
        if key in seen:continue
        seen.add(key)
        if pad.GetAttribute()==p.PAD_ATTRIB_SMD and n in {'GND','3V3','VPWR'} and key not in {('U1','9'),('U1','2'),('U1','3'),('U2','19'),('R1','1'),('L1','2')}:
            drop(ref,pad.GetNumber(),n)
for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:zone('GND',layer,[(.4,.4),(99.6,.4),(99.6,79.6),(.4,79.6)],'Ground reference' if layer==p.In1_Cu else 'Ground '+b.GetLayerName(layer),0)
for y in [3,10,20,30,40,55,70,85,100,110,120,130,140,147]:
    for x in [3,8,45,60,75,90,110,125,140,147]:
        if free((x,y),'GND'):via('GND',(x,y),physical=True)

def label(txt,at,size=1,layer=p.F_SilkS,physical=False):
    if not physical:at=expand(at)
    t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(at));t.SetTextSize(v((size,size)));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer)
    if layer==p.B_SilkS:t.SetMirrored(True)
    b.Add(t)
label('LEAF HEAT / REV D',(28,3),1.5)
label('HAND-SOLDER PROTOTYPE',(69,55),1.4)
label('FACTORY: U1 U2 U4 L1',(67,58),1)
label('12V:9  GND:3  H:7  L:2',(23,78),1)
label('NISSAN ZE0 CABLE ONLY',(24,75),1)
label('UART / 3.3V LOGIC',(83,77.5),1)
for txt,at in [('GND',(81,74)),('RX',(83.54,74)),('TX',(86.08,74))]:label(txt,at,.85)
label('NO POWER PIN',(92.5,67),.85)
label('RESET',(60.25,52),1.2);label('BOOT',(75.25,52),1.2)
label('K',(70.9,34),.85)
for q in extras:label(q['value'],(q['xy'][0],q['xy'][1]+3.3),.9,physical=True)
label('REV D / 150 x 150 mm / 4 layers',(75,65),2,p.B_SilkS,physical=True)
label('FACTORY FITS U1 U2 U4 L1 ONLY',(75,72),1.5,p.B_SilkS,physical=True)
label('COMPLETE HAND ASSEMBLY BEFORE POWER',(75,79),1.3,p.B_SilkS,physical=True)
label('NO CAN TERMINATION / UART HAS NO POWER PIN',(75,86),1,p.B_SilkS,physical=True)
# Collision-free, upright designators; value map is supplied separately.
def overlap(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]
def padded(item,m):r=rect(item);return (r[0]-m,r[1]-m,r[2]+m,r[3]+m)
blocks=[]
for f in fps.values():
    blocks.extend(padded(q,.3) for q in f.Pads())
    blocks.extend(padded(q,.18) for q in f.GraphicalItems() if q.GetLayer()==p.F_SilkS)
blocks.extend(padded(q,.2) for q in b.GetDrawings() if isinstance(q,p.PCB_TEXT) and q.GetLayer()==p.F_SilkS)
for ref,f in sorted(fps.items()):
    if ref.startswith('H'):continue
    t=f.Reference();t.SetVisible(True);t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetTextSize(v((1,1)));t.SetTextThickness(p.FromMM(.15));x,y=xy(f.GetPosition())
    candidates=[]
    if ref=='U2':candidates.append(expand((72,18)))
    if ref=='J1':candidates.append(expand((36,68)))
    for rad in [2.5,3,3.5,4,4.5,5,6,7,8]:
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0),(-.7,-.7),(.7,-.7),(-.7,.7),(.7,.7)]:candidates.append((x+rad*dx,y+rad*dy))
    for at in candidates:
        t.SetPosition(v(at));r=padded(t,.18)
        if r[0]<.5 or r[1]<.5 or r[2]>W-.5 or r[3]>HT-.5:continue
        if not any(overlap(r,q) for q in blocks):blocks.append(r);break
    else:raise RuntimeError('No reference position '+ref)
b.BuildConnectivity();p.SaveBoard(str(H/(NAME+'.kicad_pcb')),b)
pro=json.loads((C/'leaf-heat-v3.kicad_pro').read_text());pro['board']['design_settings']['track_widths']=[0,.25,.3,.4,.5,.8,1]
for cl in pro['net_settings']['classes']:
    if cl['name']=='Default':cl['track_width']=.3
pro['board']['design_settings']['rules']['min_clearance']=.2
pro['board']['design_settings']['rules']['min_track_width']=.25
(H/(NAME+'.kicad_pro')).write_text(json.dumps(pro,indent=2)+'\n')
shutil.copy2(C/'leaf-heat-v3.kicad_dru',H/(NAME+'.kicad_dru'))
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n');(H/'testpoints.json').write_text(json.dumps(extras,indent=2)+'\n')
print('Rev D placed; critical power, CAN and UART paths explicit. Run DRC before remaining routing.')

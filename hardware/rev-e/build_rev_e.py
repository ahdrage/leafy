"""Rev E: 100 mm square, distributed hand access, unchanged Rev D circuit."""
from pathlib import Path
import json,shutil,hashlib,math,subprocess
import pcbnew as p
import sexpdata as sx
H=Path(__file__).resolve().parent;D=H.parent/'rev-d';E=H/'exports'
K='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
NAME='leaf-heat-v5';W=HT=100;FACTORY={'U1','U2','U4','L1'}
def v(q):return p.VECTOR2I(*(p.FromMM(x) for x in q))
def xy(q):return p.ToMM(q.x),p.ToMM(q.y)
def child(q,k):return next((x for x in q if isinstance(x,list) and x and str(x[0])==k),None)
def children(q,k):return [x for x in q if isinstance(x,list) and x and str(x[0])==k]
for n in ['Leaf.pretty','Leaf.kicad_sym','fp-lib-table','sym-lib-table']:
    if (D/n).is_dir():shutil.copytree(D/n,H/n,dirs_exist_ok=True)
    else:shutil.copy2(D/n,H/n)
(E/'baseline-sha256.json').write_text(json.dumps({q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in D.glob('leaf-heat-v4.kicad_*') if q.suffix!='.kicad_prl'},indent=2)+'\n')
parts=json.loads((D/'parts.json').read_text());tests=json.loads((D/'testpoints.json').read_text())
# Purchasing erratum: the inherited Diodes SS110-13-F ordering code could not
# be manufacturer-verified. B1100-13-F is the documented 100 V / 1 A SMA part.
d1=next(q for q in parts if q['ref']=='D1')
d1.update(mpn='B1100-13-F',value='B1100 / 100V',datasheet='https://www.diodes.com/datasheet/download/B1100.pdf',notes='D1 ordering-code correction 2026-09-12: verified Diodes B1100-13-F, 100 V / 1 A, SMA; cathode band to pad 1 / VPWR.')
s=sx.load(open(D/'leaf-heat-v4.kicad_sch'))
for inst in children(s,'symbol'):
    for project in children(child(inst,'instances') or [],'project'):project[1]=NAME
    props={q[1]:q for q in children(inst,'property')}
    if props.get('Reference',[None,None,None])[2]=='D1':
        props['MPN'][2]=d1['mpn'];props['Value'][2]=d1['value']
for t in children(s,'text'):t[1]=t[1].replace('REV D','REV E').replace('Rev D','Rev E')
title=child(s,'title_block');child(title,'rev')[1]='E';child(title,'date')[1]='2026-09-12'
(H/(NAME+'.kicad_sch')).write_text(sx.dumps(s))
subprocess.run([K,'sch','export','netlist','--format','kicadxml','-o',str(E/(NAME+'.net.xml')),str(H/(NAME+'.kicad_sch'))],check=True)
shutil.copy2(D/'leaf-heat-v4.kicad_pro',H/(NAME+'.kicad_pro'))
shutil.copy2(D/'leaf-heat-v4.kicad_dru',H/(NAME+'.kicad_dru'))
b=p.LoadBoard(str(D/'leaf-heat-v4.kicad_pcb'))
for item in list(b.GetTracks())+list(b.Zones())+list(b.GetDrawings()):b.RemoveNative(item)
fps={f.GetReference():f for f in b.GetFootprints()}
fps['D1'].SetField('MPN',d1['mpn']);fps['D1'].SetValue(d1['value'])
positions={
 'U1':(24,19,0),'L1':(30,11,0),'C1':(11.5,21,90),'C2':(18,17.7,90),
 'C3':(33,25,0),'C4':(32,18,90),'C5':(43,11,0),'C6':(43,20,0),'C7':(43,29,0),
 'R1':(22,29,90),'R2':(30,29,0),'D3':(43,58,90),'D1':(43,69,270),'F1':(43,82,90),
 'J1':(16,91,0),'U3':(27,70,270),'C12':(26.365,62,90),'C13':(18,77,180),'R10':(38,76,0),'D4':(24,83,90),
 'U2':(73,8,0),'C9':(54,10,180),'C10':(60.5,3,180),'C8':(54,19,0),'R3':(54,28,0),
 'R5':(58,37,0),'R6':(71,37,0),'C11':(91,8,0),'R7':(91,16,0),'R8':(91,24,90),'R4':(91,35,90),
 'R18':(91,45,0),'R19':(91,54,180),'R20':(80,54,0),'R9':(53,47,0),'D6':(65,47,180),
 'SW1':(59,65,0),'SW2':(78,65,0),'C14':(76.81,80,90),'U4':(76.81,87,90),'J3':(73,92,90),
 'TP1':(8,42,0),'TP2':(49,91,0),'TP3':(29,53,0),'TP4':(37,42,0),'TP5':(9,83,0),'TP6':(9,76,0),'TP7':(54,68,0),
 'H1':(4,4,0),'H2':(96,4,0),'H3':(45,96,0),'H4':(96,96,0)}
assert set(positions)==set(fps)
for ref,f in fps.items():
    x,y,a=positions[ref];f.SetPosition(v((x,y)));f.SetOrientationDegrees(a)
    f.Value().SetVisible(False)
    if ref.startswith('H'):f.Reference().SetVisible(False)
for q in parts+tests:q['xy']=list(positions[q['ref']][:2]);q['rotation']=positions[q['ref']][2]
for a,c in [((0,0),(W,0)),((W,0),(W,HT)),((W,HT),(0,HT)),((0,HT),(0,0))]:
    d=p.PCB_SHAPE(b);d.SetShape(p.SHAPE_T_SEGMENT);d.SetStart(v(a));d.SetEnd(v(c));d.SetWidth(p.FromMM(.05));d.SetLayer(p.Edge_Cuts);b.Add(d)
b.GetDesignSettings().SetAuxOrigin(v((0,HT)));b.GetTitleBlock().SetRevision('E')
b.GetTitleBlock().SetTitle('Leaf Heat - spaced hand-solder prototype')
def pt(ref,num):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition())
def path(n,pts,w=.3,layer=p.F_Cu,physical=False):
    for a,c in zip(pts,pts[1:]):
        if math.dist(a,c)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(c));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);b.Add(t)
def via(n,at,physical=False):
    t=p.PCB_VIA(b);t.SetPosition(v(at));t.SetWidth(p.FromMM(.7));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(b.FindNet('/'+n));t.SetLocked(True);t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(t)
def zone(n,layer,points,name,priority=1):
    z=p.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet('/'+n));z.SetLocalClearance(p.FromMM(.25));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(p.FromMM(.3));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.2));z.SetAssignedPriority(priority);z.SetZoneName(name)
    poly=z.Outline();poly.NewOutline()
    for q in points:poly.Append(v(q))
    b.Add(z)
# Input, switching and bootstrap connections stay local. The output capacitor
# bank and feedback resistors gain access without enlarging the input hot loop.
path('VPWR',[pt('C2',1),(20,19.2625),(20,18.365),pt('U1',2)],.5)
path('VPWR',[pt('U1',2),pt('U1',3)],.5)
path('GND',[pt('C2',2),(20,16.1375),pt('U1',1)],.5)
path('BUCK_SW',[pt('U1',8),(28,15.97),(28,11.075),pt('L1',1)],.8)
path('BUCK_SW',[pt('U1',8),(29,17.095),(29.6575,16.4375),pt('C4',2)],.5)
path('BUCK_BOOT',[pt('U1',7),(29,18.365),(30.1975,19.5625),pt('C4',1)],.5)
path('BUCK_VCC',[pt('U1',6),(29,19.635),(30,20.635),(30,23.5625),pt('C3',1)],.4)
path('BUCK_FB',[pt('U1',5),(26.875,27.425),pt('R2',1)],.3)
path('BUCK_FB',[pt('R1',2),(23.825,27.45),(25.375,29),pt('R2',1)],.3)
path('3V3',[pt('C7',1),(39.5,30.9375),(39.5,36),(22,36),pt('R1',1)],.3)
path('CAR_12V',[pt('J1',9),(28,96.145),(40,96.145),(43,93.145),(43,91),pt('TP2',1)],1,p.B_Cu)
via('CAR_12V',(43,88));path('CAR_12V',[(43,91),(43,88)],1,p.B_Cu);path('CAR_12V',[(43,88),pt('F1',1)],1)
path('CAR_FUSED',[pt('F1',2),pt('D1',2)],1)
vpwr=[(7,13),(21,13),(21,17),(23,17),(23,24),(21,26),(21,51),(47,51),(47,54),(49,54),(89,14),(90.5,14),(90.5,17.5),(89,17.5),(50.5,56),(47,56),(47,73),(39,73),(39,59),(7,59)]
zone('VPWR',p.In2_Cu,vpwr,'Protected input distribution',4)
zone('VPWR',p.F_Cu,[(10,21),(14,21),(18,18.9),(20.4,18.9),(20.4,21),(16,23.6),(10,23.6)],'Input bypass copper',5)
zone('3V3',p.F_Cu,[(31.8,8.5),(41.8,8.5),(41.8,30.4),(39.8,30.4),(39.8,14),(31.8,14)],'Buck output capacitor bank',5)
zone('3V3',p.In2_Cu,[(1,1),(99,1),(99,99),(1,99)],'3V3 distribution',2)
# Direct CAN connection via the protection pads; no termination is added.
path('CAN_L',[pt('J1',2),(18.77,88.78),pt('D4',1),(20.3,84.5),(20.3,80.8),(26.365,74.735),pt('U3',6)],.3)
path('CAN_H',[pt('J1',7),(20.155,89.84),(24.95,85.045),pt('D4',2),(24.95,81.185),(27.635,78.5),pt('U3',7)],.3)
path('CAN_L',[pt('TP6',1),(25.1,76),(25.365,75.735)],.3,p.B_Cu);via('CAN_L',(25.365,75.735))
path('CAN_H',[pt('TP5',1),(24.45,83),(24.95,82.5)],.3,p.B_Cu);via('CAN_H',(24.95,82.5))
# Short external UART protection path and local clamp decoupling.
for n,u,j in [('PROG_RX',1,2),('PROG_TX',3,3)]:
    path(n,[pt('U4',u),pt('U4',7-u)])
    a=pt('U4',u);z=pt('J3',j);path(n,[a,(a[0],z[1]-abs(a[0]-z[0])),z])
path('3V3',[pt('C14',1),pt('U4',5)],.4)
# Module and CAN supply bypasses. GPIO pull-ups are deliberately farther apart.
path('3V3',[pt('C10',1),pt('U2',1)],.5)
path('3V3',[pt('C9',1),(59,10),(62,7),(62,2),pt('U2',1)],.5)
path('3V3',[pt('C12',1),pt('U3',3)],.4)
path('3V3',[pt('C13',1),(23,77),(25.095,74.905),pt('U3',5)],.4)

def rect(q):
    r=q.GetBoundingBox();return (p.ToMM(r.GetLeft()),p.ToMM(r.GetTop()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))
def dist_rect(at,r):return math.hypot(max(r[0]-at[0],0,at[0]-r[2]),max(r[1]-at[1],0,at[1]-r[3]))
def dist_seg(q,a,c):
    dx=c[0]-a[0];dy=c[1]-a[1];length=dx*dx+dy*dy;t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/length)) if length else 0
    return math.dist(q,(a[0]+t*dx,a[1]+t*dy))
def free(at,n):
    if not(1<at[0]<W-1 and 1.5<at[1]<HT-1):return False
    for f in fps.values():
        for pad in f.Pads():
            if dist_rect(at,rect(pad))<.65:return False
        for z in f.Zones():
            if z.GetIsRuleArea() and z.Outline().Contains(v(at)):return False
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
        if clear:path(n,[a,z],.4);via(n,z);return
    raise RuntimeError(('No plane via',ref,num,n))
seen=set()
for ref,f in fps.items():
    for pad in f.Pads():
        key=(ref,pad.GetNumber());n=pad.GetNetname().lstrip('/')
        if key in seen:continue
        seen.add(key)
        if pad.GetAttribute()==p.PAD_ATTRIB_SMD and n in {'GND','3V3','VPWR'} and key not in {('U1','9'),('U1','2'),('U1','3'),('U2','19'),('R1','1'),('L1','2')}:drop(ref,pad.GetNumber(),n)
for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:zone('GND',layer,[(.4,.4),(99.6,.4),(99.6,99.6),(.4,99.6)],'Ground reference' if layer==p.In1_Cu else 'Ground '+b.GetLayerName(layer),0)
for y in [3,10,20,30,40,50,60,70,80,90,97]:
    for x in [3,8,20,35,48,60,75,88,97]:
        if free((x,y),'GND'):via('GND',(x,y))
def label(txt,at,size=1,layer=p.F_SilkS,left=False):
    t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(at));t.SetTextSize(v((size,size)));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer)
    if layer==p.B_SilkS:t.SetMirrored(True)
    if left:t.SetHorizJustify(p.GR_TEXT_H_ALIGN_LEFT)
    b.Add(t)
label('LEAF HEAT / REV E',(25,3),1.3)
label('100 x 100 mm / HAND SOLDER',(74,59),1)
label('FACTORY: U1 U2 U4 L1',(72,62),.85)
label('12V:9  GND:3  H:7  L:2',(25,98.8),.85)
label('NISSAN ZE0 CABLE ONLY',(25,96.2),.9)
label('UART / 3.3V LOGIC',(75,98),.9)
for txt,at in [('GND',(73,95)),('RX',(75.54,95)),('TX',(78.08,95))]:label(txt,at,.85)
label('NO POWER PIN',(90,87),.8)
label('RESET',(62.25,73),1.1);label('BOOT',(81.25,73),1.1)
label('K',(67.9,47),.85)
for q in tests:label(q['value'],(q['xy'][0],q['xy'][1]+3.3),.9)
# Put the reference table on the back, leaving top-side access to actual parts.
import collections
groups=collections.defaultdict(list)
for q in parts:
    if q['assembly']=='HAND':groups[q['mpn']].append(q)
label('REV E / 100 x 100 mm / HAND PARTS',(50,7),1.3,p.B_SilkS)
short={'J1':'DB9 male','J3':'3-pin UART','U3':'TCAN3403DRQ1','D4':'PESD2CAN','D1':'B1100 / 100V','D6':'GREEN LED / K=cathode','SW1':'RESET / BOOT buttons'}
for i,qs in enumerate(groups.values()):
    # Mirrored left-justified text is right-anchored in a view from above.
    label(' '.join(q['ref'] for q in qs),(93,12+i*2.45),.85,p.B_SilkS,True)
    label(short.get(qs[0]['ref'],qs[0]['value']),(54,12+i*2.45),.85,p.B_SilkS,True)
label('FACTORY FITS U1 U2 U4 L1 ONLY',(50,63),1.1,p.B_SilkS)
label('COMPLETE HAND ASSEMBLY BEFORE POWER',(30,68),1,p.B_SilkS)
label('NO CAN TERMINATION',(72,77),.9,p.B_SilkS)
label('UART HAS NO POWER PIN',(74,80),.9,p.B_SilkS)
def overlap(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]
def padded(item,m):r=rect(item);return (r[0]-m,r[1]-m,r[2]+m,r[3]+m)
blocks=[]
for f in fps.values():
    blocks.extend(padded(q,.3) for q in f.Pads());blocks.extend(padded(q,.18) for q in f.GraphicalItems() if q.GetLayer()==p.F_SilkS)
blocks.extend(padded(q,.2) for q in b.GetDrawings() if isinstance(q,p.PCB_TEXT) and q.GetLayer()==p.F_SilkS)
for ref,f in sorted(fps.items()):
    if ref.startswith('H'):continue
    t=f.Reference();t.SetVisible(True);t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetTextSize(v((1,1)));t.SetTextThickness(p.FromMM(.15));x,y=xy(f.GetPosition())
    candidates=[]
    if ref=='U2':candidates.append((73,18))
    if ref=='J1':candidates.append((36,88))
    for rad in [2.5,3,3.5,4,4.5,5,6,7,8]:
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0),(-.7,-.7),(.7,-.7),(-.7,.7),(.7,.7)]:candidates.append((x+rad*dx,y+rad*dy))
    for at in candidates:
        t.SetPosition(v(at));r=padded(t,.18)
        if r[0]<.5 or r[1]<.5 or r[2]>W-.5 or r[3]>HT-.5:continue
        if not any(overlap(r,q) for q in blocks):blocks.append(r);break
    else:raise RuntimeError('No reference position '+ref)
b.BuildConnectivity();p.SaveBoard(str(H/(NAME+'.kicad_pcb')),b)
(H/'parts.json').write_text(json.dumps(parts,indent=2)+'\n');(H/'testpoints.json').write_text(json.dumps(tests,indent=2)+'\n')
print('Rev E 100 x 100 mm placed with critical routes, planes and unchanged 41-part circuit.')

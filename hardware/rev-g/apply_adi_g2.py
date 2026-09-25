"""One-time G.1 -> G.2 layout cleanup. Requires the archived G.1 baseline."""
from pathlib import Path
import hashlib, json, math
import pcbnew as p
import sexpdata as sx

H = Path(__file__).resolve().parent
B = H / 'leaf-heat-v7.kicad_pcb'
assert (H / 'history/rev-g1-before-adi-g2.zip').exists()
assert hashlib.sha256(B.read_bytes()).hexdigest() == '2378869bff9072b5c0786ff13958ee783a395fc549dffc6d7a9f5f7e3b53f409'
b = p.LoadBoard(str(B))
def xy(v): return tuple(round(p.ToMM(n), 6) for n in (v.x, v.y))
def vec(q): return p.VECTOR2I(*(p.FromMM(n) for n in q))
def remove(net, a, c, layer):
    found = [t for t in b.GetTracks() if not isinstance(t, p.PCB_VIA)
             and t.GetNetname() == '/' + net and t.GetLayer() == layer
             and {xy(t.GetStart()), xy(t.GetEnd())} == {a, c}]
    assert len(found) == 1, (net, a, c, len(found))
    b.RemoveNative(found[0])
def path(net, points, width, layer):
    for a, c in zip(points, points[1:]):
        t = p.PCB_TRACK(b)
        t.SetStart(vec(a)); t.SetEnd(vec(c)); t.SetWidth(p.FromMM(width))
        t.SetLayer(layer); t.SetNet(b.FindNet('/' + net)); b.Add(t)
def move_via(net, old, new):
    found = [t for t in b.GetTracks() if isinstance(t, p.PCB_VIA)
             and t.GetNetname() == '/' + net and xy(t.GetPosition()) == old]
    assert len(found) == 1
    found[0].SetPosition(vec(new))

# Feed C10's positive pad, then U2 pin 1, without the redundant copper loop.
for a, c in [((59., 10.), (62., 7.)), ((62., 7.), (62., 2.)),
             ((62., 2.), (64.25, 2.)), ((62.0625, 3.), (64.25, 2.))]:
    remove('3V3', a, c, p.F_Cu)
path('3V3', [(59., 10.), (62.0625, 6.9375), (62.0625, 3.),
             (63.0625, 2.), (64.25, 2.)], .5, p.F_Cu)

# R19 UART_RX: move the via below the pad, away from the PROG_TX track.
old = (87.1531, 52.9642); new = (89.45, 56.)
remove('UART_RX', old, (88.4142, 52.9642), p.F_Cu)
remove('UART_RX', (88.4142, 52.9642), (89.45, 54.), p.F_Cu)
remove('UART_RX', (85.556, 51.3671), old, p.B_Cu)
move_via('UART_RX', old, new)
path('UART_RX', [(89.45, 54.), new], .3, p.F_Cu)
path('UART_RX', [(85.556, 51.3671), (89.45, 55.2611), new], .3, p.B_Cu)

# D4 CAN_H: keep the existing CAN signal route; relocate the test-point via
# onto its diagonal segment, clear of D4's ground pad. No extra top stub.
old = (24.95, 82.5); new = (26.5, 79.635)
move_via('CAN_H', old, new)
remove('CAN_H', (9., 83.), (24.45, 83.), p.B_Cu)
remove('CAN_H', (24.45, 83.), old, p.B_Cu)
path('CAN_H', [(9., 83.), (23.135, 83.), new], .3, p.B_Cu)
remove('CAN_H', (24.95, 81.185), (27.635, 78.5), p.F_Cu)
path('CAN_H', [(24.95, 81.185), new, (27.635, 78.5)], .3, p.F_Cu)

# JLCPCB legend minima: 1.0 mm height, 0.15 mm stroke, 0.15 mm pad gap.
texts = []
for f in b.GetFootprints():
    texts.extend([f.Reference(), f.Value(), *list(f.GraphicalItems())])
texts.extend(list(b.GetDrawings()))
for t in texts:
    if isinstance(t, p.PCB_TEXT) and t.IsVisible() and t.GetLayer() in (p.F_SilkS, p.B_SilkS):
        size = t.GetTextSize()
        if size.y < p.FromMM(1.):
            t.SetTextSize(p.VECTOR2I(round(size.x * p.FromMM(1.) / size.y), p.FromMM(1.)))
        t.SetTextThickness(max(t.GetTextThickness(), p.FromMM(.15)))
        t.SetText(t.GetText().replace('REV G', 'REV G.2'))
        if t.GetLayer() == p.F_SilkS and t.GetText() == 'K':
            t.SetPosition(vec((69., 47.)))
    elif isinstance(t, p.PCB_SHAPE) and t.GetLayer() in (p.F_SilkS, p.B_SilkS):
        t.SetWidth(max(t.GetWidth(), p.FromMM(.15)))
# Place crowded reference labels in nearby clear areas, horizontal for reading.
ref_positions = {'C2':(17.,15.4), 'R1':(17.,26.), 'R2':(24.5,29.5),
    'C3':(33.1,23.3), 'C8':(54.,21.5), 'R3':(54.,30.5),
    'R7':(95.,16.), 'R8':(95.,24.), 'R10':(38.,78.5),
    'R24':(29.,40.), 'R25':(29.,34.), 'C17':(5.5,54.), 'D4':(18.,81.)}
for f in b.GetFootprints():
    if f.GetReference() in ref_positions:
        t = f.Reference(); t.SetPosition(vec(ref_positions[f.GetReference()]))
        t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
for t in b.GetDrawings():
    if not isinstance(t,p.PCB_TEXT) or t.GetLayer()!=p.F_SilkS: continue
    at = {'VPWR':(29.,58.3), 'FACTORY: U1 U2 U4 U5 U6 L1':(57.,57.),
          '100 x 100 mm / HAND SOLDER':(60.,59.5), 'RX':(75.54,95.5), 'TX':(78.5,95.5)}.get(t.GetText())
    if t.GetText()=='GND' and xy(t.GetPosition())==(73.,95.): at=(72.5,95.5)
    if at: t.SetPosition(vec(at))
b.GetTitleBlock().SetRevision('G.2')
b.BuildConnectivity()
p.SaveBoard(str(B), b)

pro = H / 'leaf-heat-v7.kicad_pro'
d = json.loads(pro.read_text())
rules = d['board']['design_settings']['rules']
rules.update(min_silk_clearance=.15, min_text_height=1., min_text_thickness=.15)
pro.write_text(json.dumps(d, indent=2) + '\n')

# Circuit unchanged; make the drawing's revision and factory scope accurate.
sch = H / 'leaf-heat-v7.kicad_sch'
q = sx.loads(sch.read_text())
def edit(node):
    if not isinstance(node, list): return
    if node and str(node[0]) == 'rev': node[1] = 'G.2'
    if node and str(node[0]) == 'text':
        node[1] = node[1].replace('Rev G', 'Rev G.2').replace('REV G', 'REV G.2')
        node[1] = node[1].replace('FACTORY: U1 U2 U4 L1', 'FACTORY: U1 U2 U4 U5 U6 L1').replace('FACTORY: U1 / U2 / U4 / L1', 'FACTORY: U1 / U2 / U4 / U5 / U6 / L1')
    for item in node: edit(item)
edit(q)
sch.write_text(sx.dumps(q))
print('G.2 initial cleanup applied; refill and full validation are required.')

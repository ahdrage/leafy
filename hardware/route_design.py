"""Local, deterministic critical routing before Freerouting.

Run after build_design.py. Adds short power loops and USB data connections.
KiCad's DRC, rather than this script, is the authority on clearance/connectivity.
"""
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'leaf-heat-v1.kicad_pcb'))
def v(xy):return p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1]))
def net(n):return b.FindNet('/'+n)
def path(n,points,w=.25,layer=p.F_Cu):
 for a,z in zip(points,points[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNet(net(n));t.SetLocked(True);b.Add(t)
def via(n,xy):
 t=p.PCB_VIA(b);t.SetPosition(v(xy));t.SetWidth(p.FromMM(.65));t.SetDrill(p.FromMM(.3));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(net(n));t.SetLocked(True);b.Add(t)

path('VPWR',[(16.125,11.365),(16.125,12.635)],.35)
path('VPWR',[(13.45,11.4),(15,11.4),(15.035,11.365),(16.125,11.365)],.5)
path('VPWR',[(12.975,7),(13.45,7.475),(13.45,11.4)],.5)
path('BUCK_SW',[(21.875,10.095),(22.925,9.045),(22.925,5.5)],.6)
path('BUCK_SW',[(21.875,10.095),(23.92,10.095),(24.225,10.4)],.4)
path('BUCK_BOOT',[(21.875,11.365),(25.775,11.365),(25.775,10.4)],.25)
path('BUCK_VCC',[(21.875,12.635),(24.36,12.635),(24.725,13)],.25)
path('BUCK_FB',[(21.875,13.905),(22.5,14.53),(22.5,14.8),(24,16.3),(24,17.325),(23.825,17.5)],.25)
path('BUCK_FB',[(23.825,17.5),(23.825,18.85),(22.175,20.5)],.25)
path('3V3',[(27.075,5.5),(30.025,5.5),(30.025,9.5),(30.025,13.5)],.8)
for a,z in [((10.025,7),(9,7)),((11.55,11.4),(10.8,12.15)),((16.125,10.095),(16.125,8.9)),((26.275,13),(27.1,13)),((7.5,13.85),(6.5,13.85)),((32.975,5.5),(34,5.5)),((32.975,9.5),(34,9.5)),((32.975,13.5),(34,13.5))]:
 path('GND',[a,z],.4);via('GND',z)

# Mirrored USB-C data pins join locally; one short bottom-layer crossing is required.
path('USB_CONN_DP',[(56.75,43.32),(56.75,41.8),(55.75,41.8),(55.05,41.1),(55.05,40.1375)],.2)
path('USB_CONN_DP',[(55.75,43.32),(55.75,41.8)],.2)
path('USB_CONN_DM',[(55.25,43.32),(55.25,44.5)],.2);via('USB_CONN_DM',(55.25,44.5))
path('USB_CONN_DM',[(56.25,43.32),(56.25,44.5)],.2);via('USB_CONN_DM',(56.25,44.5))
path('USB_CONN_DM',[(55.25,44.5),(56.25,44.5),(57.3,43.45),(57.3,41.3)],.2,p.B_Cu);via('USB_CONN_DM',(57.3,41.3))
path('USB_CONN_DM',[(57.3,41.3),(56.95,40.95),(56.95,40.1375)],.2)
path('USB_CONN_DP',[(55.05,40.1375),(55.05,37.8625),(55.05,36.4)],.2);via('USB_CONN_DP',(55.05,36.4))
path('USB_CONN_DM',[(56.95,40.1375),(56.95,37.8625),(57.6,37.2125),(57.6,36.8)],.2);via('USB_CONN_DM',(57.6,36.8))
path('USB_CONN_DP',[(55.05,36.4),(57,34.45),(57,21.9),(60.4,18.5),(62.5,18.5),(62.5,20.5)],.2,p.B_Cu);via('USB_CONN_DP',(62.5,20.5))
path('USB_CONN_DP',[(62.5,20.5),(62.175,20.5),(61.5,19.825)],.2)
path('USB_CONN_DM',[(57.6,36.8),(57.6,22.5),(59,21.1)],.2,p.B_Cu);via('USB_CONN_DM',(59,21.1))
path('USB_CONN_DM',[(59,21.1),(59,19.825)],.2)

b.BuildConnectivity()
p.SaveBoard(str(H/'leaf-heat-v1.kicad_pcb'),b)
assert p.ExportSpecctraDSN(b,str(H/'exports'/'leaf-heat-v1.dsn'))
print('Critical routes saved and local-router input exported.')

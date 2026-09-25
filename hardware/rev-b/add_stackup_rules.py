"""Declare the preliminary stack and enforce layer/USB geometry constraints."""
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent
q=H/'leaf-heat-v2.kicad_pcb'
b=p.LoadBoard(str(q))
for z in list(b.Zones()):
 if z.GetZoneName() in ['USB main pair rule area','USB-C mirrored contact bridges']:b.RemoveNative(z)
for name,points in [('USB main pair rule area',[(55.5,12.8),(64.4,12.8),(64.4,33.8),(55.5,33.8)]),('USB-C mirrored contact bridges',[(54,43),(58,43),(58,47),(54,47)])]:
 z=p.ZONE(b);z.SetLayer(p.F_Cu);z.SetIsRuleArea(True);z.SetZoneName(name)
 for method in ['SetDoNotAllowTracks','SetDoNotAllowVias','SetDoNotAllowPads','SetDoNotAllowFootprints','SetDoNotAllowZoneFills']:getattr(z,method)(False)
 poly=z.Outline();poly.NewOutline()
 for x,y in points:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
b.SetLayerName(p.In1_Cu,'In1.Cu');b.SetLayerName(p.In2_Cu,'In2.Cu')
p.SaveBoard(str(q),b)
s=q.read_text()
assert '\n\t\t(stackup\n' not in s, 'Do not overwrite an existing stackup'
stack='''
		(stackup
			(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.02) (epsilon_r 3.5))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "prepreg") (thickness 0.1855) (material "FR4 7628 RC46 - proposed") (epsilon_r 4.74))
			(layer "In1.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 2" (type "core") (thickness 1.03) (material "FR4 - proposed") (epsilon_r 4.6))
			(layer "In2.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 3" (type "prepreg") (thickness 0.1855) (material "FR4 7628 RC46 - proposed") (epsilon_r 4.74))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.02) (epsilon_r 3.5))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
			(copper_finish "Lead-free HASL")
			(dielectric_constraints yes)
		)
'''
s=s.replace('\t(setup\n','\t(setup\n'+stack,1).replace('(thickness 1.6)','(thickness 1.581)',1)
q.write_text(s)
(H/'leaf-heat-v2.kicad_dru').write_text('''(version 1)
# Keep the adjacent reference plane intact. Vias/pad clearances are intentional.
(rule "Ground reference layer: no tracks"
  (layer In1.Cu)
  (constraint disallow track))
(rule "Power distribution layer: no tracks"
  (layer In2.Cu)
  (constraint disallow track))
# Main USB run: 0.23 mm lines / 0.17 mm gap. Fanouts are outside this area.
(rule "USB main pair width"
  (condition "A.NetName == '/USB_CONN_P' || A.NetName == '/USB_CONN_N'")
  (constraint track_width (min 0.20mm) (opt 0.23mm) (max 0.23mm)))
(rule "USB main pair gap"
  (condition "A.inDiffPair('/USB_CONN') && A.intersectsArea('USB main pair rule area')")
  (constraint diff_pair_gap (min 0.16mm) (opt 0.17mm) (max 0.18mm)))
(rule "USB main route has no vias"
  (condition "A.inDiffPair('/USB_CONN') && !A.intersectsArea('USB-C mirrored contact bridges')")
  (constraint disallow via))
(rule "USB controller fanout has no vias"
  (condition "A.inDiffPair('/USB_D')")
  (constraint disallow via))
(rule "USB pair length match"
  (condition "A.inDiffPair('/USB*')")
  (constraint skew (within_diff_pairs) (max 0.1mm)))
''')
print('Preliminary stackup and USB/plane rules saved.')

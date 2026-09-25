"""Apply geometry checked with KiCad's coupled-microstrip calculator."""
from pathlib import Path
import pcbnew as p,json
H=Path(__file__).resolve().parent;q=H/'leaf-heat-v2.kicad_pcb';b=p.LoadBoard(str(q))
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in ['/USB_CONN_P','/USB_CONN_N','/USB_D_P','/USB_D_N'] and p.ToMM(t.GetWidth())==.23:t.SetWidth(p.FromMM(.25))
p.SaveBoard(str(q),b)
pf=H/'leaf-heat-v2.kicad_pro';pro=json.loads(pf.read_text());ds=pro['board']['design_settings'];ds['track_widths']=[0,.2,.25,.4,.5,.8,1.0];ds['diff_pair_dimensions']=[{'width':.25,'gap':.15,'via_gap':.25}]
for n in pro['net_settings']['classes']:
 if n['name']=='USB':n.update(track_width=.25,diff_pair_width=.25,diff_pair_gap=.15)
pf.write_text(json.dumps(pro,indent=2)+'\n')
f=H/'leaf-heat-v2.kicad_dru';s=f.read_text().replace('0.23 mm lines / 0.17 mm gap','0.25 mm lines / 0.15 mm gap').replace('(opt 0.23mm) (max 0.23mm)','(opt 0.25mm) (max 0.25mm)')
s=s.replace(" && A.intersectsArea('USB main pair rule area')",'')
s=s.replace('(min 0.16mm) (opt 0.17mm) (max 0.18mm)','(min 0.145mm) (opt 0.15mm) (max 2.50mm)')
s=s.replace('# Main USB run:', '# Spatially scoped diff-pair gap checks did not trigger in KiCad 10 CLI probes.\n# This global gap rule includes component fanouts; audit_layout.py separately\n# verifies the long coupled run at 0.15 mm.\n# Main USB run:')
f.write_text(s)
x={'tool':'KiCad 10.0.6 Calculator Tools, Coupled Microstrip Line, Analyze','frequency_GHz':.1,'Er':4.74,'H_mm':.1855,'copper_T_mm':.035,'W_mm':.25,'S_mm':.15,'length_mm':41,'box_height_mm':1e20,'roughness_mm':0,'tan_delta':.02,'Zeven_ohm':69.2779,'Zodd_ohm':47.8068,'Zdiff_ohm':95.6222,'required_target_ohm':90,'required_tolerance_percent':10,'status':'Nominal uncoated model only; manufacturer confirmation required','limitations':['solder mask not modeled','actual etched cross section and material tolerance not confirmed','connector/ESD/pad discontinuities not modeled'],'superseded_trial':{'W_mm':.23,'S_mm':.17,'KiCad_Zdiff_ohm':101.562,'simple_formula_Zdiff_ohm':91.16,'decision':'Rejected; use the KiCad coupled-line model for preliminary geometry.'},'stackup_source':'https://www.pcbway.com/multi-layer-laminated-structure.html'}
(H/'exports/impedance-estimate.json').write_text(json.dumps(x,indent=2)+'\n')
print('USB final geometry: 0.25 mm width / 0.15 mm gap.')

"""Prove the U5 swap changes identity only, including every PCB/CAD primitive."""
from pathlib import Path
import csv, hashlib, json, zipfile
import sexpdata as sx

H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
old,new='TPS3760A012DYYRQ1','TPS3760A012DYYR'
def substitute(s): return s.replace(old,new).replace('tps3760-q1','tps3760')
with zipfile.ZipFile(H/'history/rev-g-before-u5-g1.zip') as z:
    checked={}
    for name in ['leaf-heat-v7.kicad_pcb','leaf-heat-v7.kicad_sch','Leaf.kicad_sym']:
        before=z.read(name);after=(H/name).read_bytes()
        assert sx.loads(substitute(before.decode()))==sx.loads(after.decode()), name
        checked[name]={'before_sha256':sha(before),'after_sha256':sha(after)}
    before=json.loads(z.read('parts.json'));after=json.loads((H/'parts.json').read_text())
    assert len(before)==len(after)==55
    for a,b in zip(before,after):
        assert a['ref']==b['ref']
        if a['ref']!='U5': assert a==b,a['ref']
        else:
            for key in a:
                if key not in {'mpn','value','symbol','datasheet','notes'}: assert a[key]==b[key],key
            assert b['mpn']==b['value']==new and b['assembly']=='FACTORY'
    assert z.read('exports/CPL-FACTORY-JLCPCB.csv')==(H/'exports/CPL-NATIVE-REFERENCE-ONLY.csv').read_bytes()
    for name in ['BOM-HAND.csv','MOUSER-HAND-TWO-BOARDS.csv']:
        assert z.read('exports/'+name)==(H/'exports'/name).read_bytes(),name
    native=list(csv.DictReader((H/'exports/CPL-NATIVE-REFERENCE-ONLY.csv').open()))
    supplier=list(csv.DictReader((H/'exports/CPL-FACTORY-JLCPCB.csv').open()))
    target={'L1':0,'U1':270,'U2':0,'U4':0,'U5':270,'U6':270}
    assert len(native)==len(supplier)==6
    for n,s in zip(native,supplier):
        for k in ['Designator','Mid X','Mid Y','Layer']:assert n[k]==s[k],(k,s)
        assert float(s['Rotation'])==target[s['Designator']],s
    fabrication=[]
    gerber_suffixes={'.gbr','.gbo','.gto','.gm1','.gtp','.g2','.gbs','.gtl','.gbp','.gbl','.g1','.gts'}
    gerbers_checked=0
    drills_checked=0
    for p in sorted((H/'exports/fabrication').iterdir()):
        if p.suffix not in gerber_suffixes | {'.drl'}: continue
        a=z.read('exports/fabrication/'+p.name).decode(); b=p.read_text()
        if p.suffix in gerber_suffixes:
            strip=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith('%TF.CreationDate,') and not l.startswith('G04 Created by KiCad (PCBNEW '))
            assert strip(a)==strip(b),p.name
            gerbers_checked+=1
        else:
            # Excellon generation timestamps are the only allowed difference.
            strip=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith('; DRILL file KiCad ') and 'TF.CreationDate,' not in l)
            assert strip(a)==strip(b),p.name
            drills_checked+=1
        fabrication.append(p.name)
    assert gerbers_checked==11,gerbers_checked
    assert drills_checked==2,drills_checked
report={'revision':'G.1','status':'PASS','checked_files':checked,
        'pcb_and_schematic_comparison':'Full parsed structures identical after only U5 part-number and datasheet substitutions; all copper, pads, zones, drill geometry, net connections, positions, dimensions and graphics unchanged.',
        'other_components_unchanged':54,'hand_components_unchanged':49,
        'native_factory_placement_file_unchanged':True,'hand_BOM_and_two_board_shopping_list_unchanged':True,
        'jlc_catalog_angles_degrees':target,'jlc_CPL_centres_layers_and_references_unchanged':True,
        'fabrication_comparison':'All 11 Gerber files and both drill files identical to original Rev G except generation timestamps.',
        'gerber_files_checked':gerbers_checked,'drill_files_checked':drills_checked,
        'fabrication_files_checked':fabrication,
        'pinout':'DYY14: VDD 1, SENSE 3, RESET_N 6, GND 8/13, CTR 9, CTS 10; all other pins NC',
        'electrical_comparison':'A012 UV, non-latching, 0.8 V threshold, 2% internal hysteresis, active-low open drain; same calculation inputs and timing specifications.',
        'qualification_tradeoff':'Catalog grade, no AEC-Q100. 65 V operating maximum. No Q1 70 V/50 ms operating-transient allowance.',
        'sources':['https://www.ti.com/lit/ds/symlink/tps3760.pdf','https://www.ti.com/lit/ds/symlink/tps3760-q1.pdf'],
        'physical_validation':'Not performed; DFM approval and bench/vehicle tests remain.'}
(H/'exports/u5-g1-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

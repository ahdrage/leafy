"""Export local router input with non-overlapping representations of planes.

The manufacturing board retains KiCad's priority-based zones. Specctra DSN does
not carry those priorities, so this interchange view uses an explicit window.
Only outer layers accept routes; native DRC validates the imported result.
"""
from pathlib import Path
import re,pcbnew as p,shutil
H=Path(__file__).resolve().parent;E=H/'exports'
b=p.LoadBoard(str(H/'leaf-heat-v7.kicad_pcb'))
shutil.copy2(H/'leaf-heat-v7.kicad_pcb',E/'before-router.kicad_pcb')
assert p.ExportSpecctraDSN(b,str(E/'leaf-heat-v7.dsn'))
s=(E/'leaf-heat-v7.dsn').read_text()
def replace(m):
    t=m.group()
    if t.startswith('(plane /GND') and not '(polygon In1.Cu' in t:return ''
    if t.startswith('(plane /3V3 (polygon In2.Cu'):
        points=[(6.6,12.6),(21.4,12.6),(21.4,16.6),(23.4,16.6),(23.4,24.2),(21.4,26.2),(21.4,50.6),(47.4,50.6),(47.4,53.6),(48.8343,53.6),(88.8343,13.6),(90.9,13.6),(90.9,17.9),(89.1657,17.9),(50.6657,56.4),(47.4,56.4),(47.4,73.4),(38.6,73.4),(38.6,59.4),(6.6,59.4),(6.6,12.6)]
        poly=' '.join(f'{x*1000:.1f} {-y*1000:.1f}' for x,y in points)
        return t[:-1]+' (window (polygon In2.Cu 0 '+poly+')))'
    return t
s=re.sub(r'\(plane\s+[^()]+\(polygon\s+[^()]+\)\)',replace,s)
s=s.replace('(clearance 50 (type smd_smd))','(clearance 200 (type smd_smd))')
(E/'leaf-heat-v7-routing.dsn').write_text(s)
print('Exported conservative non-overlapping plane representation for local outer-layer routing.')

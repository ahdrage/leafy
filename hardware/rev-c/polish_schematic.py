"""Keep long fields and the regulator ground labels readable on the A3 sheet."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import build_design as g
import sexpdata as sx

def polish(s):
    positions={'C1':(111.76,76.2,'right'),'C11':(393.7,55.88,None),'D4':(375.92,182.88,None)}
    for inst in g.children(s,'symbol'):
        fields=g.children(inst,'property')
        ref=next((x[2] for x in fields if x[1]=='Reference'),None)
        if ref not in positions:continue
        x,y,just=positions[ref]
        for prop in fields:
            if prop[1] in ['Reference','Value']:
                g.child(prop,'at')[1:]=[x,y+(2.54 if prop[1]=='Value' else 0),0]
                prop[-1]=g.effects(1.27 if prop[1]=='Reference' else 1.0,justify=just)
    g.child(g.child(s,'title_block'),'rev')[1]='C'
    if any(g.child(t,'uuid') and g.child(t,'uuid')[1]==g.uid('U1-label-9') for t in g.children(s,'label')):
        s[:]=[t for t in s if not (isinstance(t,list) and g.child(t,'uuid') and g.child(t,'uuid')[1]==g.uid('U1-label-9'))]
        for t in g.children(s,'wire'):
            if g.child(t,'uuid')[1]==g.uid('U1-wire-1'):g.children(g.child(t,'pts'),'xy')[1][2]=91.44
        for t in g.children(s,'label'):
            if g.child(t,'uuid')[1]==g.uid('U1-label-1'):g.child(t,'at')[2]=91.44
        s.append(g.node('wire',g.node('pts',g.node('xy',160.02,88.9),g.node('xy',157.48,88.9)),g.node('stroke',g.node('width',0),g.node('type',g.S('default'))),g.node('uuid',g.uid('U1-ground-link'))))
        s.append(g.node('junction',g.node('at',157.48,88.9),g.node('diameter',0),g.node('color',0,0,0,0),g.node('uuid',g.uid('U1-ground-junction'))))
    return s

if __name__=='__main__':
    f=Path(__file__).resolve().parent/'leaf-heat-v3.kicad_sch'
    f.write_text(sx.dumps(polish(sx.load(f.open()))))

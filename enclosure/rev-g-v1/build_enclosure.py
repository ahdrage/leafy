"""Build the millimetre-scale enclosure with Blender's bundled Python.

Run with Blender --background --factory-startup --python-exit-code 1 --python FILE.
The native KiCad project is read-only. Every printable solid is exported alone;
the assembled board and fasteners are labelled reference objects, never prints.
"""
from pathlib import Path
from math import sin, cos, pi, radians
import bpy
import bmesh
import json
import hashlib
import struct
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

H = Path(__file__).resolve().parent
P = json.loads((H / 'parameters.json').read_text())
G = json.loads((H / 'reference/board-geometry.json').read_text())
assert G['pcb_sha256'] == P['reference_board_sha256']
actual_mounts = [tuple([G['footprints'][r]['xy_mm'][0], -G['footprints'][r]['xy_mm'][1]]) for r in ['H1','H2','H3','H4']]
assert actual_mounts == [tuple(p) for p in P['pcb_mounts']]
assert G['thickness'] == P['pcb_thickness']

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.resolution_x = 1800
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.world.color = (0.22, 0.22, 0.22)
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

case_c = collection('01 PRINTABLE — base and lid')
ref_c = collection('02 REFERENCE — actual Rev G PCB, not for printing')
hardware_c = collection('03 REFERENCE — bought screws and nuts, not for printing')
test_c = collection('04 OPTIONAL — fit test pieces')
studio_c = collection('05 STUDIO — lights and camera')

def move_collection(o, c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o)
    return o

def material(name, color, metallic=0, roughness=0.45):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return m

base_mat = material('Warm graphite polymer', (0.045, 0.065, 0.075))
lid_mat = material('Soft pale grey polymer', (0.68, 0.74, 0.73))
steel = material('Lid screws — stainless', (0.4, 0.43, 0.45), 0.8, 0.25)
nylon = material('PCB fasteners — unfilled nylon', (0.77, 0.76, 0.64), 0, 0.38)
black = material('Black component body', (0.025, 0.026, 0.028))
gold = material('Contact metal', (0.66, 0.47, 0.16), 0.75)
white = material('Studio background', (0.79, 0.82, 0.83), 0, 0.8)

def mat(o, m):
    o.data.materials.clear(); o.data.materials.append(m)
    return o

def active(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o

def cube(name, lo, hi, c=case_c):
    bpy.ops.mesh.primitive_cube_add(size=1, location=tuple((a+b)/2 for a,b in zip(lo,hi)))
    o = bpy.context.object; o.name = name
    o.dimensions = tuple(b-a for a,b in zip(lo,hi))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return move_collection(o,c)

def cylinder(name, x, y, z0, z1, radius, vertices=64, c=case_c):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=z1-z0, location=(x,y,(z0+z1)/2))
    o=bpy.context.object; o.name=name
    return move_collection(o,c)

def round_rect(name, xmin, xmax, ymin, ymax, r, z0, z1, c=case_c):
    pts=[]
    for cx,cy,a in [(xmax-r,ymax-r,0),(xmin+r,ymax-r,90),(xmin+r,ymin+r,180),(xmax-r,ymin+r,270)]:
        for i in range(13):
            ang=radians(a+i*90/12)
            pts.append((cx+r*cos(ang),cy+r*sin(ang)))
    n=len(pts); vs=[(x,y,z) for z in [z0,z1] for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);c.objects.link(o)
    return o

def boolean(a, b, operation='DIFFERENCE'):
    active(a)
    mod=a.modifiers.new(operation,'BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=b
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(b,do_unlink=True)
    return a

def clean(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()

def nut_cut(post,x,y,z0,height,af,direction):
    # Hex cavity with a horizontal insertion channel; open face points into case.
    rad=af/(2*cos(pi/6))
    hexagon=cylinder('nut pocket cutter',x,y,z0,z0+height,rad,vertices=6)
    boolean(post,hexagon)
    if direction in ['+x','-x']:
        xmin,xmax=(x,x+12) if direction=='+x' else (x-12,x)
        channel=cube('nut insertion cutter',(xmin,y-af/2,z0),(xmax,y+af/2,z0+height))
    else:
        # Rotate the channel and hex together so a pair of flats faces the slot.
        ymin,ymax=(y,y+12) if direction=='+y' else (y-12,y)
        channel=cube('nut insertion cutter',(x-af/2,ymin,z0),(x+af/2,ymax,z0+height))
    boolean(post,channel)

def post(kind,x,y,direction):
    if kind=='pcb':
        top=P['pcb_bottom_z']; shoulder=top-2.0
        o=cylinder('PCB post',x,y,1.8,shoulder+0.05,4.5)
        boolean(o,cylinder('insulating contact land',x,y,shoulder,top,2.6),'UNION')
        bore=P['pcb_bore'];af=P['pcb_nut_pocket_af'];height=P['pcb_nut_pocket_height']
        nut_z=top-2.2-height
    else:
        top=P['lid_bottom_z'];o=cylinder('Lid post',x,y,1.8,top,5.0)
        bore=P['lid_bore'];af=P['lid_nut_pocket_af'];height=P['lid_nut_pocket_height']
        nut_z=top-2.5-height
    boolean(o,cylinder('screw bore cutter',x,y,top-11,top+1,bore/2))
    nut_cut(o,x,y,nut_z,height,af,direction)
    return o

W=P['wall'];F=P['floor'];Z=P['lid_bottom_z'];T=P['lid_thickness']
IX0,IX1=P['inner_x'];IY0,IY1=P['inner_y']
X0,X1=IX0-W,IX1+W;Y0,Y1=IY0-W,IY1+W
R=P['outer_corner_radius']
base=round_rect('BASE — print floor down',X0,X1,Y0,Y1,R,0,Z)
boolean(base,round_rect('cavity',IX0,IX1,IY0,IY1,R-W,F,Z+1))
cx=P['connector_center_x'];cw=P['connector_opening_width']
boolean(base,cube('DB9 drop-in opening',(cx-cw/2,Y0-1,P['connector_opening_bottom_z']),(cx+cw/2,IY0+1,Z+1)))
for (x,y),direction in zip(P['pcb_mounts'],['+x','-x','+x','-x']):
    boolean(base,post('pcb',x,y,direction),'UNION')
for x,y in P['lid_mounts']:
    boolean(base,post('lid',x,y,'+x' if x<50 else '-x'),'UNION')
clean(base);mat(base,base_mat)

lid=round_rect('LID — print exterior face down',X0,X1,Y0,Y1,R,Z,Z+T)
C=P['lip_clearance_per_side'];LW=P['lip_wall'];LD=P['lip_depth']
lip=round_rect('alignment lip',IX0+C,IX1-C,IY0+C,IY1-C,R-W-C,Z-LD,Z+0.05)
boolean(lip,round_rect('lip hollow',IX0+C+LW,IX1-C-LW,IY0+C+LW,IY1-C-LW,max(0.2,R-W-C-LW),Z-LD-1,Z+1))
for x,y in P['lid_mounts']:
    boolean(lip,cylinder('boss clearance',x,y,Z-LD-1,Z+1,5.4))
boolean(lip,cube('connector lip relief',(cx-cw/2,Y0-1,Z-LD-1),(cx+cw/2,IY0+C+LW+1,Z+1)))
boolean(lid,lip,'UNION')
for x,y in P['lid_mounts']:
    boolean(lid,cylinder('lid screw through hole',x,y,Z-LD-1,Z+T+1,P['lid_bore']/2))

def text_mesh(text,name,loc,size,extrude=0.25):
    curve=bpy.data.curves.new(name,'FONT');curve.body=text;curve.size=size;curve.align_x='CENTER';curve.extrude=extrude;curve.resolution_u=4
    o=bpy.data.objects.new(name,curve);case_c.objects.link(o);o.location=loc
    active(o);bpy.ops.object.convert(target='MESH')
    return bpy.context.object

for txt,y,size in [('LEAF HEAT',-34,8.2),('Wi-Fi climate control',-43,3.1)]:
    boolean(lid,text_mesh(txt,'engraving cutter',(50,y,Z+T-0.45),size,0.55))
# Status viewing hole. All programming and button access is with the lid removed.
boolean(lid,cylinder('status sight hole',65,-47,Z-1,Z+T+1,1.75))
clean(lid);mat(lid,lid_mat)

# Native KiCad GLB is in metres; flatten world transforms and convert to mm.
before=set(bpy.data.objects)
# glTF import honours the scene unit scale. Import into metres explicitly, then
# convert once; importing with scale_length=0.001 would already return mm units.
scene.unit_settings.scale_length=1.0
bpy.ops.import_scene.gltf(filepath=str(H/'reference/leaf-heat-rev-g.glb'))
bpy.context.view_layer.update()
imported=[o for o in bpy.data.objects if o not in before]
flattened=[]
for o in imported:
    if o.type!='MESH': continue
    mesh=o.data.copy();transform=Matrix.Scale(1000,4)@o.matrix_world
    mesh.transform(transform)
    for v in mesh.vertices:v.co.z+=P['pcb_bottom_z']
    n=bpy.data.objects.new('REF '+o.data.name,mesh);ref_c.objects.link(n);flattened.append(n)
for o in imported:bpy.data.objects.remove(o,do_unlink=True)
scene.unit_settings.scale_length=0.001

def bounds(o):
    pts=[o.matrix_world@v.co for v in o.data.vertices]
    if not pts:return [[0,0],[0,0],[0,0]]
    return [[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]

pcb_reference=next(o for o in flattened if o.name.endswith('_PCB'))
pcb_bounds=bounds(pcb_reference)
assert all(abs(pcb_bounds[i][j]-[[0,100],[-100,0],[P['pcb_bottom_z'],P['pcb_bottom_z']+1.49]][i][j])<0.03
           for i in range(3) for j in range(2)),pcb_bounds
radio_reference=next(o for o in flattened if 'ESP32-C3-WROOM-02' in o.name)
radio_bounds=bounds(radio_reference)
assert all(abs(radio_bounds[i][j]-[[64,82],[-14.9,5.1]][i][j])<0.03
           for i in range(2) for j in range(2)),radio_bounds

# KiCad's legacy DB9 model is approximate; replace it with drawing-based envelope
# geometry, including the fitted female screwlocks. It is not a certified STEP.
for o in list(flattened):
    if 'DSUB' in o.name:
        flattened.remove(o);bpy.data.objects.remove(o,do_unlink=True)
def refbox(name,lo,hi,m):
    o=mat(cube('REF '+name,lo,hi,ref_c),m);flattened.append(o);return o
refbox('J1 insulating body — drawing envelope',(cx-15.4,-101.72,20),(cx+15.4,-89.41,32.55),black)
refbox('J1 flange — drawing envelope',(cx-15.4,-102.12,20),(cx+15.4,-101.72,32.55),steel)
# Trapezoidal male shell, represented as a hollow bezel for a useful visual.
shell=refbox('J1 male shell — envelope',(cx-8.46,-108.12,22.25),(cx+8.46,-102.1,30.3),steel)
boolean(shell,cube('connector face opening',(cx-7.65,-108.3,23.0),(cx+7.65,-101.9,29.55)))
for xx in [cx-12.495,cx+12.495]:
    s=cylinder('REF J1 female screwlock — assumed 5 mm projection',0,0,0,5,4.8/(2*cos(pi/6)),vertices=6,c=ref_c)
    s.rotation_euler.x=pi/2;s.location=Vector((xx,-104.62,26.275))
    # Cylinder primitive already has z-centre 2.5: reset local mesh/world placement.
    s.location=(xx,-104.62,26.275);mat(s,steel);flattened.append(s)
refbox('F1 fuse body — conservative proxy',(41.5,-85.1,20),(44.5,-78.9,23.5),white)
# Bound the new radial capacitor from its exact product dimensions, not a generic model.
for o in list(flattened):
    if 'CP_Radial_D6.3mm' in o.name:
        flattened.remove(o);bpy.data.objects.remove(o,do_unlink=True)
c15=mat(cylinder('REF C15 FR47u63V — 6.3mm x 11.2mm',12.25,-32,20,31.2,3.15,c=ref_c),black);flattened.append(c15)
refbox('U5 DYY14 — body envelope',(15.95,-45.15,20),(18.05,-40.85,21.1),black)

for yy,xs in [(-107.9,[cx-5.54,cx-2.77,cx,cx+2.77,cx+5.54]),(-107.9,[cx-4.155,cx-1.385,cx+1.385,cx+4.155])]:
    zz=27.7 if len(xs)==5 else 24.86
    for xx in xs:
        pin=cylinder('REF DB9 contact',0,0,-0.8,0.8,0.32,c=ref_c)
        pin.rotation_euler.x=pi/2;pin.location=(xx,yy,zz);mat(pin,gold);flattened.append(pin)

def reference_screw(x,y,seat,length,diam,m,name):
    shaft=mat(cylinder(name+' shaft',x,y,seat-length,seat,diam/2,32,c=hardware_c),m)
    head=mat(cylinder(name+' head',x,y,seat,seat+diam*0.65,diam*0.92,48,c=hardware_c),m)
    return [shaft,head]
lid_hardware=[]
for x,y in P['lid_mounts']:
    lid_hardware += reference_screw(x,y,Z+T,10,3,steel,'REF M3 x 10 lid screw')
    mat(cylinder('REF M3 nut',x,y,Z-5.1,Z-2.7,5.5/(2*cos(pi/6)),6,c=hardware_c),steel)
for x,y in P['pcb_mounts']:
    reference_screw(x,y,P['pcb_bottom_z']+P['pcb_thickness'],8,2.5,nylon,'REF nylon M2.5 x 8 PCB screw')
    mat(cylinder('REF nylon M2.5 nut',x,y,P['pcb_bottom_z']-4.5,P['pcb_bottom_z']-2.5,5.0/(2*cos(pi/6)),6,c=hardware_c),nylon)

# Fastener test: actual PCB and lid post designs on a small shared base.
coupon=round_rect('TEST — screw and captive-nut fit',0,36,0,18,3,0,F,test_c)
for kind,x in [('pcb',9),('lid',27)]:
    q=post(kind,x,9,'-x' if kind=='pcb' else '+x')
    boolean(coupon,q,'UNION')
clean(coupon);mat(coupon,lid_mat)
test_c.hide_render=True;test_c.hide_viewport=True

# A flat U-shaped connector gauge, representing the assembled opening width/height.
gap_h=Z-P['connector_opening_bottom_z']
gauge=cube('TEST — DB9 opening gauge',(0,0,0),(cw+8,gap_h+4,2.4),test_c)
boolean(gauge,cube('gauge opening',(4,4,-1),(cw+4,gap_h+5,3.4)))
clean(gauge);mat(gauge,lid_mat)

def mesh_report(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    invalid=sum(not e.is_manifold for e in bm.edges)
    volume=bm.calc_volume(signed=True)
    # Count connected vertex components, including accidental isolated pieces.
    unseen=set(bm.verts);components=0
    while unseen:
        components+=1;stack=[unseen.pop()]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen: unseen.remove(w);stack.append(w)
    b=bounds(o);result={'bounds_mm':b,'dimensions_mm':[v[1]-v[0] for v in b],
        'nonmanifold_edges':invalid,'connected_solids':components,'volume_mm3':volume,
        'faces':len(bm.faces),'vertices':len(bm.verts)}
    bm.free();return result

def bvh(o):
    mesh=o.data
    return BVHTree.FromPolygons([o.matrix_world@v.co for v in mesh.vertices],
                               [list(f.vertices) for f in mesh.polygons],all_triangles=False,epsilon=0.00001)

def overlap_volume(a,b):
    temp=a.copy();temp.data=a.data.copy();case_c.objects.link(temp)
    operand=b.copy();operand.data=b.data.copy();case_c.objects.link(operand)
    boolean(temp,operand,'INTERSECT');clean(temp)
    report=mesh_report(temp);bpy.data.objects.remove(temp,do_unlink=True)
    return abs(report['volume_mm3'])

bpy.context.view_layer.update()
reports={o.name:mesh_report(o) for o in [base,lid,coupon,gauge]}
for name,r in reports.items():
    assert r['nonmanifold_edges']==0,(name,r)
    assert r['connected_solids']==1,(name,r)
    assert r['volume_mm3']>0,(name,r)
case_intersection=overlap_volume(base,lid)
assert case_intersection<0.001,case_intersection
collisions=[]
for c in [base,lid]:
    cb=bvh(c)
    for o in flattened:
        # PCB underside intentionally touches the four insulating support lands.
        if any(s in o.name for s in ['_PCB','silkscreen','_pad']):continue
        if cb.overlap(bvh(o)):
            collisions.append({'case':c.name,'reference':o.name})
assert not collisions,collisions

def export_stl(o,name,lid_flip=False):
    test_c.hide_viewport=False
    out=o.copy();out.data=o.data.copy();case_c.objects.link(out)
    out.data.transform(out.matrix_world)
    out.matrix_world=Matrix.Identity(4)
    if lid_flip:
        out.data.transform(Matrix.Rotation(pi,4,'X'))
    b=[[min(v.co[i] for v in out.data.vertices),max(v.co[i] for v in out.data.vertices)] for i in range(3)]
    shift=Vector([v[0] for v in b])
    for v in out.data.vertices:v.co-=shift
    out.data.update();bpy.context.view_layer.update()
    active(out)
    path=H/'print'/name
    bpy.ops.wm.stl_export(filepath=str(path),export_selected_objects=True,
                          use_scene_unit=False,global_scale=1.0,apply_modifiers=True)
    # Check the actual binary STL triangle bounds, including mm scale.
    blob=path.read_bytes();n=struct.unpack_from('<I',blob,80)[0]
    assert len(blob)==84+50*n
    coords=[]
    for i in range(n):coords.extend(struct.unpack_from('<9f',blob,84+50*i+12))
    bb=[[min(coords[j::3]),max(coords[j::3])] for j in range(3)]
    assert all(abs((bb[i][1]-bb[i][0])-(b[i][1]-b[i][0]))<0.01 for i in range(3))
    assert abs(bb[2][0])<0.01
    result={'file':str(path.relative_to(H)),'sha256':hashlib.sha256(blob).hexdigest(),
            'triangles':n,'bounds_mm':bb,'print_orientation':'exterior face down' if lid_flip else 'flat base down'}
    bpy.data.objects.remove(out,do_unlink=True);test_c.hide_viewport=True
    return result

exports=[export_stl(base,'leaf-rev-g-case-base.stl'),export_stl(lid,'leaf-rev-g-case-lid.stl',True),
         export_stl(coupon,'OPTIONAL-fastener-fit-test.stl'),export_stl(gauge,'OPTIONAL-connector-fit-test.stl')]
validation={'pcb_sha256':G['pcb_sha256'],'revision':P['revision'],'units':'mm',
    'imported_pcb_bounds_mm':pcb_bounds,'imported_radio_bounds_mm':radio_bounds,
    'external_dimensions_mm':[X1-X0,Y1-Y0,Z+T], 'mounts_from_native_pcb':actual_mounts,
    'mesh_reports':reports,'base_lid_intersection_mm3':case_intersection,
    'reference_surface_collisions':collisions,'stl_exports':exports,
    'antenna_to_main_shell_mm':{'rear_wall':IY1-5.1,'right_wall':IX1-82,'floor':19.9-F,'lid':Z-21},
    'limitations':['Printed fit, nut/screw sizes and cable hood must be checked physically.',
      'H2 PCB support lies within the suggested 15 mm antenna clearance; use unfilled nylon PCB fasteners and verify Wi-Fi range.',
      'DB9 envelope is derived from a manufacturer drawing; female screwlock projection and actual cable hood remain assumptions.',
      'PCB GLB dielectric body is 1.49 mm; native total PCB thickness 1.6 mm governs assembly.',
      'No weatherproofing, automotive thermal qualification, vibration qualification or physical print test is claimed.']}
(H/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')

# Studio and presentation views.
floor=mat(cube('STUDIO ground',(-350,-350,-1.5),(350,300,-0.1),studio_c),white)
def area(name,loc,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);studio_c.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((50,-40,15))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large softbox',(-100,-160,260),1400000,200)
area('Fill softbox',(200,-10,170),1000000,180)
area('Rear rim',(20,170,200),1100000,160)
camdata=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camdata);studio_c.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.clip_start=0.1;camdata.clip_end=2000
def camera(loc,target,scale):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.ortho_scale=scale
def render(name):
    scene.render.filepath=str(H/'previews'/name);bpy.ops.render.render(write_still=True)

camera((225,-245,215),(50,-40,17),205)
render('01-closed-case.png')
lid.hide_render=True
for o in lid_hardware:o.hide_render=True
render('02-open-case-with-board.png')
lid.hide_render=False
for o in lid_hardware:o.hide_render=False
lid.location.z=62
for o in lid_hardware:o.location.z+=62
camera((235,-270,245),(50,-40,45),240)
render('03-exploded-case.png')
lid.location.z=0
for o in lid_hardware:o.location.z-=62
ref_c.hide_render=True;hardware_c.hide_render=True;lid.hide_render=True
camera((185,-205,230),(50,-40,10),190)
render('04-empty-base.png')
ref_c.hide_render=False;hardware_c.hide_render=False;lid.hide_render=False

# Save an exploded, editable view; one parent moves the lid and its screws together.
lid_assembly=bpy.data.objects.new('LID ASSEMBLY — Z=0 closed, Z=62 exploded',None)
case_c.objects.link(lid_assembly)
lid_assembly.empty_display_type='PLAIN_AXES';lid_assembly.empty_display_size=8
for o in [lid,*lid_hardware]:
    world=o.matrix_world.copy();o.parent=lid_assembly;o.matrix_world=world
lid_assembly.location.z=62
camera((235,-270,245),(50,-40,45),240)
studio_c.hide_viewport=True
for area_ui in bpy.context.screen.areas:
    if area_ui.type=='VIEW_3D':
        space=area_ui.spaces.active;space.clip_end=3000;space.clip_start=0.1
        space.region_3d.view_distance=230
        space.region_3d.view_location=(50,-40,40)
        space.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
        space.shading.type='MATERIAL'
active(base)
scene['Assembly instructions']='Millimetres. Select LID ASSEMBLY and set Location Z to 0 mm for closed assembly, or 62 mm for exploded view. Only the supplied STL files are printable; PCB and fasteners are references.'
bpy.ops.wm.save_as_mainfile(filepath=str(H/'leaf-rev-g-enclosure.blend'))
print('SUCCESS: enclosure created; manifold solids, exact mounting-hole positions and mm-scale STL exports checked.')

"""Original reference-gallery props. build(ctx) is called after the room layout.

Offline: python Tools/reference_props.py --generate
No external models/images, no Editor launch, no Source/Config changes.
All source assets live below Assets/Reference; imports below /Game/ReferenceGallery.
"""
from pathlib import Path
import json
import math

from reference_rotation import rot

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Assets' / 'Reference'
DEST = '/Game/ReferenceGallery'


def _normalize(v):
    length = math.sqrt(sum(x*x for x in v))
    return tuple(x / max(length, 1e-12) for x in v)


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def _sweep(vertices, faces, curve, radius, depth, samples=160, sides=16):
    """Closed elliptical ribbon-section tube with smoothly varying breadth."""
    offset = len(vertices)
    for i in range(samples):
        t = 2 * math.pi * i / samples
        center = curve(t)
        before, after = curve(t-0.0001), curve(t+0.0001)
        tangent = _normalize(tuple(b-a for a, b in zip(before, after)))
        radial = _normalize(_cross((0, 1, 0), tangent))
        binormal = _normalize(_cross(tangent, radial))
        breadth = radius * (1 + 0.24*math.sin(t+0.7))
        for j in range(sides):
            angle = 2*math.pi*j/sides
            vertices.append(tuple(center[k] + breadth*math.cos(angle)*radial[k] + depth*math.sin(angle)*binormal[k] for k in range(3)))
    for i in range(samples):
        for j in range(sides):
            a = offset + i*sides+j
            b = offset + ((i+1)%samples)*sides+j
            c = offset + ((i+1)%samples)*sides+(j+1)%sides
            d = offset + i*sides+(j+1)%sides
            faces.extend([(a, c, b), (a, d, c)])


def _write_obj(path, vertices, faces, uvs=None):
    """Explicit smooth normals; Z-up centimetres; one material section."""
    normals = [[0.0, 0.0, 0.0] for _ in vertices]
    for face in faces:
        a,b,c = (vertices[i] for i in face)
        n = _cross(tuple(b[k]-a[k] for k in range(3)), tuple(c[k]-a[k] for k in range(3)))
        for i in face:
            for k in range(3):
                normals[i][k] += n[k]
    lines = ['# Original procedural mesh; Z-up; centimetres', 'o '+path.stem, 's 1']
    lines += ['v %.6f %.6f %.6f' % v for v in vertices]
    if uvs:
        lines += ['vt %.6f %.6f' % uv for uv in uvs]
    lines += ['vn %.6f %.6f %.6f' % _normalize(n) for n in normals]
    for face in faces:
        lines.append('f ' + ' '.join(f'{i+1}/{i+1 if uvs else ""}/{i+1}' for i in face))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return dict(vertices=len(vertices), triangles=len(faces), bounds_min=[min(p[k] for p in vertices) for k in range(3)], bounds_max=[max(p[k] for p in vertices) for k in range(3)])


def generate_meshes():
    meshes = SOURCE / 'Meshes'
    v, f = [], []
    # Three unequal interwoven rising ribbons, not a stock torus/cylinder.
    _sweep(v, f, lambda t: (39*math.cos(t)+7*math.sin(2*t), -13+8*math.sin(2*t), 91+75*math.sin(t)), 11, 6, 160, 16)
    _sweep(v, f, lambda t: (-22+27*math.cos(t)+17*math.sin(t), 13+11*math.sin(t), 106+88*math.sin(t)), 9, 5, 160, 16)
    _sweep(v, f, lambda t: (12+27*math.cos(t)-12*math.sin(t), -20+9*math.sin(2*t), 115+43*math.sin(t)), 13, 5, 128, 16)
    lo, hi = min(p[2] for p in v), max(p[2] for p in v)
    v = [(x,y,(z-lo)*195/(hi-lo)) for x,y,z in v]
    result = {'SM_BronzeLoop': _write_obj(meshes/'SM_BronzeLoop.obj',v,f)}
    v,f = [],[]
    _sweep(v, f, lambda t: (35*math.cos(t)+10*math.sin(2*t), 5*math.sin(2*t), 65+58*math.sin(t)), 8, 11, 96, 12)
    lo = min(p[2] for p in v)
    v = [(x,y,z-lo) for x,y,z in v]
    result['SM_RearLoop'] = _write_obj(meshes/'SM_RearLoop.obj',v,f)
    # Local X horizontal, Z up, artwork front faces local -Y.
    result['SM_ArtPlane'] = _write_obj(meshes/'SM_ArtPlane.obj',[(-50,0,-50),(50,0,-50),(50,0,50),(-50,0,50)],[(0,1,2),(0,2,3)],[(0,0),(1,0),(1,1),(0,1)])
    return result


def _append_box(vertices, faces, center, size):
    # Separate per-face vertices preserve the timber's crisp square edges.
    x,y,z = center
    a,b,c = (n/2 for n in size)
    corners = [(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
               (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
    for quad in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
        offset = len(vertices)
        vertices.extend(corners[i] for i in quad)
        faces.extend([(offset,offset+1,offset+2),(offset,offset+2,offset+3)])


def _torus_y(vertices, faces, center, major, minor, sides=32, section=8):
    offset = len(vertices)
    for i in range(sides):
        t = 2*math.pi*i/sides
        for j in range(section):
            a = 2*math.pi*j/section
            r = major + minor*math.cos(a)
            vertices.append((center[0]+r*math.cos(t),center[1]+minor*math.sin(a),center[2]+r*math.sin(t)))
    for i in range(sides):
        for j in range(section):
            a=offset+i*section+j
            b=offset+((i+1)%sides)*section+j
            c=offset+((i+1)%sides)*section+(j+1)%section
            d=offset+i*section+(j+1)%section
            faces.extend([(a,c,b),(a,d,c)])


# Subject, wall face, position, size, texture, label, yaw. Single source of truth:
# the lighting module imports this so the art spots always land on the pieces.
# The reference's pieces are landscape black gestural contour works, portrait
# translucent-disc works, and ochre facet works inside the niche.
ART_HANGINGS = (
    ('West_Contour',   (-688, -270, 174), 128,  84, 'T_ContourField', 'T_Label_04',  90),
    ('West_Orbit',     (-688,   90, 183), 104, 132, 'T_OrbitForms',   'T_Label_02',  90),
    ('West_ContourII', (-688,  600, 177), 120,  80, 'T_ContourField', 'T_Label_01',  90),
    ('East_Contour',   ( 688, -300, 173), 140,  92, 'T_ContourField', 'T_Label_04', -90),
    ('East_Orbit',     ( 688,  390, 181), 112, 140, 'T_OrbitForms',   'T_Label_03', -90),
    ('East_Ochre',     ( 688,  620, 179), 106, 124, 'T_OchreFacets',  'T_Label_07', -90),
    ('Rear_Divider_Orbit', (-330, 418, 155), 104, 138, 'T_OrbitForms', 'T_Label_05', 0),
)

CEILING_SLATS = [((x,0,408),(3.0,1796,4.0)) for x in range(-690,691,18)]
BENCH_SLATS = [((x,0,0),(4.0,145,5.0)) for x in range(-20,21,5)]

# Open-web trusses, taken from the reference scene's own primitives rather than
# invented: each truss is two 4x4 chords 22 apart with 26 vertical webs of
# 2.5x26x2.5 on a 49 cm pitch, and there are three of them. The reference has a
# slat deck AND exposed trusses below it; a slat deck alone reads as a flat
# ceiling and loses the industrial structure that carries the whole look.
TRUSS_WEB_COUNT = 26
TRUSS_WEB_PITCH = 49.0
TRUSS_TOP_Z = 405.0
TRUSS_BOTTOM_Z = 383.0
TRUSS_CHORD = 4.0
TRUSS_WEB = 2.5
TRUSS_WEB_HEIGHT = 26.0
TRUSS_LENGTH = 1400.0
# Reference trusses sit at 12%, 41% and 68% of the room's depth; mapped onto this
# room's 1800 cm depth so the spacing rhythm matches.
TRUSS_Y = (-680.0, -169.0, 317.0)


def generate_detail_meshes():
    result = {}
    for name, items in [('SM_CeilingSlats',CEILING_SLATS),('SM_BenchSlats',BENCH_SLATS)]:
        vertices, faces = [], []
        for center,size in items:
            _append_box(vertices,faces,center,size)
        uvs=[[(0,0),(1,0),(1,1),(0,1)][i%4] for i in range(len(vertices))]
        result[name] = _write_obj(SOURCE/'Meshes'/f'{name}.obj',vertices,faces,uvs)
    vertices, faces = [], []
    for x in [-390,430]:
        for y in range(-800,801,100):
            _torus_y(vertices,faces,(x,y,393.5),15.4,0.8,32,8)
    result['SM_DuctBands'] = _write_obj(SOURCE/'Meshes'/'SM_DuctBands.obj',vertices,faces)
    return result


def generate_textures():
    """Pillow-only offline raster authoring; no downloaded source artwork."""
    import random
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    directory = SOURCE/'Textures'
    directory.mkdir(parents=True,exist_ok=True)
    files = []
    rng = random.Random(731)
    # 1. Contour field: loose black gestural contour lines on warm beige. Reads as
    #    an aerial map sketch, matching the reference's map-like wall piece.
    #    Landscape format with a thin black frame. Lines are heavier and denser
    #    than a light sketch so the piece still reads from across a gallery.
    image=Image.new('RGB',(1536,1024),'#e8dfcb'); draw=ImageDraw.Draw(image)
    for row in range(34):
        points=[]
        for x in range(-40,1580,7):
            y=95+row*27+40*math.sin(x/131+row*0.61)+19*math.sin(x/47+row*1.3)+8*math.sin(x/17+row)
            points.append((x,int(y)))
        draw.line(points,fill=['#14120f','#221f1a','#302b24'][row%3],width=[3,4,5,4][row%4])
    for j in range(34):
        x=rng.randrange(1536); y=rng.randrange(70,970)
        draw.arc((x-72,y-58,x+92,y+72),rng.randrange(0,180),rng.randrange(200,360),fill='#26231f',width=2)
    for j in range(70):
        x=rng.randrange(1536); y=rng.randrange(1024)
        draw.line((x,y,x+rng.randrange(8,44),y+rng.randrange(-4,4)),fill='#4a443a',width=1)
    path=directory/'T_ContourField.png'; image.save(path); files.append(path.relative_to(SOURCE).as_posix())
    # 2. Orbit forms: overlapping TRANSLUCENT discs in magenta, red-orange,
    #    orange, violet and teal on a pale ground. The translucency is the point --
    #    opaque shapes lose the layered overlaps the reference depends on.
    #    NOTE: draw with real alpha (32) and let the compositor blend. A high
    #    alpha here silently produces opaque discs with only 7 distinct colours,
    #    which reads as "flat shapes" not "layered colour".
    #    MEASURED: at alpha 96 the result was a 181..233 grey field -- only 52
    #    levels of spread, so on a wall at this exposure it read as a blank panel.
    #    The reference's discs are bold and saturated, so alpha is raised and the
    #    palette deepened.
    base=Image.new('RGBA',(1200,1500),'#e8e0d0')
    orbit=[(0xc4,0x18,0x78),(0xd8,0x42,0x14),(0xe8,0x84,0x10),
           (0x52,0x1c,0x94),(0x18,0xb8,0x84),(0xb0,0x24,0x34)]
    for i in range(11):
        layer=Image.new('RGBA',(1200,1500),(0,0,0,0))
        od=ImageDraw.Draw(layer)
        x=rng.randrange(200,1000); y=rng.randrange(250,1250); r=rng.randrange(175,350)
        rgb=orbit[i%len(orbit)]
        od.ellipse((x-r,y-r,x+r,y+r),fill=rgb+(190,))
        base=Image.alpha_composite(base,layer)
    image=base.convert('RGB')
    path=directory/'T_OrbitForms.png'; image.save(path); files.append(path.relative_to(SOURCE).as_posix())
    # 3. Ochre facets: angular ochre/caramel planes on dark umber with a warm
    #    glow, as hung inside the reference's arched niche.
    image=Image.new('RGB',(1200,1400),'#241a12'); draw=ImageDraw.Draw(image)
    for j in range(16):
        pts=[(rng.randrange(-140,1340),rng.randrange(-140,1540)) for _ in range(rng.choice([3,4]))]
        draw.polygon(pts,fill=rng.choice(['#c8912f','#a9711f','#7a4a16','#4a2c0e','#e0b558','#8d5a1c']))
    draw.ellipse((400,880,800,1280),fill='#ffd977')
    draw.ellipse((510,990,690,1170),fill='#fff3c4')
    path=directory/'T_OchreFacets.png'; image.save(path); files.append(path.relative_to(SOURCE).as_posix())
    titles=['CONTOUR FIELD','ORBIT FORMS','OCHRE FACETS','CONTOUR FIELD II','ORBIT FORMS II','CONTINUITY','OCHRE FACETS II']
    font_path=Path('C:/Windows/Fonts/arial.ttf')
    # Fonts are rasterized locally, never copied/distributed as font files.
    font=ImageFont.truetype(str(font_path),34) if font_path.exists() else ImageFont.load_default(size=34)
    small=ImageFont.truetype(str(font_path),23) if font_path.exists() else ImageFont.load_default(size=23)
    for i,title in enumerate(titles):
        image=Image.new('RGB',(1024,320),'#1a1b1b'); draw=ImageDraw.Draw(image)
        draw.rectangle((40,40,48,275),fill='#bf9656')
        draw.text((78,48),f'{i+1:02d}  /  {title}',font=font,fill='#e9e5da')
        medium='Bronze / original digital form' if i>=5 else 'Original digital composition'
        draw.text((80,119),medium,font=small,fill='#c4c1b6')
        draw.text((80,200),'REFERENCE GALLERY  /  COLLECTION 01',font=small,fill='#9e9e94')
        path=directory/f'T_Label_{i+1:02d}.png'; image.save(path); files.append(path.relative_to(SOURCE).as_posix())
    # Fine wood grain to avoid uniform plastic-looking timber.
    image=Image.new('RGB',(512,1024),'#794a29'); draw=ImageDraw.Draw(image)
    for x in range(512):
        tone=rng.randint(-17,17)
        color=(max(0,121+tone),max(0,74+tone),max(0,41+tone))
        points=[(x+2*math.sin(y/80+x/9),y) for y in range(0,1030,8)]
        draw.line(points,fill=color,width=1)
    image=image.filter(ImageFilter.GaussianBlur(.35))
    path=directory/'T_WalnutGrain.png'; image.save(path); files.append(path.relative_to(SOURCE).as_posix())
    return files


def generate_assets():
    meshes=generate_meshes()
    meshes.update(generate_detail_meshes())
    textures=generate_textures()
    manifest={'units':'centimetres','up_axis':'Z','source':'Original procedural geometry and Pillow artwork authored for this project',
              'meshes':meshes,'textures':textures,'ceiling_slat_instances':len(CEILING_SLATS),'bench_slat_instances':len(BENCH_SLATS)}
    (SOURCE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


def _import_asset(u, filename, category):
    name=Path(filename).stem
    target=f'{DEST}/{category}/{name}'
    source=SOURCE/filename
    asset=u.load_asset(target)
    if asset:
        # Re-import when the SOURCE is newer than the imported asset. Returning
        # early on existence means regenerated artwork never reaches the engine,
        # and the wall keeps showing the previous (washed-out) texture.
        if not source.exists():
            return asset
        try:
            imported=Path(u.EditorAssetLibrary.find_asset_data(target).get_asset().get_path_name())
        except Exception:
            imported=None
        on_disk=Path(u.Paths.convert_relative_path_to_full(
            u.Paths.project_content_dir()+target[len('/Game/'):]+'.uasset'))
        if on_disk.exists() and source.stat().st_mtime <= on_disk.stat().st_mtime:
            return asset
        u.log(f'REIMPORT {name}: source is newer than the imported asset')
        u.EditorAssetLibrary.delete_asset(target)
    if not source.exists():
        raise FileNotFoundError(f'{source}: run Tools/reference_props.py --generate with system Python first')
    task=u.AssetImportTask()
    task.set_editor_property('filename',str(source))
    task.set_editor_property('destination_path',f'{DEST}/{category}')
    task.set_editor_property('destination_name',name)
    task.set_editor_property('automated',True)
    task.set_editor_property('replace_existing',False)
    task.set_editor_property('save',True)
    if source.suffix.lower()=='.obj':
        options=u.FbxImportUI()
        options.set_editor_property('import_mesh',True)
        options.set_editor_property('import_as_skeletal',False)
        options.set_editor_property('import_materials',False)
        options.set_editor_property('import_textures',False)
        options.set_editor_property('mesh_type_to_import',u.FBXImportType.FBXIT_STATIC_MESH)
        options.set_editor_property('automated_import_should_detect_type',False)
        data=options.get_editor_property('static_mesh_import_data')
        data.set_editor_property('combine_meshes',True)
        data.set_editor_property('auto_generate_collision',False)
        data.set_editor_property('generate_lightmap_u_vs',False)
        data.set_editor_property('convert_scene',False)
        data.set_editor_property('convert_scene_unit',False)
        data.set_editor_property('import_translation',u.Vector(0,0,0))
        data.set_editor_property('import_rotation',u.Rotator(0,0,0))
        data.set_editor_property('import_uniform_scale',1.0)
        data.set_editor_property('build_nanite',False)
        data.set_editor_property('force_front_x_axis',False)
        data.set_editor_property('normal_import_method',u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
        task.set_editor_property('options',options)
        # OBJ is routed through the explicit legacy factory, not Interchange defaults.
        task.set_editor_property('factory',u.FbxFactory())
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset=u.load_asset(target)
    if not asset:
        raise RuntimeError(f'Asset import failed: {source}; returned {task.get_editor_property("imported_object_paths")}')
    if category=='Textures':
        asset.set_editor_property('srgb',True)
        asset.set_editor_property('never_stream',True)
        u.EditorAssetLibrary.save_loaded_asset(asset)
    if name=='SM_BronzeLoop':
        # Fail visibly if an import backend silently changes OBJ units/up-axis.
        size=asset.get_bounding_box().max-asset.get_bounding_box().min
        if abs(size.z-195)>1 or abs(size.x-116.386)>1:
            raise RuntimeError(f'Bronze OBJ axis/scale mismatch: {size}; expected 116.386 x 63 x 195 cm')
    return asset


def _texture_material(u,name,texture,roughness=.72):
    path=f'{DEST}/Materials/M_{name}'
    mat=u.load_asset(path)
    if mat:
        # Re-check cached assets: without this flag every HISM batch using the
        # timber material silently renders with the engine's grey default, and
        # without the roughness rewrite a later tuning change is a no-op.
        if not mat.get_editor_property('used_with_instanced_static_meshes'):
            mat.set_editor_property('used_with_instanced_static_meshes',True)
            u.log('REFERENCE_MATERIAL_FLAG fixed M_'+name)
        node=u.MaterialEditingLibrary.get_material_property_input_node(mat,u.MaterialProperty.MP_ROUGHNESS)
        if node is not None:
            node.set_editor_property('r',roughness)
        # Point the sampler at the CURRENT texture object. Re-importing a texture
        # replaces the asset, so a material built against the old one keeps
        # sampling the stale image even though both assets look correct.
        mel=u.MaterialEditingLibrary
        for e in mel.get_material_expressions(mat):
            if e.__class__.__name__.startswith('MaterialExpressionTextureSample'):
                if e.get_editor_property('texture') is not texture:
                    e.set_editor_property('texture',texture)
                    e.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR)
                    u.log('REFERENCE_MATERIAL_RETARGET M_'+name)
        mel.recompile_material(mat)
        u.EditorAssetLibrary.save_loaded_asset(mat)
        return mat
    mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
    mel=u.MaterialEditingLibrary
    sample=mel.create_material_expression(mat,u.MaterialExpressionTextureSample)
    sample.set_editor_property('texture',texture)
    sample.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    assert mel.connect_material_property(sample,'RGB',u.MaterialProperty.MP_BASE_COLOR)
    r=mel.create_material_expression(mat,u.MaterialExpressionConstant)
    r.set_editor_property('r',roughness)
    assert mel.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
    # Artwork planes are two-sided for robustness, although front winding is -Y.
    mat.set_editor_property('two_sided',True)
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    mel.recompile_material(mat)
    u.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def _spawn_mesh(u,ctx,name,mesh,loc,material,rotation=(0,0,0),scale=(1,1,1),folder='Reference/Props'):
    actor=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.StaticMeshActor,u.Vector(*loc),rot(*rotation))
    actor.set_actor_label(name)
    actor.set_folder_path(folder)
    comp=actor.static_mesh_component
    comp.set_mobility(u.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh)
    comp.set_material(0,ctx['mat'][material] if isinstance(material,str) else material)
    actor.set_actor_scale3d(u.Vector(*scale))
    comp.set_collision_profile_name('NoCollision')
    comp.set_mobility(u.ComponentMobility.STATIC)
    ctx['actors'].append(actor)
    return actor


def _slat_batch(u,ctx,name,items,material,fallback,origin=(0,0,0)):
    """Serialized editor HISM component, with one merged-mesh fallback."""
    actor=None
    try:
        subsystem=u.get_engine_subsystem(u.SubobjectDataSubsystem)
        if subsystem is None:
            raise RuntimeError('SubobjectDataSubsystem unavailable')
        actor=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.Actor,u.Vector(*origin))
        actor.set_actor_label(name)
        actor.set_folder_path('Reference/Props/Timber')
        handles=subsystem.k2_gather_subobject_data_for_instance(actor)
        params=u.AddNewSubobjectParams(parent_handle=handles[0],new_class=u.HierarchicalInstancedStaticMeshComponent)
        handle,reason=subsystem.add_new_subobject(params)
        data=u.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        comp=u.SubobjectDataBlueprintFunctionLibrary.get_associated_object(data)
        if not isinstance(comp,u.HierarchicalInstancedStaticMeshComponent):
            raise RuntimeError(str(reason))
        comp.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'))
        comp.set_material(0,material)
        comp.set_collision_profile_name('NoCollision')
        for loc,size in items:
            # World-space placement avoids dependence on component root creation rules.
            transform=u.Transform(location=u.Vector(*(loc[k]+origin[k] for k in range(3))),rotation=u.Rotator(),scale=u.Vector(*(n/100 for n in size)))
            comp.add_instance(transform,world_space=True)
        comp.set_mobility(u.ComponentMobility.MOVABLE)
        if comp.get_instance_count()!=len(items):
            raise RuntimeError('Incomplete HISM batch')
        ctx['actors'].append(actor)
        u.log(f'{name}: HISM instances={comp.get_instance_count()}')
        return actor
    except Exception as error:
        if actor:
            u.get_editor_subsystem(u.EditorActorSubsystem).destroy_actor(actor)
        u.log_warning(f'{name}: HISM unavailable ({error}); using one merged static mesh, not individual slat actors')
        return _spawn_mesh(u,ctx,name+'_Merged',fallback,origin,material,folder='Reference/Props/Timber')


def _framed_art(u,ctx,plane,name,loc,width,height,material,label,yaw=0):
    """Loc is the wall's inward face; local front is -Y, rotated about Z."""
    box=ctx['box']
    angle=math.radians(yaw)
    def point(x,y,z):
        return (loc[0]+x*math.cos(angle)-y*math.sin(angle),loc[1]+x*math.sin(angle)+y*math.cos(angle),loc[2]+z)
    folder='Reference/Props/Art'
    box(name+'_Backing',point(0,-1.5,0),(width+7,3,height+7),'black',rotation=(0,yaw,0),collision=False,folder=folder)
    box(name+'_Mat',point(0,-3.3,0),(width+3,.8,height+3),'wall',rotation=(0,yaw,0),collision=False,folder=folder)
    _spawn_mesh(u,ctx,name+'_Canvas',plane,point(0,-3.9,0),material,(0,yaw,0),(width/100,1,height/100),folder)
    for sign in [-1,1]:
        box(name+f'_FrameSide{sign}',point(sign*(width/2+2.7),-4,0),(2.2,4,height+7),'wood',rotation=(0,yaw,0),collision=False,folder=folder)
        box(name+f'_FrameRail{sign}',point(0,-4,sign*(height/2+2.7)),(width+7,4,2.2),'wood',rotation=(0,yaw,0),collision=False,folder=folder)
    # Flush-readable placard alongside painting, not floating on the canvas.
    _spawn_mesh(u,ctx,name+'_Label',plane,point(-width/2-22,-1.2,-height/2+14),label,(0,yaw,0),(.32,1,.10),folder)


def build(ctx):
    import unreal as u
    box,cyl,mats=ctx['box'],ctx['cyl'],ctx['mat']
    mesh_names=['SM_BronzeLoop','SM_RearLoop','SM_ArtPlane','SM_CeilingSlats','SM_BenchSlats','SM_DuctBands','SM_CurvedPartition']
    meshes={name:_import_asset(u,f'Meshes/{name}.obj','Meshes') for name in mesh_names}
    names=['T_ContourField','T_OrbitForms','T_OchreFacets','T_WalnutGrain']+[f'T_Label_{i:02d}' for i in range(1,8)]
    textures={name:_import_asset(u,f'Textures/{name}.png','Textures') for name in names}
    painted={name:_texture_material(u,name[2:],tex,.53 if name=='T_WalnutGrain' else .78) for name,tex in textures.items()}
    before=len(ctx['actors'])
    props='Reference/Props/Sculpture'
    # Plinth top exactly 40; source mesh base 0 and top 195 => hero top 235.
    box('Hero_Plinth',(220,-120,20),(140,100,40),'stone',folder=props)
    box('Hero_Plinth_Reveal',(220,-120,2),(133,93,4),'black',folder=props)
    _spawn_mesh(u,ctx,'Continuity_Bronze_Interwoven_Loops',meshes['SM_BronzeLoop'],(220,-120,40),'bronze',folder=props)
    _spawn_mesh(u,ctx,'Continuity_Plinth_Label',meshes['SM_ArtPlane'],(220,-170.3,23),painted['T_Label_06'],scale=(.56,1,.175),folder=props)
    # A small adjacent white interpretation plinth, clear of the sculpture silhouette.
    box('Interpretation_Plinth',(343,-66,43),(44,44,86),'wall',folder=props)
    _spawn_mesh(u,ctx,'Interpretation_Label',meshes['SM_ArtPlane'],(343,-88.3,68),painted['T_Label_06'],scale=(.34,1,.106),folder=props)
    box('Rear_Plinth',(-150,700,12),(105,90,24),'stone',folder=props)
    _spawn_mesh(u,ctx,'Counterform_Rear_Loop',meshes['SM_RearLoop'],(-150,700,24),'bronze',folder=props)
    sphere=u.load_asset('/Engine/BasicShapes/Sphere')
    _spawn_mesh(u,ctx,'Counterform_Stone_Orb',sphere,(-150,700,179),'stone',scale=(.62,.62,.62),folder=props)
    _spawn_mesh(u,ctx,'Counterform_Label',meshes['SM_ArtPlane'],(-150,654.5,13),painted['T_Label_07'],scale=(.42,1,.131),folder=props)
    box('Small_Study_Plinth',(-340,675,36),(42,42,72),'wall',folder=props)
    _spawn_mesh(u,ctx,'Small_Study_Orb',sphere,(-340,675,88),'bronze',scale=(.32,.32,.32),folder=props)
    # Bench long axis Y; seat footprint 44 x 145cm, top 45cm.
    wood=painted['T_WalnutGrain']
    _slat_batch(u,ctx,'Walnut_Bench_Slats',BENCH_SLATS,wood,meshes['SM_BenchSlats'],(-200,-70,42.5))
    for x in [-218,-182]:
        box('Bench_Underrail', (x,-70,36),(4,137,7),'black',folder='Reference/Props/Bench')
    for y in [-123,-17]:
        box('Bench_Foot',( -200,y,3),(44,6,6),'black',folder='Reference/Props/Bench')
        for x in [-215,-185]:
            box('Bench_Leg',(x,y,20),(4,5,34),'black',folder='Reference/Props/Bench')
    # Thin collision carrier under the visible slats; slats themselves stay cheap.
    box('Bench_Collision_Seat',(-200,-70,39),(43,144,4),'black',folder='Reference/Props/Bench')
    # Seat pad over the slats, as in the reference. Collision-free: the carrier
    # above already provides the seat collision, so the pad is purely visual.
    box('Bench_Cushion',(-200,-70,48.5),(40,138,7),'fabric',collision=False,folder='Reference/Props/Bench')
    _slat_batch(u,ctx,'Ceiling_Walnut_Fins',CEILING_SLATS,mats['wood'],meshes['SM_CeilingSlats'])
    # Exposed open-web trusses below the slat deck, matching the reference's
    # structure. Chords run the room's X span; webs are verticals between them.
    truss_items=[]
    for ty in TRUSS_Y:
        for cz in (TRUSS_TOP_Z, TRUSS_BOTTOM_Z):
            truss_items.append(((0.0,ty,cz),(TRUSS_LENGTH,TRUSS_CHORD,TRUSS_CHORD)))
        start=-TRUSS_WEB_PITCH*(TRUSS_WEB_COUNT-1)/2.0
        for w in range(TRUSS_WEB_COUNT):
            truss_items.append(((start+w*TRUSS_WEB_PITCH,ty,(TRUSS_TOP_Z+TRUSS_BOTTOM_Z)/2.0),
                                (TRUSS_WEB,TRUSS_WEB_HEIGHT,TRUSS_WEB)))
    _slat_batch(u,ctx,'Ceiling_Trusses',truss_items,mats['metal'],None)
    overhead='Reference/Props/Services'
    # Services fit between z375 and z410. A cylinder's native axis is local Z.
    for x in [-390,430]:
        cyl('Spiral_Duct_Main',(x,0,393.5),(30,30,1730),'metal',rotation=(0,0,90),collision=False,folder=overhead)
        for y in [-700,-300,100,500,800]:
            box('Duct_Hanger_Crossbar',(x,y,376.5),(44,3,3),'metal',collision=False,folder=overhead)
            for dx in [-20,20]:
                cyl('Duct_Hanger_Rod',(x+dx,y,391),(1,1,32),'metal',collision=False,folder=overhead)
    _spawn_mesh(u,ctx,'Duct_Clamp_Bands',meshes['SM_DuctBands'],(0,0,0),'metal',folder=overhead)
    cyl('Cross_Duct', (0,-470,387),(22,22,1260),'metal',rotation=(90,0,0),collision=False,folder=overhead)
    for x in range(-560,561,140):
        cyl('Cross_Duct_Coupling',(x,-470,387),(23.5,23.5,3),'metal',rotation=(90,0,0),collision=False,folder=overhead)
    # Fixtures only; the lighting module owns actual emitters/light actors.
    for x in [-535,70,570]:
        box('Lighting_Track',(x,0,374),(4,1690,4),'black',collision=False,folder=overhead)
        for y in range(-720,721,240):
            box('Track_Adapter',(x,y,371),(8,10,4),'metal',collision=False,folder=overhead)
            cyl('Track_Stem',(x,y,362),(3,3,16),'metal',collision=False,folder=overhead)
            tilt=24 if x<0 else -24
            cyl('Track_Spot_Housing',(x,y,349),(11,11,19),'wall',rotation=(tilt,0,0),collision=False,folder=overhead)
            # Pitch tilts local Z toward -X, so the EMITTING end of the housing is
            # the -Z end: offset along -Z, not along +X as the sign used to imply.
            lens=(x+9.5*math.sin(math.radians(tilt)),y,349-9.5*math.cos(math.radians(tilt)))
            cyl('Track_Spot_Lens',lens,(9,9,.7),'emissive',rotation=(tilt,0,0),collision=False,folder=overhead)
    art=meshes['SM_ArtPlane']
    # Side wall faces are x +/-688. No art in the southwest entry strip.
    # Positions come from ART_HANGINGS, which the lighting module imports so the
    # art spots land on the pieces rather than between them.
    hangings=ART_HANGINGS
    for name,loc,w,h,paint,label,yaw in hangings:
        _framed_art(u,ctx,art,name,loc,w,h,painted[paint],painted[label],yaw)
    # Curved freestanding partition, swept from the reference scene's own
    # NonParametricGeometry centreline (see Assets/SplineReference/
    # curved_partition_fit.json). An earlier attempt built this from rotated
    # boxes, whose chorded segments read as separate leaning slabs; this is a
    # single swept solid with a 90-degree fillet, so the surface is continuous.
    # Placed clear of the focal pedestal at (220,-120) and the ART_HANGINGS.
    _spawn_mesh(u,ctx,'Curved_Partition',meshes['SM_CurvedPartition'],(-390,0,0),'wall',
                folder='Reference/Props/Partitions')
    box('Curved_Partition_Toe',(-390,0,2),(500,370,4),'black',collision=False,
        folder='Reference/Props/Partitions')
    ctx['reference_props_summary']={'actors':len(ctx['actors'])-before,'artworks':len(hangings),'hero_top_cm':235,
                                    'ceiling_slats':len(CEILING_SLATS),'bench_slats':len(BENCH_SLATS)}
    u.log('REFERENCE_PROPS_OK '+json.dumps(ctx['reference_props_summary']))
    return ctx['reference_props_summary']


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true')
    args = parser.parse_args()
    if args.generate:
        print(json.dumps(generate_assets(), indent=2))

"""Run inside UE Editor; deterministic, separately saved reference gallery."""
import unreal
import sys
import json
import importlib
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Tools'))
BASE = '/Game/ReferenceGallery'
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def _update_cached(m, color, roughness, metallic, emission):
    """Rewrite the value nodes of an existing material in place.

    Without this, an idempotent builder returns the cached asset and every
    colour/roughness tweak silently does nothing -- the render stays
    byte-identical and looks like the change "had no effect".
    """
    base = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_BASE_COLOR)
    if base is not None:
        base.set_editor_property('constant', unreal.LinearColor(*color, 1.0))
    for prop, value in ((unreal.MaterialProperty.MP_ROUGHNESS, roughness),
                        (unreal.MaterialProperty.MP_METALLIC, metallic)):
        node = MEL.get_material_property_input_node(m, prop)
        if node is not None:
            node.set_editor_property('r', value)
    emissive = MEL.get_material_property_input_node(m, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if emissive is not None:
        emissive.set_editor_property('constant',
            unreal.LinearColor(*(v * emission for v in color), 1.0) if emission
            else unreal.LinearColor(0.0, 0.0, 0.0, 1.0))
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)


def material(name, color, roughness=0.5, metallic=0.0, emission=0.0):
    path = BASE + '/Materials/M_' + name
    if EAL.does_asset_exist(path):
        # Cached assets are re-checked and rewritten, not returned as-is: a
        # material missing the HISM flag renders grey, and a stale value node
        # makes every later tuning change a silent no-op.
        existing = unreal.load_asset(path)
        if not existing.get_editor_property('used_with_instanced_static_meshes'):
            existing.set_editor_property('used_with_instanced_static_meshes', True)
            unreal.log('REFERENCE_MATERIAL_FLAG fixed M_' + name)
        _update_cached(existing, color, roughness, metallic, emission)
        return existing
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_' + name, BASE + '/Materials', unreal.Material, unreal.MaterialFactoryNew())
    def scalar(value, prop):
        n = MEL.create_material_expression(m, unreal.MaterialExpressionConstant)
        n.set_editor_property('r', value)
        assert MEL.connect_material_property(n, '', prop)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector)
    c.set_editor_property('constant', unreal.LinearColor(*color, 1.0))
    assert MEL.connect_material_property(c, '', unreal.MaterialProperty.MP_BASE_COLOR)
    scalar(roughness, unreal.MaterialProperty.MP_ROUGHNESS)
    scalar(metallic, unreal.MaterialProperty.MP_METALLIC)
    if emission:
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector)
        e.set_editor_property('constant', unreal.LinearColor(*(v * emission for v in color), 1.0))
        assert MEL.connect_material_property(e, '', unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    try:
        # HISM batches (ceiling fins, bench slats) silently fall back to the grey
        # default material without this usage flag.
        m.set_editor_property('used_with_instanced_static_meshes', True)
        MEL.recompile_material(m)
    except Exception as exc:
        print('usage flag skipped for M_' + name + ': ' + str(exc))
    EAL.save_loaded_asset(m)
    return m


def main():
    EAL.make_directory(BASE)
    level = BASE + '/L_ReferenceGallery'
    if EAL.does_asset_exist(level):
        # Deterministic rebuild: reload the saved level and clear it rather than
        # creating a second level asset with the same name.
        assert LES.load_level(level)
        existing = AS.get_all_level_actors()
        for actor in existing:
            AS.destroy_actor(actor)
        unreal.log('REFERENCE_REBUILD cleared ' + str(len(existing)) + ' actors')
    else:
        assert LES.new_level(level)
    mats = {
        'wall': material('Wall', (0.50,0.487,0.465),0.85),
        # Roughness 0.70 (from 0.64 then 0.80): at 0.64 the hero shot showed a
        # near-perfect mirror image of the sculpture and bench; at 0.80 the floor
        # stopped reading as dark polished stone at all and washed out to pale
        # matte grey. The reference is a dark floor with a SOFT reflection, which
        # is between the two.
        'floor': material('Floor', (0.100,0.103,0.109),0.70,0.02),
        # Bench seat pad. The reference bench carries a pale cushion over the
        # timber slats; bare slats read as an unfinished bench, not a gallery one.
        'fabric': material('Fabric', (0.62,0.60,0.555),0.92),
        'ceiling': material('Ceiling', (0.075,0.078,0.082),0.75),
        'metal': material('DuctMetal', (0.29,0.31,0.33),0.38,0.8),
        'bronze': material('Bronze', (0.46,0.23,0.075),0.28,0.82),
        'wood': material('Walnut', (0.23,0.105,0.039),0.48),
        'black': material('Black', (0.012,0.013,0.016),0.43,0.12),
        # MEASURED: at 18x the suspended loop read as dark rings rather than a
        # luminous fixture. The reference's loop is the brightest element in the
        # ceiling plane, so the emissive term is raised well above surface albedo.
        'emissive': material('Light', (1.0,0.93,0.8),0.3,0.0,42.0),
        'glass': material('SmokedGlass', (0.075,0.105,0.12),0.1,0.55),
        'stone': material('PlinthStone', (0.045,0.04,0.034),0.37,0.1),
        # Floor slab joints: pure black on a reflective floor reads as cracks, not
        # as joints. Only slightly darker than the floor itself.
        'joint': material('FloorJoint', (0.055,0.057,0.061),0.62),
    }
    actors = []
    meshes = {k:unreal.load_asset('/Engine/BasicShapes/' + n) for k,n in [('box','Cube'),('cyl','Cylinder')]}
    from reference_rotation import rot
    def shape(kind, name, loc, size, mat, rotation=(0,0,0), collision=True, folder='Reference'):
        # rot() keeps the authored (pitch, yaw, roll) order: the Python binding's
        # positional order is (roll, pitch, yaw), so a positional call silently
        # converts every yaw into a pitch.
        a = AS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*loc), rot(*rotation))
        a.set_actor_label(name)
        a.set_folder_path(folder)
        c = a.static_mesh_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_static_mesh(meshes[kind])
        c.set_material(0, mats[mat] if isinstance(mat,str) else mat)
        a.set_actor_scale3d(unreal.Vector(*(v / 100.0 for v in size)))
        c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
        c.set_mobility(unreal.ComponentMobility.STATIC)
        actors.append(a)
        return a
    def box(name,loc,size,material,rotation=(0,0,0),collision=True,folder='Reference'):
        return shape('box',name,loc,size,material,rotation,collision,folder)
    def cyl(name,loc,size,material,rotation=(0,0,0),collision=True,folder='Reference'):
        return shape('cyl',name,loc,size,material,rotation,collision,folder)
    ctx = dict(box=box,cyl=cyl,mat=mats,materials={'door':mats['glass'],'metal':mats['metal']},actors=actors,root=ROOT,base=BASE)
    summary = {}
    for name in ['reference_layout','reference_props','reference_lighting','reference_technical']:
        module = importlib.import_module(name)
        before = len(AS.get_all_level_actors())
        module.build(ctx)
        summary[name] = len(AS.get_all_level_actors()) - before
        unreal.log('REFERENCE_MODULE_OK ' + name + ' actors=' + str(summary[name]))
    assert LES.save_current_level()
    EAL.save_directory(BASE, only_if_is_dirty=False, recursive=True)
    all_actors = AS.get_all_level_actors()
    data = {'map':BASE+'/L_ReferenceGallery','module_actor_counts':summary,'total_actors':len(all_actors),'actors':[{'label':a.get_actor_label(),'class':a.get_class().get_name(),'position':str(a.get_actor_location())} for a in all_actors]}
    (ROOT/'Saved'/'reference_build.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    unreal.log('REFERENCE_BUILD_SUCCESS ' + str(len(all_actors)))

if __name__ == '__main__':
    main()

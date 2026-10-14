"""Decisive test: put the art material on a plain engine Plane and screenshot.

Bypasses the custom art mesh entirely. If the texture shows on a fresh plane the
fault is the art mesh; if it does not, the fault is the material.
"""
import unreal

LEVEL = '/Game/ReferenceGallery/L_ReferenceGallery'
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL):
    unreal.log_error('UVPROBE could not load level')
AS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in AS.get_all_level_actors():
    if a.get_actor_label().startswith('UVPROBE'):
        AS.destroy_actor(a)

mesh = unreal.load_asset('/Engine/BasicShapes/Plane')
unreal.log('UVPROBE plane valid=%s' % unreal.SystemLibrary.is_valid(mesh))
# Engine Plane faces local +Z; rotate -90 pitch so it faces -X (toward the camera).
for i, (x, y) in enumerate([(-620, -400), (-620, 400)]):
    for matname in ('M_OrbitForms', 'M_ContourField'):
        a = AS.spawn_actor_from_class(unreal.StaticMeshActor,
                                      unreal.Vector(x, y + (0 if matname.endswith('OrbitForms') else 320), 220),
                                      unreal.Rotator(0, -90, 0))
        a.set_actor_label('UVPROBE_%d_%s' % (i, matname))
        comp = a.static_mesh_component
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(mesh)
        comp.set_material(0, unreal.load_asset('/Game/ReferenceGallery/Materials/' + matname))
        a.set_actor_scale3d(unreal.Vector(3.0, 3.0, 3.0))
unreal.log('UVPROBE spawned 4 test quads at x=-620 facing -X')

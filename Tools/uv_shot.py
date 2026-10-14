"""Screenshot the UV probe quads, then clean them up."""
import unreal

LEVEL = '/Game/ReferenceGallery/L_ReferenceGallery'
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL):
    unreal.log_error('UVSHOT could not load level')
AS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Camera looking at the probe quads at x=-620 from x=-300
cam = None
for a in AS.get_all_level_actors():
    if a.get_actor_label() == 'UVSHOT_Camera':
        cam = a
        break
if cam is None:
    cam = AS.spawn_actor_from_class(unreal.CameraActor,
                                    unreal.Vector(-300.0, 0.0, 220.0),
                                    unreal.MathLibrary.find_look_at_rotation(
                                        unreal.Vector(-300.0, 0.0, 220.0),
                                        unreal.Vector(-620.0, 0.0, 220.0)))
    cam.set_actor_label('UVSHOT_Camera')
cam.get_component_by_class(unreal.CameraComponent).set_editor_property('field_of_view', 70.0)

pc = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.log('UVSHOT camera at %s' % cam.get_actor_location())
unreal.EditorLevelLibrary.pilot_level_actor(cam)
unreal.log('UVSHOT done - now render a viewport screenshot')

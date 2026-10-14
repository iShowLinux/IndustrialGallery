"""Line-trace from each artwork-view camera to its canvas; report the first hit."""
import unreal

LEVEL = '/Game/ReferenceGallery/L_ReferenceGallery'
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL):
    unreal.log_error('TRACE could not load level')
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

CASES = [
    ('shot5', unreal.Vector(-445, 90, 183), unreal.Vector(-684.1, 90, 183)),
    ('shot6', unreal.Vector(-445, 600, 177), unreal.Vector(-684.1, 600, 177)),
]
for name, start, end in CASES:
    hit = unreal.SystemLibrary.line_trace_single_by_channel(
        world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.TraceQueryTest.TRACE_TEST_VISIBILITY, False)
    if hit:
        actor = hit.actor
        unreal.log('TRACE %s HIT %s at %s dist %.0f' % (
            name, actor.get_actor_label() if actor else '?',
            hit.impact_point, (hit.impact_point - start).length()))
    else:
        unreal.log('TRACE %s NO HIT' % name)

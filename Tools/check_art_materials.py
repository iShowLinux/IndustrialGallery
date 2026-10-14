"""Report the material actually assigned to each artwork canvas actor."""
import unreal

BASE = '/Game/ReferenceGallery'
LEVEL = '/Game/ReferenceGallery/L_ReferenceGallery'
# Load the level first: with no level open the actor subsystem is empty and this
# script silently reports nothing at all.
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL):
    unreal.log_error('ART could not load ' + LEVEL)
AS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
count = 0
for actor in AS.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.endswith('_Canvas'):
        continue
    count += 1
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = comp.static_mesh
    mat = comp.get_material(0)
    unreal.log('ART %s mesh=%s mat=%s' % (
        label, mesh.get_name() if mesh else None, mat.get_name() if mat else None))
    if mat is not None:
        # Read the sampler and the base-colour connection back from disk. A
        # material can carry the right NAME while its texture pin is unwired,
        # which renders as the engine grey default with no error in any log.
        mel = unreal.MaterialEditingLibrary
        sampler = None
        for e in mel.get_material_expressions(mat):
            if e.__class__.__name__.startswith('MaterialExpressionTextureSample'):
                sampler = e
                break
        if sampler is None:
            unreal.log('ART_NOSAMPLER ' + label)
            continue
        tex = sampler.get_editor_property('texture')
        unreal.log('ART_SAMPLER %s texture=%s type=%s' % (
            label, tex.get_name() if tex else 'NONE',
            sampler.get_editor_property('sampler_type')))
        base = mel.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
        unreal.log('ART_BASE %s <- %s' % (
            label, base.__class__.__name__ if base else 'NONE'))

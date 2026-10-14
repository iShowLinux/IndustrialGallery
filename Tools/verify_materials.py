"""Read material values back from disk -- never trust the builder's own report."""
import unreal

BASE = '/Game/ReferenceGallery/Materials/'
MEL = unreal.MaterialEditingLibrary
for name in ('M_Wall', 'M_Floor', 'M_Light', 'M_Ceiling'):
    mat = unreal.load_asset(BASE + name)
    if mat is None:
        unreal.log('VERIFY ' + name + ' MISSING')
        continue
    base = MEL.get_material_property_input_node(mat, unreal.MaterialProperty.MP_BASE_COLOR)
    rough = MEL.get_material_property_input_node(mat, unreal.MaterialProperty.MP_ROUGHNESS)
    emis = MEL.get_material_property_input_node(mat, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.log('VERIFY %s base=%s rough=%s emissive=%s hism=%s' % (
        name,
        base.get_editor_property('constant') if base else None,
        rough.get_editor_property('r') if rough else None,
        emis.get_editor_property('constant') if emis else None,
        mat.get_editor_property('used_with_instanced_static_meshes')))

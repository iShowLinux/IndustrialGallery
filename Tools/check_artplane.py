"""Check the art material graph and texture settings node by node."""
import unreal

TEX = '/Game/ReferenceGallery/Textures/T_OrbitForms'
mat = unreal.load_asset('/Game/ReferenceGallery/Materials/M_OrbitForms')
tex = unreal.load_asset(TEX)
unreal.log('UVCHECK texture valid=%s' % unreal.SystemLibrary.is_valid(tex))
if tex:
    unreal.log('UVCHECK texture size=%dx%d srgb=%s group=%s' % (
        tex.blueprint_get_size_x(), tex.blueprint_get_size_y(),
        tex.get_editor_property('srgb'), tex.get_editor_property('lod_group')))
mel = unreal.MaterialEditingLibrary
unreal.log('UVCHECK material=%s expressions=%d' % (
    mat.get_name(), len(mel.get_material_expressions(mat))))
for e in mel.get_material_expressions(mat):
    desc = e.__class__.__name__
    try:
        if desc.startswith('MaterialExpressionTextureSample'):
            t = e.get_editor_property('texture')
            desc += ' tex=%s' % (t.get_name() if t else 'NONE')
        if desc == 'MaterialExpressionConstant':
            desc += ' r=%s' % e.get_editor_property('r')
    except Exception:
        pass
    unreal.log('UVCHECK   node %s' % desc)
for prop in ('MP_BASE_COLOR', 'MP_ROUGHNESS', 'MP_METALLIC'):
    try:
        node = mel.get_material_property_input_node(mat, getattr(unreal.MaterialProperty, prop))
        unreal.log('UVCHECK %s <- %s' % (prop, node.__class__.__name__ if node else 'NONE'))
    except Exception as exc:
        unreal.log('UVCHECK %s unreadable (%s)' % (prop, exc))

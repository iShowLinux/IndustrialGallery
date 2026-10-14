"""Import the art plane via a fresh path and read its UVs back.

The material, texture and material graph all verify correct, so the remaining
suspect is the mesh's UV channel. This re-imports into a scratch path with UV
import explicitly enabled and compares.
"""
import unreal

SRC = unreal.Paths.project_dir() + 'Assets/Reference/Meshes/SM_ArtPlane.obj'
DEST = '/Game/ReferenceGallery/UVProbe'

task = unreal.AssetImportTask()
task.set_editor_property('filename', SRC)
task.set_editor_property('destination_path', DEST)
task.set_editor_property('destination_name', 'SM_ArtPlaneProbe')
task.set_editor_property('automated', True)
task.set_editor_property('replace_existing', True)
task.set_editor_property('save', True)
options = unreal.FbxImportUI()
options.set_editor_property('import_mesh', True)
options.set_editor_property('import_as_skeletal', False)
options.set_editor_property('import_materials', False)
options.set_editor_property('import_textures', False)
options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
options.set_editor_property('automated_import_should_detect_type', False)
data = options.get_editor_property('static_mesh_import_data')
data.set_editor_property('combine_meshes', True)
data.set_editor_property('auto_generate_collision', False)
data.set_editor_property('generate_lightmap_u_vs', False)
task.set_editor_property('options', options)
task.set_editor_property('factory', unreal.FbxFactory())
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

probe = unreal.load_asset(DEST + '/SM_ArtPlaneProbe')
unreal.log('UVPROBE imported=%s' % unreal.SystemLibrary.is_valid(probe))
if probe:
    # LOD0 vertex buffer UVs
    try:
        lod = probe.get_editor_property('render_data').get_editor_property('lod_resources')
        unreal.log('UVPROBE lod_resources=%d' % len(lod))
        for i, entry in enumerate(lod):
            vb = entry.get_editor_property('vertex_buffer')
            unreal.log('UVPROBE lod%d vertex_buffer valid=%s' % (i, vb is not None))
            if vb:
                try:
                    num_uv = vb.get_num_tex_coords(0)
                    unreal.log('UVPROBE lod%d num_tex_coords=%d' % (i, num_uv))
                    for v in range(min(4, vb.get_num_vertices())):
                        unreal.log('UVPROBE lod%d v%d uv=%s' % (i, v, vb.get_vertex_uv(v)))
                except Exception as exc:
                    unreal.log('UVPROBE lod%d uv read failed: %s' % (i, exc))
    except Exception as exc:
        unreal.log('UVPROBE render_data read failed: %s' % exc)

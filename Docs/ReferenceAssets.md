# Reference gallery: original props and asset provenance

## Integration

`Tools/reference_props.py` exports **`build(ctx)`**, called after `reference_layout.build(ctx)` by the parent builder. It requires `box`, `cyl`, `mat`, and `actors` in `ctx`. Helpers use centimetres and `(pitch, yaw, roll)` rotations — and construct every
`unreal.Rotator` through `reference_rotation.rot()`, because the Python binding's
positional order is `(roll, pitch, yaw)`. Calling `unreal.Rotator(*tuple)` with an
authored C++-order tuple silently turns every yaw into a pitch (flat artwork,
vertical ducts, every aimed light firing along +X). See `Docs/ReferenceGallery.md`. It adds editor-authored props only; it does not launch Unreal, create/save a level, change project configuration, or edit C++.

The module imports source assets exclusively into:

- `/Game/ReferenceGallery/Meshes`
- `/Game/ReferenceGallery/Textures`
- `/Game/ReferenceGallery/Materials`

Existing assets are reused. Rebuilding the **level** should start from the parent's new level; calling `build(ctx)` twice on an existing populated level duplicates props. If source geometry/textures are regenerated after a first import, explicitly reimport the corresponding existing assets in Unreal before rebuilding. The module does not overwrite unrelated editor edits.

## Delivered composition

- **Continuity:** three unequal, interwoven, variable-width bronze ribbons, generated as actual closed smooth-normal triangle meshes. No cylinder or generic torus stands in for the hero. Source bounds are approximately 116.386 x 63 x 195 cm. The base sits at `(220,-120,40)` on a 140 x 100 x 40 cm stone plinth; the sculpture's top is exactly Z=235 cm.
- A small white interpretation plinth with a readable original title card.
- **Counterform:** a second curved bronze form supporting a stone orb at the rear `(-150,700)`, with its own low stone base and label; a smaller nearby white study plinth supports a bronze orb.
- Walnut slatted bench centered at `(-200,-70)`, long axis Y, 44 x 145 cm seat, top Z=45. Nine separate slat instances, metal support rails, legs, feet and a simple collision seat carrier. A pale **fabric seat cushion** sits over the slats at Z=48.5 (non-colliding; the carrier below owns seat collision), matching the reference bench, which carries a pad rather than bare slats.
- 73 narrow overhead timber fins at Z=406..410; two long metal ducts, a transverse duct, couplings, 34 modeled clamp rings and hangers. Main ducts/bands remain below Z=410. Suspended light fixtures extend lower, intentionally.
- Three track rails with 21 adapters, stems, tilted spotlight housings and small emissive lenses. **Actual light actors are the lighting module's responsibility.**
- Seven framed hangings with separate backing, pale mat, four wood frame rails, single artwork UV plane and nearby black/gold title card. Side art is at X=+/-688, facing inward; wall-pier Y locations are avoided. The large chromatic rear-divider piece faces -Y at `(-330,418,155)`. Entry and rear-door wall openings stay clear.
- No decals were added: subtle floor detailing belongs to the shell module, avoiding overlapping floor planes or unnecessary decal cost.

## Origins / rights notes

All six OBJ files, five artwork compositions, seven label textures, and the walnut grain texture are **locally generated original project assets**. The generation code is in `Tools/reference_props.py`, using Python's standard library and installed Pillow. Random details use a fixed seed (731).

The user-provided reference JPG is visual guidance for gallery composition only. Its pixels, paintings, watermark and branding were not extracted or distributed. The artwork here does not claim to reproduce the original photograph's paintings or to be work by any named artist.

- `SM_BronzeLoop.obj`: analytic swept elliptical ribbon cross-sections, three unequal closed curves.
- `SM_RearLoop.obj`: original asymmetric closed supporting loop.
- `SM_ArtPlane.obj`: original UV-mapped plane; local X horizontal, Z up, front -Y.
- `SM_CeilingSlats.obj`, `SM_BenchSlats.obj`: combined original box geometry for the single-actor fallback path.
- `SM_DuctBands.obj`: combined original toroidal clamp geometry.
- `T_Chromatic_01..03.png`: original warm/cool intersecting polygons, arcs and fine marks; 1024 x 1280.
- `T_ContourField.png`: original gestural contour-line composition; 1536 x 640.
- `T_QuietTerrain.png`: original layered hill/sun composition; 1024 x 768.
- `T_Label_01..07.png`: original collection typography; 1024 x 320. The system Arial font is rasterized locally when present; no font binary is copied or distributed. Pillow's bundled default font is the fallback.
- `T_WalnutGrain.png`: original fine grain lines; 512 x 1024.
- `SourcePreview.png`: offline source-mesh/artwork contact sheet, **not an Unreal screenshot**. Its simple software triangle shading is not the final engine material or lighting.

Engine-provided basic Cube, Cylinder and Sphere assets remain engine dependencies; they are not copied into `Assets/Reference` or represented as original third-party content.

## Optimization and import contracts

| Source mesh | Triangles |
|---|---:|
| Hero bronze loops | 14,336 |
| Rear bronze loop | 2,304 |
| Artwork plane | 2 |
| Ceiling slats fallback | 876 |
| Bench slats fallback | 108 |
| Combined duct bands | 17,408 |

`Assets/Reference/manifest.json` is the generated inventory, including vertex counts, triangle counts, bounds, texture paths and instance counts.

- Repeated ceiling and bench timber first attempts **HISM**, one serialized actor/component per batch, using `SubobjectDataSubsystem`. UE 5.8's `SubobjectDataBlueprintFunctionLibrary.get_data()` and `get_associated_object()` retrieve the real instance component. If unavailable, a warning is logged and the batch becomes **one combined static-mesh actor**, never dozens of standalone timber actors. Both paths keep the same composition.
- Duct rings are merged into one source mesh/actor/material section. No thousands-of-actors construction.
- The dry-run layout creates **209 prop actors**, including all frame pieces and track housings. This count assumes either one HISM owner or one merged actor per timber batch; Unreal import and component registration still require editor verification.
- Fine decoration, imported sculpture surfaces, art, and overhead services have no collision. Bench supports and plinths use the parent's simple box collision. Imported sculpture does not need complex collision because its pedestal already blocks access.
- OBJ sources are explicit Z-up centimetres with imported vertex normals. Static-mesh import disables scene/unit conversion, sets translation/rotation to zero and uniform scale to one, skips auto-collision and lightmap UV generation, and does not require Nanite. Hero bounds are checked after first import; an unexpected axis/scale conversion raises an error instead of silently accepting the wrong model.
- The explicit legacy `FbxFactory` is used for OBJ; no additional mesh-authoring plugin is required. All import tasks are automated and save assets. Missing source files produce an actionable generation error.
- Art uses an actual UV plane rather than a texture repeated on all faces of a cube. Each material's texture is assigned before compilation, uses a color sampler, and is connected to Base Color with explicit roughness. No transparent glass overlay, unnecessary translucent sorting, or emissive paintings.
- Texture mipmaps remain enabled. Small gallery artwork/label textures are `never_stream=True` for stable cinematic captures. For a substantially larger collection, profile texture memory and allow streaming instead.
- Import and runtime paths use no Pillow. Pillow is needed only to regenerate the already-delivered PNG sources and preview offline.

## Reproduction and verification

From the project root, with the installed system Python:

```bash
python Tools/reference_props.py --generate
python Assets/Reference/verify_assets.py
python Assets/Reference/preview_assets.py
```

Performed offline checks:

1. Python parse/compile check of `Tools/reference_props.py`.
2. Closed manifold edge incidence, finite positions, positive signed volume/outward face winding, hero dimensions and pedestal-relative height.
3. Outward detail-mesh winding, fallback slat UV presence and ceiling/band vertical bounds.
4. Manifest completeness and successful decoding of every authored PNG.
5. Execution of the real `build(ctx)` and framing logic using a documented engine-call test double: seven artworks, correct hero source/placement, 73 ceiling instances, actor budget, and all actor origins within the room.
6. Visual inspection of the offline mesh/artwork contact sheet: open curved loops and nonblank original compositions with legible title card.

**Verification boundary:** Unreal was not launched for this delegated task. No claim is made that assets have already been imported, HISM serialization tested in the live editor, shaders compiled by Unreal, or a final gallery render produced. The parent builder must execute the module and inspect `REFERENCE_PROPS_OK`, import warnings, shader compilation logs and final camera views.

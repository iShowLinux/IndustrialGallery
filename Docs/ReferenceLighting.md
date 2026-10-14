# Reference gallery: lighting and post processing

## Integration

Run `Tools/reference_lighting.py` from the parent editor build, **after the room, partitions and materials exist**:

```python
import reference_lighting
lighting = reference_lighting.build(ctx)
```

`ctx` may be a dictionary or an object exposing:

- `box(name, loc, size, material, rotation=(0,0,0), collision=True, folder=...)`
- `cyl(...)`, same signature; cylinder local Z is its axis. Sizes are world centimetres, not actor scale.
- `mat`: material objects keyed by `metal`, `black`, and `emissive`.
- `actors`: list receiving spawned actors. Geometry helpers register their own actors; this module registers lights and the post-process volume.

The return value contains `lights`, `post_process`, `shadowed_lights`, `ribbon_segments`, and `exposure_bias`. Actors use `Reference/Lighting`; light/volume labels start with `REF_Light_`. The caller owns saving the level. Call once per fresh map: this module does not remove other agents' actors or deduplicate repeated builds.

**Material prerequisite:** `mat['emissive']` must emit actual HDR radiance, not merely use a white base color. A neutral to slightly warm linear emissive multiplier around **64** is a starting point with the authored exposure. Tune that existing material in the parent material builder. It is not modified here. The ribbon's illumination comes from explicit rect lights, not an assumed emissive-only Lumen contribution.

## What is matched

Reference: `C:/Users/mrjul/Downloads/5fa4f58c-618c-43ed-90d1-785c8f010b95.jpg`.

- A large suspended **closed rounded-triangle light ribbon**, bright but thin, below dark industrial ceiling services.
- Neutral/warm wall-art pools, warmer bronze highlights, a slightly cooler cross-light, and a real sculpture shadow against the white partition.
- Restrained bloom, dark reflective flooring and readable white walls; no fake atmospheric fog or visible light shafts. The reference's contrast comes from local illumination and materials, not a fog layer.
- A lit rear artwork/divider and rear sculpture preserve depth beyond the hero partition.

Coordinates follow the supplied room: X ±700, Y ±900, floor Z=0, ceiling Z=420; entrance at Y=-900. Hero camera is `(-580,-780,310)` aimed toward `(80,180,170)`.

## Fixture and light layout

### Ribbon

Nominal triangle vertices XY: `(-410,-270)`, `(380,-90)`, `(-110,430)`. Centerline height Z=350 cm. Quadratic corner fillets trim 18% of adjoining edges. The resulting path has 104 segments; overlapping thin housing and diffuser boxes close the joins. The full fixture adds **214 geometry actors**, including three suspension wires and three ceiling canopies. This is editable prototype geometry, not a high-poly asset; merge to a static mesh later if desired.

The visible ribbon owns its own housing, diffuser, wires and canopies. Ceiling slats, ducts, track rails and spotlight housings remain the props module's responsibility. **Do not create a second luminous ribbon in props.**

Three rect lights underneath approximate its distributed output (not an exact curved area emitter):

| Light | Position | Lumens | Source W × H cm | Kelvin |
|---|---|---:|---:|---:|
| Ribbon_Front | (-15,-185,346) | 3400 | 280 × 14 | 4100 |
| Ribbon_Right | (135,170,346) | 2900 | 220 × 14 | 4100 |
| Ribbon_Left | (-255,85,346) | 2900 | 240 × 14 | 4100 |
| Entry_Ambient | (-245,-625,373) | 2800 | 210 × 160 | 4200 |
| Rear_Ambient | (125,645,373) | 3200 | 240 × 150 | 4200 |

All five aim vertically downward; ribbon source widths align with the corresponding triangle edge. The two ambient sources are broad ceiling-fill approximations, not extra visible fixture meshes. All five cast shadows so illumination does not simply pass through the central partitions. Their attenuation radius is 650 cm.

### Track spots

`SPOTS` in the module is the authoritative position/target table and may be imported by props when orienting heads. Art positions are provisional target centers: if the art module chooses different centers, adjust these rows to match, rather than widening every cone.

| Target group | Count | Lumens each | Kelvin | Shadowing |
|---|---:|---:|---:|---|
| Left side art at Y -570, -30, 585 | 3 | 1250, 1250, 1150 | 3700 | Off |
| Right side art at Y -570, 10, 600 | 3 | 1300, 1300, 1150 | 3700 | Off |
| Bronze key / cross | 2 | 2400 / 1750 | 3400 / 4200 | On |
| Rear divider art | 1 | 1500 | 3700 | On |
| Rear sculpture | 1 | 2000 | 3600 | On |

The six unshadowed wall spots point **outward toward their adjacent side walls**, away from the central partition. Restrained cone angles and target-distance-plus-145 cm attenuation limit leakage. If a prop is placed inside a beam, enable only that spot's shadows instead of turning all shadowing on globally.

**Budget:** 10 spot lights + 5 rect lights = **15 movable local lights, 9 shadowed**. There are no point lights, directional lights, skylights or fog actors in this module. No 30-light shadowed overlap rig. Inverse-square falloff is explicitly enabled on spots; **all local lights explicitly use lumens** before intensity is assigned. Spot/rect forward is local +X; `_aim_angles()` produces negative pitch for downward aiming. Vertical down is pitch **-90**, not +90.

## Exposure and post process

A single unbound volume has priority 100 and blend weight 1. Every edited field includes its corresponding override flag.

- Exposure method: **Manual**.
- Apply Physical Camera Exposure: **False**.
- Exposure compensation: **-5.0 stops**, `EXPOSURE_BIAS` in the module.
- Exposure compensation curve explicitly cleared.
- Lumen GI and reflections selected; scene lighting, final gather and reflection quality each 2.
- Bloom 0.18, threshold 1; vignette 0.12.
- White balance 4200 K, tint 0.
- Motion blur, chromatic aberration and film grain disabled.
- Local exposure highlight/shadow contrast scale both 1; no local tone lifting.

Manual exposure without physical camera exposure starts at EV100=0, so the negative compensation is deliberate for lumen-calibrated interior lighting. **Do not change bias to zero while retaining these lumen values:** that is a large exposure increase, not a neutral reset. A camera's ISO/aperture/shutter must not unexpectedly blacken the room. Camera post-process blend weight should be 0, or its exposure overrides cleared, so it cannot supersede this volume. The old project min/max brightness values are irrelevant to the selected manual method.

## Parent-owned project/render prerequisites (no config edits here)

Verify these in project settings before final rendering:

```ini
[/Script/Engine.RendererSettings]
r.DynamicGlobalIlluminationMethod=1
r.ReflectionMethod=1
r.Shadow.Virtual.Enable=1
r.GenerateMeshDistanceFields=True
r.AllowStaticLighting=False
```

Use deferred desktop rendering, DX12/SM6 where supported, and High/Epic GI/reflection scalability. Software Lumen needs generated mesh distance fields; enabling this can require restart and asset/shader preparation. Hardware ray tracing is optional, not required by the script. The existing config already selects Lumen GI/reflections and virtual shadows; mesh distance fields were not explicitly enabled in the inspected config. Do not use a null-RHI run to judge rendering. Keep walls/ceiling opaque and adequately thick for Lumen occlusion.

The config's default auto-exposure toggle does not replace this explicit manual volume. Do not add an extra skylight as a blind brightness fix: a captured empty sky may contribute nothing, while an unoccluded fill can wash out the reference contrast. Remove/disable legacy `GalleryLighting` actors and any runtime procedural light generation in the new map; otherwise this budget and exposure no longer describe the scene.

## Capture and adjustment handoff

1. Finish shaders and allow Lumen/temporal histories to settle before capturing. Ensure Game Settings exposure is used in the viewport, with no editor EV override.
2. Capture from the specified hero camera and verify the sculpture is in front of the Y=80 partition, ribbon remains above it, and each art pool hits the actual artwork.
3. Compare **the image content, excluding the reference's black letterbox and logo**, not just mean brightness across its whole canvas. Measure white-wall and floor regions separately. The floor is intentionally dark, so a whole-frame dark-pixel percentage is not itself a failure.
4. If everything is too dark/light, adjust only `EXPOSURE_BIAS` by half-stop increments and capture again. Raising it brightens the image. If walls are right but art/bronze is not, change only the corresponding light intensity/aim.
5. If walls are correct but the ribbon is dull, raise its material's emissive multiplier, not room exposure. If the ribbon becomes a fat halo, reduce bloom or emissive strength. Do not add dozens of point lights around the loop.
6. Keep floor roughness around 0.3–0.45 as a starting material choice. Bright sources can retain reflection streaks without turning the entire floor into a white mirror. Material author owns this setting.
7. Inspect logs for failed material compilation and confirm the map actually contains 15 `REF_Light_` light actors plus its post-process volume. Unexpectedly identical captures after material edits often indicate a fallback material or a stale map.

## Validation status

- Python syntax compiled successfully without importing Unreal in a real editor.
- An explicit **UE-free test-double harness** exercised `build(ctx)`: 15 lights, 9 shadowed, 16 registered light/volume actors, 214 fixture geometry calls; positive dimensions, unique geometry labels, in-room centers and a closed finely sampled ribbon path.
- Harness checked explicit lumen units, movable mobility, negative downward pitch, fixed manual exposure, disabled physical camera exposure and every post-process override flag.
- All selected post-process property/override names were cross-checked against the installed UE5.8 `Engine/Classes/Engine/Scene.h`; key light setter methods were checked against installed component headers.
- **No UE process was launched.** The harness is not Unreal API execution, a lighting bake, performance profiling, or a rendered visual acceptance test. Parent editor execution and image measurement are still required. Unsupported mandatory API fields fail loudly rather than silently skipping exposure or Lumen settings.

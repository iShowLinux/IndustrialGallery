# Reference Gallery — how to run it

Project: `C:\Users\mrjul\Documents\IndustrialGallery` (UE 5.8, C++ module `IndustrialGallery`)

Two levels exist and both still work:

| Level | Behaviour |
|---|---|
| `/Game/Gallery/Maps/L_IndustrialGallery` | Original scene. Camera-only overview, spawned by `AGalleryGameMode::BeginPlay`. Unchanged. |
| `/Game/ReferenceGallery/L_ReferenceGallery` | New reference gallery: 518 authored actors, walking visitor, interactive entrance door. |

`GlobalDefaultGameMode` points at `AGalleryGameMode`, which picks behaviour from the map name, so
opening either level gives the right result without editing config.

## Play it

```bash
# Editor, then press Play
"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "C:/Users/mrjul/Documents/IndustrialGallery/IndustrialGallery.uproject"

# Standalone game
"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "C:/Users/mrjul/Documents/IndustrialGallery/IndustrialGallery.uproject" \
  /Game/ReferenceGallery/L_ReferenceGallery -game -windowed -ResX=1600 -ResY=900
```

Controls: **WASD** walk · **mouse / arrow keys** look · **E** open/close the entrance door (stand
back — the leaf refuses to swing into an occupied zone) · **L** toggle showcase lighting.

## Headless verification

`Tools/run_reference.py` is the whole pipeline. Each stage fails loudly instead of reporting success
on stale output: every stage that launches the engine first checks that the module DLL exists and is
newer than every `.cpp`/`.h`, and the `probe` stage parses the log and rejects a FAIL in any case even
if the summary line says PASS.

```bash
python Tools/run_reference.py compile   # UnrealBuildTool; requires "Result: Succeeded" + a fresh DLL
python Tools/run_reference.py author    # rebuild the level from the four build modules
python Tools/run_reference.py capture   # -ReferenceShots: 6 PNGs, 15 s warmup each
python Tools/run_reference.py probe     # -ReferenceProbe: spawn/floor + 16 injected-input cases
python Tools/measure_shots.py           # luminance metrics per shot
python Tools/test_reference_runner.py   # unit-tests the runner's own gates (no Unreal launch)
```

`author` is idempotent: it reloads the saved level and clears it before rebuilding, so re-running
never creates a duplicate `L_ReferenceGallery` asset.

## Geometry verification (run this after any layout change)

```bash
"C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" \
  "C:/Users/mrjul/Documents/IndustrialGallery/IndustrialGallery.uproject" \
  -ExecutePythonScript="C:/Users/mrjul/Documents/IndustrialGallery/Tools/verify_reference_transforms.py" \
  -nullrhi -unattended -nopause -nosplash -stdout -FullStdOutLogOutput
```

Read-only. Loads the saved level and asks the **engine** where things actually point — 39 checks
covering artwork uprightness and wall-facing, duct axes, suspended-fixture horizontality, every aimed
light's forward vector against its own table target, the PlayerStart facing, and a negative control
that the rejected arc wall is absent. It raises at the end, so a run cannot report success while
checks failed. Report: `Saved/ReferenceVerification/transforms.json`.

**Why this exists:** `unreal.Rotator`'s positional argument order is `(roll, pitch, yaw)` — NOT the
C++ `(pitch, yaw, roll)`. Passing an authored C++-order tuple positionally turned every intended yaw
into a pitch: wall art lay flat on its back, ceiling ducts pointed straight up, and every aimed light
fired along world +X. Every parameter readback and the build's own success marker passed the whole
time. All rotation construction now goes through `Tools/reference_rotation.py::rot()`, which takes
`(pitch, yaw, roll)` and builds the binding call with keywords.

## Reference material

`Assets/SplineReference/` holds the recovered evidence for the linked Spline reference
(`Modern Industrial Art Gallery`): a published runtime screenshot, the 397-object runtime transform
inventory, the inline published `.splinecode`, and `RECOVERY_REPORT.md` documenting provenance and its
revision caveat. Read that report before treating any number in it as the latest editor revision.

## Rebuild chain

`Tools/build_reference.py` creates the level and shared materials, then calls, in order:

1. `reference_layout.py` — room shell, partitions, doors, cameras
2. `reference_props.py` — sculpture, bench, ducts, slats, artwork
3. `reference_lighting.py` — ribbon, spots, bounce fill, post-process
4. `reference_technical.py` — door, PlayerStart, audio, light tagging

Order matters: technical runs last because it tags every light component for the `L` key.

## Docs

`Docs/ReferenceArtDirection.md`, `ReferenceLayout.md`, `ReferenceAssets.md`, `ReferenceLighting.md`,
`ReferenceTechnical.md` — one per workstream, each separating verified facts from authored substitutes.

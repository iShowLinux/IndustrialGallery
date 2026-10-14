# Reference gallery technical integration

## Implementation delivered

- `AGalleryVisitor`: real `ACharacter`, capsule radius 28 / half-height 98 cm, gravity 1, walk speed 220 cm/s, step height 30 cm. Camera is 72 cm above capsule origin (nominal standing eye 170 cm). WASD feeds `AddMovementInput`, not teleportation. Mouse uses native axis-key bindings without delta-time scaling. E interacts with the nearest door within its distance limit; L toggles showcase lighting. Input setup needs no Input.ini or authored input assets.
- `AGalleryInteractiveDoor`: Blueprintable actor with registered default-subobject root/meshes, BlockAll leaf collision, 75 degrees/sec hinged motion, and BlueprintCallable `Interact`. A conservative visitor proximity zone pauses rotation and rejects new toggles until the visitor steps clear. This avoids relying on unsupported continuous rotational collision sweeps.
- `AGalleryGameMode`: chooses the walking pawn in `InitGame` only for map names ending in `L_ReferenceGallery` (including PIE prefixes). Other maps preserve the original fixed overview camera / no-default-pawn behavior. The reference branch never spawns the old scene loader.
- `Tools/reference_technical.py`: exposes `build(ctx)`, authors door and PlayerStart in the currently open saved reference world, sets its GameMode override, tags lights, imports original looping room tone, and optionally discovers an existing engine/plugin dust NiagaraSystem. It does not create a world, launch an editor, compile, or save the level: the parent builder owns those operations.

## Exact layout contract (centimeters)

Room: X [-700,700], Y [-900,900], floor Z 0.

| Item | Transform / dimensions |
|---|---|
| Door actor hinge | **(-530,-900,0), yaw 0** |
| Closed leaf local center | **(80,0,120)** |
| Closed leaf size | **160 wide X, 6 thick Y, 240 high Z** |
| Wall opening | **X [-530,-370], centered -450; Y -900; Z [0,240]** |
| Open target | **+95 degrees yaw**, swings toward interior +Y |
| PlayerStart | **(-450,-680,100), yaw +90**, faces +Y |
| Standing eye | Approximately **(-450,-680,170)** after floor settling |

Keep the 205 cm radius around the hinge clear when toggling; the initial PlayerStart is outside that zone and within E interaction range. Clearance checks are intentionally conservative. If the shell opening is larger, add jambs in the layout module, not a second door. Keep only this PlayerStart in the reference map so the default spawn chooser is unambiguous.

## Calling the builder

Compile the new classes and restart the editor first. After layout and lighting have populated `/Game/ReferenceGallery/L_ReferenceGallery`:

```python
import reference_technical
report = reference_technical.build({
    "materials": {"door": door_material, "metal": metal_material},
    "ambient_audio": True,
    "enable_dust": True,
})
# Parent builder must save the current level and dirty asset packages afterward.
```

`ctx` may also be an object with those attributes; missing options use defaults. Material values may be loaded material objects or asset paths. `build` replaces only actors tagged `ReferenceTechnical` on rerun. It preserves existing accent tags and never destroys layout actors.

Call technical integration **after lighting**: every current `LightComponent` becomes movable and its actor receives `ReferenceSwitchableLight`. Actors with `ReferenceAccentLight` retain full intensity in showcase mode; other tagged lights scale to 35%, restoring exactly to their cached intensity on the next L press. Skylights are not touched because they derive from `LightComponentBase`, not `LightComponent`. Author accent tags in the lighting module if desired.

## Audio and dust

- Original periodic room tone is generated using Python stdlib into `Assets/Reference/A_ReferenceRoomTone.wav`: 8 seconds, 22050 Hz, mono PCM16. It contains 47/94/141/233 Hz partials, completes whole periods at the loop boundary, and uses no external recording.
- Builder imports `/Game/ReferenceGallery/Audio/A_ReferenceRoomTone` as a looping SoundWave. Visitor loads that exact asset, plays a non-spatialized attached AudioComponent at volume multiplier 0.18, and logs a warning if missing. Audibility/mix are not yet listened to in-engine.
- Dust is optional and not fabricated. Builder searches Asset Registry NiagaraSystem entries with `dust` in their name, restricted to `/Engine/` or `/Niagara/`, validates existence/type, and only then spawns a NiagaraActor. An optional `dust_asset` setting must still be an existing engine/plugin asset. No system found or unavailable plugin => explicit skipped report. No arbitrary smoke/fire effect is substituted. Installed filesystem search did not identify a usable built-in dust effect; discovery in the parent editor remains authoritative.
- No Niagara C++ module dependency was added. For packaged builds, explicitly cook the audio asset/directory; it is loaded by runtime path rather than a serialized hard reference. Packaging is outside the verified scope here.

## Capture and diagnostics

Launch the reference map with `-game -ReferenceShots` (and an actual rendering backend, not `-nullrhi`). Capture waits **15 wall-clock seconds at each view**, calls genuine `FScreenshotRequest::RequestScreenshot`, checks a fresh nonempty file, and exits after all three. Each request has a 30-second save timeout and fails with exit status 1 if blocked. Stale files are removed before requesting a new capture; failure to remove is fatal.

Output directory: `Saved/Screenshots/WindowsEditor/`.

| File | Camera eye | Look target | FOV |
|---|---|---|---|
| `Reference_01_Hero.png` | (-580,-780,310) | (80,180,170) | 70 |
| `Reference_02_Walkthrough.png` | (-450,-680,170) | (-250,350,170) | 70 |
| `Reference_03_Detail.png` | (320,-80,170) | (680,260,160) | 55 |

Capture uses a separate camera actor so the hero view does not disable the visitor's physical gravity/collision. Player move/look input is ignored during capture. Normal play is never put into capture mode without the flag. Composition of the detail shot must be reviewed against the parent's finished asset placement.

`-ReferenceProbe` waits four seconds, logs visitor possession/type, grounded movement, enabled collision/gravity, and feet-to-floor trace agreement within 6 cm. On its own it exits 0/1 for pass/fail. Combined with `-ReferenceShots`, probe results are logged but capture controls final exit. **This is a spawn/floor probe, not a locomotion or wall-stop test.**

Expected runtime log prefixes: `ReferenceVisitor`, `ReferenceDoor`, `ReferenceShots`, `ReferenceProbe`, `ReferenceTechnical`.

## Verification status

### Verified without editor launch

- Python syntax compilation (`python -m py_compile Tools/reference_technical.py`) passed.
- Original WAV test first failed because builder was missing; after implementation it passed: actual generated WAV is mono, PCM16, 22050 Hz, exactly eight seconds, with nonzero audio frames.
- Static checks passed for all six owned C++ source/header files: balanced delimiters, reflected-header pragma once, exactly one GENERATED_BODY per header, generated header last.
- Reviewed relevant installed UE5.8 declarations for native `BindAxisKey`, screenshot request signatures, world settings access, light intensity setter, AudioComponent spatialization flag, and SoundWave looping property.
- `IndustrialGallery.Build.cs` was left unchanged; all new native code uses already-declared Engine/Core/InputCore modules.

### Not verified here (parent explicitly owns build/editor)

- **No C++ compile/UHT/link, editor launch, Unreal Python execution, map save, or screenshot rendering performed by this subagent.** Static checks are not a compile.
- Door open/close clearance, wall blocking, WASD/mouse focus, floor settling, lighting switch appearance, audio playback, and saved-map persistence require parent runtime verification.
- Niagara system availability and effect appearance are not established; omission is an intentional supported outcome.
- Parent should build, run `build(ctx)` last, save the map, run standalone `-ReferenceProbe`, run `-ReferenceShots`, inspect all PNGs/logs, and manually walk into a wall and toggle the door/light modes.

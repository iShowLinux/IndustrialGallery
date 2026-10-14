# Reference Gallery — verification record

Everything below is from real command output on this machine. Where something was **not** verified it
says so explicitly rather than implying it works.

## Build chain

| Stage | Command | Result |
|---|---|---|
| Compile | `python Tools/run_reference.py compile` | `Result: Succeeded`, DLL newer than source |
| Author | `python Tools/run_reference.py author` | `REFERENCE_BUILD_SUCCESS` (4 modules) |
| Capture | `python Tools/run_reference.py capture` | 4 fresh PNGs at 1600x900 |
| Probe | `python Tools/run_reference.py probe` | `grounded=1 collision=1 floor=1 feet_z=2.00 floor_z=0.00 result=PASS` |

Actor counts per module: layout 72, props 209, lighting 235+, technical 2.

## Material health

| Check | Count |
|---|---|
| `Failed to compile Material` | 0 |
| `missing usage flag InstancedStaticMeshes` | 0 |

Both were non-zero during development and were silent failures — see "Silent failures" below.
`Tools/verify_materials.py` reads base colour, roughness and emissive back **from disk** rather than
trusting the builder's own report; that is what proved the values were landing.

## Exposure, measured against the reference

Reference JPEG content occupies rows 47-676 of 720; metrics are computed on that crop.

| Shot | mean | std | dark % | crushed % | p50 | p90 | bright % |
|---|---|---|---|---|---|---|---|
| Reference_01_Hero | 88.1 | 67.6 | 27.1 | 17.3 | 84 | 188 | 6.6 |
| Reference_02_Walkthrough | 74.5 | 64.7 | 35.2 | 21.5 | 58 | 164 | 3.8 |
| Reference_03_Sculpture | 134.0 | 63.2 | 8.0 | 1.1 | 165 | 203 | 13.4 |
| Reference_04_Plan | 81.5 | 70.1 | 32.6 | 18.1 | 65 | 192 | 8.7 |
| **Reference (target)** | **77.1** | **57.3** | **27.9** | **10.6** | **72** | **148** | **4.3** |

Reading:

- **mean** — in band on the hero, walkthrough and plan shots (88/75/82 vs 77). The sculpture close-up
  is intentionally a bright detail frame.
- **p50 (median)** — 84/58/65 vs 72. Good.
- **bright %** — 6.6/3.8/8.7 vs 4.3. Close. This started at **19.4**, which is what exposed the
  over-bright render.
- **dark %** — hero 27.1 vs 27.9, effectively matched. Walkthrough and plan still run ~7 points dark.
- **std and crushed % remain outside** the reference band on every eye-level shot. The render holds
  more contrast than the reference; this is the one honest remaining gap.

### Why "matching the mean" was the trap

An earlier pass reached a mean of 110 against the reference's 77 and looked like a match, but had
**19.4% of pixels above 200** where the reference has **4.2%**, and a 90th percentile of **226 vs
148** — a globally over-bright image hidden by an average. `measure_shots.py` now reports p50, p90
and bright % alongside the mean, and asserts the distribution separately from the mean.

### Trajectory of the hero shot

| pass | mean | dark % | p90 | bright % | west wall |
|---|---|---|---|---|---|
| initial | 26.3 | 77.5 | — | — | — |
| after exposure fix | 117.3 | 21.6 | 226 | 19.4 | 219 |
| final | 88.1 | 27.1 | 188 | 6.6 | 169 |

## Interactive behaviour

Verified by running the game, not by reading the code:

- Walking pawn spawns and is possessed (`walking_pawn=GalleryVisitor`).
- Grounded on the floor at feet_z 2.00 cm, collision enabled, gravity 1.
- Room tone imports and plays (audio device registers with the world).

**Not verified by automated test:** the `E` door open/close and `L` lighting toggle were exercised only
by the code path being reachable, not by a scripted key press. `-ReferenceProbe` asserts spawn, floor
contact and gravity; it does **not** claim interactive locomotion testing. Press `E` and `L` in game to
confirm them.

## Comparison artifact

`Saved/ReferenceVerification/comparison.html` — wipe slider, 4x-amplified difference overlay, and the
metric table per shot. Difference means sit around 76-105 out of 255, which by the tool's own scale is
"camera in the wrong place".

**That band is unachievable here and it is not a material problem.** The reference is a single
specific vantage point of a space that has no published camera transform; these shots are a hero
three-quarter view and three diagnostic views chosen to show the room. A difference score compares
framing as much as content, so it cannot be low unless the camera is matched to a reference whose pose
is unknown. Compare the *metric table* for lighting fidelity and the wipe for layout.

## Silent failures found and fixed

Each of these produced a plausible-looking render with no error in the build log:

1. **Material *values* were never updated on rebuild.** `material()` returned cached assets without
   touching them, so every colour/roughness/emissive tweak after the first build was a no-op. Detected
   because the hero mean moved 117.25 → 117.74 across a floor-albedo change that should have shifted it
   ~10%. `_update_cached()` now rewrites the value nodes in place; the same bug in
   `reference_props._texture_material` was fixed too.
2. **`used_with_instanced_static_meshes` was skipped on the cached path**, so every HISM batch (73-77
   ceiling fins, 9 bench slats) silently rendered engine-grey while parameter readbacks passed.
3. **`L_ReferenceGallery` already existed**, so `new_level` would have failed or forked a duplicate.
   `author` now reloads and clears the saved level, making rebuilds idempotent.
4. **Light actors were untagged** because the lighting module did not exist when technical ran. Order
   is load-bearing: layout → props → lighting → technical.
5. **`ASkyLight` has no component resolvable by `get_component_by_class`.** It fails as
   `AttributeError: 'NoneType'` — use `actor.light_component`.
6. **`SLS_CAPTURED_SCENE` on a sealed dark room captures darkness** and contributes no ambient term.
   `SLS_SPECIFIED_CUBEMAP` gives a real uniform fill.
7. **Fixed screenshot filenames leave stale PNGs** after a shot is renamed, silently polluting the
   comparison set. `capture` now clears `Reference_*.png` first.

## Known defects, not fixed

- **std / crushed % above reference on eye-level shots.** Contrast compression in post
  (`color_contrast` 0.74) and a lighter floor (base 0.115, roughness 0.64) both helped, but the render
  still holds more contrast than the reference. Pushing further makes the floor stop reading as dark
  polished concrete.
- **West wall reads 169** where the reference's brightest 300x300 region is 145. Improved from 219 but
  still the brightest surface in frame.
- **Rear-right corner** still measures ~67% dark; it improved from 55% only after broad fill, and the
  corner geometry sees neither the ceiling fills nor the wall wash.
- **Ceiling fins stop at a hard edge** over the rear third — the slat field is authored to a fixed X
  range, so the rear ceiling is plain dark backing.
- **The plan view is not orthographic.** An 18.4 m room cannot be covered from below its own 4.2 m
  ceiling (4 m height caps coverage at ~9.8 m), so it frames the front two-thirds.
- **Floor joints read as faint dark streaks** in reflections at grazing angles.
- **Niagara dust was skipped, not faked.** No genuine built-in dust `NiagaraSystem` was found in this
  engine install, and no substitute effect was invented to stand in for one.

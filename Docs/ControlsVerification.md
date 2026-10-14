# Controls verification — Reference Gallery visitor

Scope: `AGalleryVisitor` locomotion and look, and the `-ReferenceProbe` input harness that proves them.

## Verified by actual input injection

`python Tools/run_reference.py probe` drives the real input path: it injects key/axis events through
`APlayerController::InputKey` and measures what the pawn and controller actually did. Binding
declarations alone prove nothing — a binding that is silently ignored (a legacy bind on an
`EnhancedInputComponent`, or a missing mapping) shows up here as zero movement.

Last verified run, **16 of 16 cases PASS**, plus the floor/spawn probe:

| Case | Measured |
|---|---|
| W | forward +163.7 cm, right 0.0, Δz 0.0 |
| A | right −164.1 cm, forward 0.0 |
| S | forward −164.3 cm |
| D | right +164.9 cm |
| Left | yaw −38.673° (crossing 10° → −28.673) |
| Right | yaw +38.504° (crossing 350° → 28.504) |
| Up | pitch +37.829° |
| Down | pitch −37.757° |
| MouseX+ / MouseX− | yaw +18.000° / −18.000° |
| MouseY+ / MouseY− | pitch +18.000° / −18.000° |
| E open / E close | door `bIsOpen` 0→1 then 1→0 |
| L showcase / L normal | switchable light total 59125 → 20693.75 → 59125 (×0.35 exactly) |

Floor/spawn: `grounded=1 collision=1 floor=1 feet_z=2.00 floor_z=0.00 result=PASS`.

Each case asserts sign, magnitude, and isolation: a movement case must not rotate the view, a look
case must not move the pawn, and the wrong-sign case must go red. Yaw deltas are wrap-normalized with
`FMath::FindDeltaAngleDegrees`, and the yaw cases deliberately start at 350° and 10° so a naive
subtraction crosses 0/360 and fails.

## How it is implemented

- **Movement and look are polled in `Tick`** from `PC->IsInputKeyDown` for W/A/S/D and the arrow keys.
  Digital keys are not axis keys; `BindAxisKey(EKeys::Right, …)` silently never fires.
- **Mouse** uses `BindAxisKey(EKeys::MouseX/MouseY, …)`. A mouse reports movement-per-frame, so it is
  **not** multiplied by delta time; a held key yields a constant 1.0 and **is** scaled by delta time
  to become a usable rate (`ArrowLookRate`, default 150°/s).
- **`ApplyLookDelta`** writes an absolute rotation in explicit degrees rather than accumulating
  through the legacy controller multipliers (+2.5 yaw / −2.5 pitch), and clamps pitch to the camera
  manager's `ViewPitchMin/Max`.
- **`DefaultInputComponentClass`** is `/Script/Engine.InputComponent` and `DefaultPlayerInputClass` is
  `/Script/Engine.PlayerInput`. These bindings are legacy; an `EnhancedInputComponent` ignores them
  without an error.
- **Probe timing is simulation time** (`GetWorld()->GetTimeSeconds()`), never wall time, so a
  hitch cannot make a case pass or fail spuriously.

## Known limits

- The probe injects events; it does not synthesise OS-level keyboard hardware. A platform-level
  capture problem (window focus, a remote-desktop session) would not appear here.
- Gamepad input is not bound. The reference scene's published camera is a floating Spline camera and
  has no gamepad mapping to port.
- `E` picks the nearest `AGalleryInteractiveDoor`; the probe asserts the door's `bIsOpen` actually
  toggles, not that the leaf animation looks right.

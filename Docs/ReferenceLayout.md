# Reference gallery — architectural layout

## Deliverable and integration

`Tools/reference_layout.py` exposes `build(ctx)` for the parent's editor-time
`Tools/build_reference.py` orchestrator. It creates **68 static-mesh actors and
4 CameraActors** in the current destination level. The intended destination is
`/Game/ReferenceGallery/L_ReferenceGallery`.

- Uses only the supplied `ctx['box']` helper and shared material keys; camera
  creation uses `EditorActorSubsystem`. The helper sets solid meshes to static
  mobility with `BlockAll` collision.
- Does not open, replace, or save a level itself. The parent creates a fresh
  destination, runs all modules, and saves the complete map. These are authored
  editor actors, not a runtime scene loader.
- Does not touch the old source, maps, game mode, project settings, assets, or
  other modules. Re-running this module alone adds actors; use the parent's
  fresh-level build rather than running it twice in the same level.
- Publishes a serializable `ctx['layout']` contract and returns the same object:
  room dimensions, doorway dimensions, camera labels, reserved sculpture
  envelope, clearances, a walking route, and this module's actor count.
- Outliner folders are `Reference/Layout/{Shell,Doors,Details,Structure,Partitions}`
  and `Reference/Cameras`. Actor labels have the `RG_` prefix.

## Reference interpretation

Reference: `C:/Users/mrjul/Downloads/5fa4f58c-618c-43ed-90d1-785c8f010b95.jpg`, plus the
linked Spline scene `Modern Industrial Art Gallery` recovered under
`Assets/SplineReference/` (see its `RECOVERY_REPORT.md` for provenance and its
revision caveat — the published export is an earlier snapshot than the editor).

The loaded image shows a long, open industrial gallery: dark polished floor,
light warm-grey perimeter walls, a high dark ceiling, a foreground right-hand
sculpture bay formed by a low white L-shaped partition, and a staggered rear-left
art partition. Thin metallic door frames and dark glazing sit behind the display
zones. Clear open aisles matter more than a dense maze of partitions.

The Spline scene's own transform inventory (`published_runtime_metadata.json`,
397 objects) gives its real proportions for comparison, in Spline units
(Y-up, so its `y` is height and its `z` is depth): interior X ≈ -607..707,
depth ≈ -807..565, ceiling ≈ 283. Its ceiling is **three open-web trusses**
(3 × 26 webs) rather than this level's flat slat ceiling, and it has no rear door
bank. Those remain known differences; the plan here was authored from the
reference image before that inventory was recovered.

This module recreates that architectural hierarchy using real engine primitives.
Dimensions and concealed areas are an authored interpretation of one perspective
image, not a measured survey. Material appearance, exhibits, ceiling services,
and final exposure are completed by the other modules.

## Coordinate contract (centimetres)

| Element | Position / dimensions |
| --- | --- |
| Clear interior | X = -700 to +700; Y = -900 to +900; floor Z = 0; ceiling underside Z = 420 |
| Orientation | Entrance/south = Y -900; rear/north = Y +900; east = positive X |
| Wall thickness | 20, outside the clear room envelope |
| Floor slab | Centre (0, 0, -10), size 1440 × 1840 × 20; continuous collision; top exactly Z 0 |
| Ceiling backing | Centre (0, 0, 428), size 1440 × 1840 × 16; underside Z 420 |
| Entrance opening | Centre X -460 at Y -900; 180 clear width × 270 clear height |
| Entrance jambs | Inner faces X -550 / -370; each 5 thick; frame centre Y -902 |
| Rear door bank | Centre X 340 at Y +900; overall framed width 380, with two sidelights |
| Rear double doors | 180 nominal clear opening × 270 high, with two closed static leaves and centre mullion |
| Focal back partition | Centre (215, 80, 132.5), size 430 × 22 × 265 |
| Focal return | Centre (0, -45, 132.5), size 22 × 250 × 265; ends Y -170 and +80 |
| Rear-left partition | Centre (-330, 430, 122.5), size 310 × 22 × 245 |
| Reserved pedestal | X 150..290, Y -170..-70, centred (220, -120); props module owns it |
| Reserved focal exhibit | Same reference envelope, overall top approximately Z 235 |

The X/Y/Z bounds describe the **clear interior**, not the outer shell. Wall
thickness, the foundation, and ceiling backing extend beyond those bounds.
Partition caps are 1 cm thick above the nominal partition height.

### Entrance handoff — important

**No entrance door leaf is created.** The technical module owns the interactive
leaf. Use the clear opening X `[-550, -370]`, Y `-900`, Z `[0, 270]`, centred at
`(-460, -900, 0)`. The metal threshold is flush at Z 0 and non-colliding. No
unbroken front wall or hidden glass pane blocks this opening. Frame collision
is outside the clear opening.

Rear doors are deliberately **closed, colliding, static architectural props**,
not functional exits. Their glazing uses the supplied `glass` material, which is
an opaque smoked-glass approximation in the parent's current palette. There is
no modeled exterior behind them. If these doors become interactive later, remove
or replace the existing rear leaf/glazing collision and center mullion rather
than adding a second leaf over them.

## Composition and structural zoning

1. **Arrival / long view:** the west-offset entrance feeds an open front apron.
   It preserves the strong left perimeter wall and gives an immediate diagonal
   view toward the central exhibit and receding partitions.
2. **Foreground focal bay:** the main back partition lies at Y 80, behind the
   bronze location at Y -120. The short return creates the recognizable L shape
   but ends before the hero-to-sculpture rays cross its X coordinate. There is
   no accidental wall between the elevated hero view and the focal sculpture.
3. **East bypass:** the main partition ends at X 430, leaving an open route to
   the east wall at X 700. The shell's shallow perimeter piers do not turn into
   freestanding columns or interrupt the central view.
4. **Rear-left exhibit bay:** a shorter wall at (-330, 430) gives the reference's
   staggered near-right / far-left composition, with open paths to either side.
5. **Rear return:** an open cross-aisle sits between the rear display and the
   framed door bank. Rear cameras and a turning visitor remain inside the room.

Details are restrained: interrupted black skirting, thin partition toe details,
subtle large-slab floor joints, metallic door stiles/rails/pulls/kickplates, and
six shallow perimeter piers. There are no floor steps, railings, unnecessary
freestanding columns, exterior terrain, or foliage. This module adds only the
plain dark ceiling backing: **ribs, beams, ducts, tracks, light fixtures, and
ceiling dressing remain with the lighting/props agents**.

## Circulation and collision

- A 180 cm clear entrance establishes the primary route width.
- The east bypass is 270 cm nominally, reducing to 258 cm at a shallow wall pier.
- The rear-left partition leaves 215 cm nominally to the west wall.
- The pedestal reservation has 139 cm geometric clearance to the return's east
  face and 139 cm to the focal back wall's south face. The non-colliding toe
  detail reduces the latter visible gap to **138.2 cm**. These exceed the
  requested 120 cm human-circulation target.
- `ctx['layout']['walking_route']` is a floor-level sequence, not a pawn-centre
  route and not a camera tour. Apply capsule/eye height in the technical module.
- The illustrative route comes through the entrance, around the front of the
  pedestal, along the east bypass, across the rear, then back down the west side
  of the focal return. It is not a generated NavMesh or a legal-egress analysis.
- Structural walls, floor, piers, partitions, rear panes and door framing collide.
  Skirting, decorative caps/toes, floor-joint strips, pulls, kickplates, and the
  flush threshold do not. Floor joints are surface marks, never physical gaps.
- Props agents must preserve the route and exhibit clearances. A later bench,
  plinth, or label pedestal can invalidate the shell-only test; rerun collision
  and traversal validation after all modules integrate.

## Saved camera actors

All four are normal `unreal.CameraActor` instances with horizontal FOV **90°**,
16:9 aspect ratio, and explicit look-at rotation. The parent's map save persists
them; this module does not activate a camera or override play behavior.

| Actor label | Location | Look-at target | Purpose |
| --- | --- | --- | --- |
| `RG_Camera_Hero` | (-580, -780, 310) | (80, 180, 170) | Exact requested elevated reference composition |
| `RG_Camera_EntryEye` | (-460, -720, 170) | (180, 50, 150) | Human-height arrival / circulation check |
| `RG_Camera_EastSculpture` | (540, -470, 190) | (220, -120, 145) | Unobstructed focal exhibit inspection |
| `RG_Camera_Return` | (540, 720, 170) | (-150, -200, 145) | Reverse view through the staggered layout |

## Executed verification

Validation used the actual source with Python 3.14, without launching Unreal:

- Python `compile(...)` and `ast.parse(...)`: **PASS**.
- `build(ctx)` executed against a minimal Unreal API / mesh-helper test double:
  **PASS**, 68 mesh actors + 4 camera actors = **72 actors**.
- Unique actor labels, positive mesh dimensions, actor-list registration, and
  all four 90° camera properties: **PASS**.
- Entrance sample points inside the clear opening and absence of a leaf/pane:
  **PASS**.
- Route checked against every colliding shell obstacle at walking height and
  the reserved pedestal AABB, using points no more than 2 cm apart:
  **PASS** for a 90 cm route radius. Minimum sampled centreline clearance was
  **91.445 cm**, near `RG_Partition_Rear_Display`, at approximately
  `(-83.96, 410.40)`. The sampling margin also exceeds half the sample spacing.
- Hero-to-sculpture segment/AABB checks for bottom, top, left and right focal
  targets against every focal-partition piece: **PASS**.

**Not yet verified here:** UE 5.8 API execution, saved-map reopening, final mesh
collision in-engine, NavMesh, actual pawn traversal, lighting, and image/render
fidelity. The parent owns integration and Unreal execution; no Unreal process was
started for this module task.

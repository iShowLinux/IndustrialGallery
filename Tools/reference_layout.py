"""Editor-authored shell for /Game/ReferenceGallery/L_ReferenceGallery.

Call build(ctx) after the parent creates the destination level and materials.
All dimensions are centimetres. Nothing is spawned at BeginPlay. The parent owns
level saving, shared materials, lighting, props, and the interactive entry leaf.
"""

import math

import unreal


ROOM = {"x_min": -700.0, "x_max": 700.0,
        "y_min": -900.0, "y_max": 900.0, "height": 420.0}
ENTRY = {"center": (-460.0, -900.0, 0.0), "clear_width": 180.0,
         "clear_height": 270.0, "wall_depth": 20.0}
REAR_DOOR = {"center": (340.0, 900.0, 0.0), "clear_width": 180.0,
             "clear_height": 270.0, "interactive": False}
CAMERAS = (
    ("RG_Camera_Hero", (-580.0, -780.0, 310.0), (80.0, 180.0, 170.0)),
    ("RG_Camera_EntryEye", (-460.0, -720.0, 170.0), (180.0, 50.0, 150.0)),
    ("RG_Camera_EastSculpture", (540.0, -470.0, 190.0), (220.0, -120.0, 145.0)),
    ("RG_Camera_Return", (540.0, 720.0, 170.0), (-150.0, -200.0, 145.0)),
)


def build(ctx):
    """Populate the current editor level using the parent's real mesh helpers.

    Returns a serializable layout contract and also publishes it as
    ctx['layout']. Helpers register their own actors; camera actors are appended
    here. This module is deliberately not idempotent: rebuild into a fresh level
    using the parent orchestrator rather than deleting another module's actors.
    """
    box = ctx["box"]
    # Validate dependencies before changing the level.
    for key in ("wall", "floor", "ceiling", "black", "metal", "glass"):
        if key not in ctx["mat"]:
            raise KeyError("reference_layout requires material: " + key)
    actors = ctx["actors"]
    first_actor = len(actors)

    def block(name, loc, size, material="wall", collision=True,
              zone="Shell", rotation=(0, 0, 0)):
        if min(size) <= 0:
            raise ValueError("Non-positive dimension: " + name)
        return box("RG_" + name, loc, size, material, rotation=rotation,
                   collision=collision, folder="Reference/Layout/" + zone)

    def x_wall(name, left, right, y, bottom=0.0, top=420.0, depth=20.0):
        return block(name, ((left + right) / 2.0, y, (bottom + top) / 2.0),
                     (right - left, depth, top - bottom))

    def frame(name, center_x, y, width, height, material="metal",
              depth=24.0, trim=5.0):
        # Width/height are clear dimensions; jambs sit OUTSIDE the opening.
        for side, sign in (("Left", -1), ("Right", 1)):
            block(name + "_" + side,
                  (center_x + sign * (width / 2.0 + trim / 2.0), y, height / 2.0),
                  (trim, depth, height), material, zone="Doors")
        block(name + "_Head", (center_x, y, height + trim / 2.0),
              (width + trim * 2.0, depth, trim), material, zone="Doors")

    # Clear room extents are measured to the interior faces. Solid exterior
    # thickness extends 20 cm beyond them; the finished floor is exactly Z=0.
    block("FloorSlab", (0, 0, -10), (1440, 1840, 20), "floor")
    block("Wall_West", (-710, 0, 210), (20, 1800, 420))
    block("Wall_East", (710, 0, 210), (20, 1800, 420))
    # A simple dark soffit only. Ribs, HVAC, tracks and lights belong elsewhere.
    block("CeilingBacking", (0, 0, 428), (1440, 1840, 16), "ceiling")

    # Front opening: raw masonry is 190 wide; 5 cm jambs leave 180 clear.
    # Absolutely no leaf, glass, barrier, or raised threshold spans this opening.
    x_wall("Wall_EntryWest", -720, -555, -910)
    x_wall("Wall_EntryEast", -365, 720, -910)
    x_wall("Wall_EntryLintel", -555, -365, -910, bottom=275)
    frame("EntryFrame", -460, -902, 180, 270)
    block("EntryThresholdFlush", (-460, -902, -0.2), (180, 30, 0.4),
          "metal", collision=False, zone="Doors")

    # Rear glazed service-door bank: two static door leaves and two sidelights.
    # The wall is actually cut out instead of placing panes over a solid wall.
    x_wall("Wall_RearWest", -720, 150, 910)
    x_wall("Wall_RearEast", 530, 720, 910)
    x_wall("Wall_RearLintel", 150, 530, 910, bottom=285)
    frame("RearBankOuter", 340, 902, 370, 280, depth=22)
    frame("RearDoubleDoor", 340, 900, 180, 270, depth=18)
    # Panels are deliberately closed/non-interactive. Walkable rear circulation
    # is in front of them, not a route into an unbuilt exterior space.
    for label, x in (("Left", 293.5), ("Right", 386.5)):
        block("RearDoor_" + label + "_Glass", (x, 904, 139),
              (87, 4, 258), "glass", zone="Doors")
        for stile, dx in (("L", -41.5), ("R", 41.5)):
            block("RearDoor_" + label + "_Stile" + stile,
                  (x + dx, 898, 135), (4, 7, 270), "metal", zone="Doors")
        for rail, z in (("Bottom", 5), ("Top", 265)):
            block("RearDoor_" + label + "_Rail" + rail, (x, 898, z),
                  (87, 7, 10), "metal", zone="Doors")
        block("RearDoor_" + label + "_Kickplate", (x, 895, 16),
              (81, 1, 22), "metal", collision=False, zone="Doors")
        handle_x = x + (30 if label == "Left" else -30)
        block("RearDoor_" + label + "_Pull", (handle_x, 889, 115),
              (2, 4, 34), "metal", collision=False, zone="Doors")
    block("RearDoor_CenterMullion", (340, 900, 135), (6, 18, 270),
          "metal", zone="Doors")
    for side, x in (("Left", 200), ("Right", 480)):
        block("RearSidelight_" + side, (x, 904, 140), (90, 4, 280),
              "glass", zone="Doors")
        block("RearSidelight_" + side + "_Sill", (x, 900, 3),
              (90, 18, 6), "metal", zone="Doors")
    block("RearDoor_Transom", (340, 904, 277.5), (180, 4, 5),
          "glass", zone="Doors")

    # Quiet base detail, interrupted at openings so there are no ankle barriers.
    for side, x in (("West", -699.4), ("East", 699.4)):
        block("Skirting_" + side, (x, 0, 4), (1.2, 1800, 8),
              "black", collision=False, zone="Details")
    for name, left, right, y in (
        ("FrontWest", -700, -555, -899.4),
        ("FrontEast", -365, 700, -899.4),
        ("RearWest", -700, 150, 899.4),
        ("RearEast", 530, 700, 899.4),
    ):
        block("Skirting_" + name, ((left + right) / 2.0, y, 4),
              (right - left, 1.2, 8), "black", collision=False, zone="Details")

    # Perimeter pilasters subdivide the long gallery without adding freestanding
    # columns to the reference's clear sightlines and broad circulation aisles.
    for side, x in (("West", -694), ("East", 694)):
        for index, y in enumerate((-590, 230, 730), 1):
            block("Pier_%s_%02d" % (side, index), (x, y, 210),
                  (12, 26, 420), zone="Structure")

    # Front focal island: the horizontal wall is BEHIND the bronze sculpture.
    # The short return ends north of the hero-to-sculpture sightline.
    block("Partition_Focal_Back", (215, 80, 132.5), (430, 22, 265),
          zone="Partitions")
    block("Partition_Focal_Return", (0, -45, 132.5), (22, 250, 265),
          zone="Partitions")
    block("Partition_Focal_BackCap", (215, 80, 265.5), (430, 22, 1),
          collision=False, zone="Details")
    block("Partition_Focal_ReturnCap", (0, -45, 265.5), (22, 250, 1),
          collision=False, zone="Details")
    block("Partition_Focal_BackToe", (215, 68.6, 4), (430, 0.8, 8),
          "black", collision=False, zone="Details")
    block("Partition_Focal_ReturnToe", (-11.4, -45, 4), (0.8, 250, 8),
          "black", collision=False, zone="Details")

    # Staggered left rear display wall gives the same near-right / far-left
    # rhythm as the reference and makes separate viewing bays without a maze.
    block("Partition_Rear_Display", (-330, 430, 122.5), (310, 22, 245),
          zone="Partitions")
    block("Partition_Rear_Cap", (-330, 430, 245.5), (310, 22, 1),
          collision=False, zone="Details")
    block("Partition_Rear_Toe", (-330, 418.6, 4), (310, 0.8, 8),
          "black", collision=False, zone="Details")

    # NOTE: a swept arc partition was tried here and removed -- its chorded
    # segments read as leaning slabs rather than a curve. The partitions are
    # orthogonal planes, matching the earlier working layout.

    # Sparse hairline joints suggest large polished concrete slabs. They are
    # visual marks, not floor gaps or collision boxes that catch a pawn capsule.
    # The dedicated 'joint' material keeps them from reading as cracks.
    for index, x in enumerate((-500, -100, 300), 1):
        block("FloorJoint_X_%02d" % index, (x, 0, 0.025),
              (0.18, 1800, 0.05), "joint", collision=False, zone="Details")
    for index, y in enumerate((-700, -300, 100, 500), 1):
        block("FloorJoint_Y_%02d" % index, (0, y, 0.025),
              (1400, 0.18, 0.05), "joint", collision=False, zone="Details")

    editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    camera_labels = []
    for label, location, target in CAMERAS:
        origin = unreal.Vector(*location)
        rotation = unreal.MathLibrary.find_look_at_rotation(origin, unreal.Vector(*target))
        camera = editor.spawn_actor_from_class(unreal.CameraActor, origin, rotation)
        if camera is None:
            raise RuntimeError("Could not create camera " + label)
        camera.set_actor_label(label)
        camera.set_folder_path("Reference/Cameras")
        component = camera.get_component_by_class(unreal.CameraComponent)
        component.set_editor_property("field_of_view", 90.0)
        component.set_editor_property("aspect_ratio", 16.0 / 9.0)
        component.set_editor_property("constrain_aspect_ratio", True)
        actors.append(camera)
        camera_labels.append(label)

    layout = {
        "room": dict(ROOM), "entry": dict(ENTRY), "rear_door": dict(REAR_DOOR),
        "cameras": camera_labels, "hero_camera": "RG_Camera_Hero",
        "focal_pedestal_reserved_bounds": ((150, -170, 0), (290, -70, 235)),
        "minimum_primary_route_width_cm": 180,
        "minimum_focal_pedestal_clearance_cm": 138.2,
        "walking_route": [(-460, -810, 0), (-320, -350, 0), (-120, -270, 0),
                          (540, -270, 0), (550, 260, 0), (550, 700, 0),
                          (0, 700, 0), (-80, 450, 0), (-100, 250, 0),
                          (-320, -200, 0)],
        "actor_count": len(actors) - first_actor,
    }
    ctx["layout"] = layout
    unreal.log("REFERENCE_LAYOUT_OK actors=%d cameras=%d" %
               (layout["actor_count"], len(camera_labels)))
    return layout

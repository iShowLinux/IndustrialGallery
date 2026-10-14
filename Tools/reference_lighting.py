"""Reference-gallery practical lighting. Run build(ctx) in the UE editor.

ctx is a dict or object exposing box, cyl, mat and actors (see the lighting doc).
No project config writes, sky actors, fog, level saving, or editor launch here.
"""
import math

import unreal

# rot() builds unreal.Rotator from C++ (pitch, yaw, roll) order; the Python
# binding's positional order is (roll, pitch, yaw). Imported at module scope so
# every helper can use it.
from reference_rotation import rot


FOLDER = "Reference/Lighting"
# Manual exposure with physical camera disabled is EV100=0 before compensation.
# A negative bias is intentional with physically specified lumen light sources.
# MEASURED: -5.0 gave mean 26 / 78% dark; -3.4 gave mean 125 with art spots
# blowing walls to 209; -4.35 gave a mean of 110 that matched the reference's
# mean but had 19.4% of pixels above 200 against the reference's 4.2% and a 90th
# percentile of 226 vs 148. Matching the MEAN while ignoring the distribution
# hid a globally over-bright render. Now tuned against the 90th percentile.
# MEASURED against the linked reference render: at -4.9 the hero shot measured
# mean 113.8 / p50 120 / p90 177 against the reference's 77.1 / 72 / 148 -- ours
# was brighter across the whole distribution, not just at the mean. Matching the
# distribution (p50 and p90, not the mean alone) is what this value is tuned to.
EXPOSURE_BIAS = -5.5
# Lumen counts are scaled as a group so the fixture table stays readable.
LUMEN_SCALE = 1.25
RIBBON_Z = 350.0
RIBBON_VERTICES = ((-410.0, -270.0), (380.0, -90.0), (-110.0, 430.0))

# name, position, aim, lumens, temperature K, outer cone degrees, shadow
# Props may use this same table to place the corresponding track heads.
#
# The six wall-art spots are GENERATED from the prop module's ART_HANGINGS so a
# spot always sits in front of the piece it lights. Hand-listing them is how the
# beams ended up between the artworks: the spots sat at y -570/-30/585 while the
# pieces hang at y -270/90/600, so every canvas fell in a dark gap.
def _art_spots():
    try:
        import reference_props
    except ImportError:
        unreal.log_warning("Reference lighting: reference_props unavailable; art spots skipped")
        return ()
    rows = []
    for name, (wx, wy, wz), width, height, _tex, _label, yaw in reference_props.ART_HANGINGS:
        if wx == 0:
            continue                      # rear divider is lit by its own spot
        side = -1.0 if wx < 0 else 1.0
        stand_off = 180.0
        rows.append((
            "Art_" + name,
            (wx - side * stand_off, wy, 367.0),
            (wx, wy, float(wz)),
            1000.0, 3700.0,
            # Wide enough to cover the piece with margin at this stand-off.
            max(38.0, math.degrees(2.0 * math.atan((max(width, height) * 0.75) / stand_off))),
            False,
        ))
    return tuple(rows)


ART_SPOTS = _art_spots()

SPOTS = ART_SPOTS + (
    # MEASURED: a tight cone at ~1.8 m from the wall produced a blown-out
    # specular pool on the east wall. Wider cones spread the same lumens over
    # more surface. NOTE: these must still be bright enough to make the artworks
    # readable -- at 300 lm the pieces rendered as dark rectangles, so the fix
    # for a hot WALL is cone width and bounce reduction, not starving the art.
    # Aim height is taken from each piece's own z, so the beam lands on the
    # canvas rather than between two of them.
    ("Bronze_Key", (375, -380, 363), (220, -115, 150), 2000, 3400, 34, True),
    ("Bronze_Cross", (-155, -245, 363), (220, -105, 165), 1500, 4200, 30, True),
    ("Rear_Sculpture", (-145, 460, 363), (-150, 700, 150), 2000, 3600, 30, True),
)
# name, position, aim, lumens, source width, source height, temperature
# Broad practical/downward fill; shadowing preserves partition separation.
RECTS = (
    ("Ribbon_Front", (-15, -185, 346), (-15, -185, 0), 3400, 280, 14, 4100),
    ("Ribbon_Right", (135, 170, 346), (135, 170, 0), 2900, 220, 14, 4100),
    ("Ribbon_Left", (-255, 85, 346), (-255, 85, 0), 2900, 240, 14, 4100),
    ("Entry_Ambient", (-245, -625, 373), (-245, -625, 0), 2800, 210, 160, 4200),
    ("Rear_Ambient", (125, 645, 373), (125, 645, 0), 3200, 240, 150, 4200),
)
# Large, shadowless bounce fill. A sealed room has no sky term, so without these
# the walls read as black gaps between pools of light.
BOUNCE = (
    ("Bounce_Centre_Down", (0, 0, 300), (0, 0, 0), 1800, 900, 700, 4600),
    # With the sky light providing the uniform ambient term, these no longer have
    # to carry the whole fill. They sit inboard so inverse-square does not blast
    # the plaster: the west wall measured 193 against a reference whose brightest
    # 300x300 region is 145.
    ("Bounce_West_Up", (-380, 0, 80), (-380, 0, 400), 300, 800, 600, 4600),
    ("Bounce_East_Up", (380, 0, 80), (380, 0, 400), 500, 800, 600, 4600),
    ("Bounce_Front_Up", (-300, -700, 60), (-300, -700, 400), 1600, 700, 600, 4600),
    # MEASURED: the rear half crushed to black. The sky light now covers most of
    # this; the rear bay keeps a modest dedicated wash.
    ("Bounce_Rear_Up", (100, 700, 60), (100, 700, 400), 2600, 700, 600, 4600),
    ("Bounce_Ceiling_Front", (-300, -450, 210), (-300, -450, 420), 2400, 1000, 800, 4700),
    ("Bounce_Ceiling_Rear", (250, 450, 210), (250, 450, 420), 3000, 1000, 800, 4700),
    ("Bounce_East_Rear_Fill", (520, 400, 200), (520, 400, 60), 3200, 900, 700, 4600),
    ("Bounce_RearRight_Corner", (600, 790, 190), (640, 860, 40), 1800, 700, 600, 4600),
    ("Bounce_RearWall_Wash", (100, 780, 210), (100, 898, 210), 2400, 1000, 600, 4600),
)


def _get(ctx, key):
    return ctx[key] if isinstance(ctx, dict) else getattr(ctx, key)


def _aim_angles(start, target):
    """Light forward is local +X: negative pitch aims below the horizon."""
    dx, dy, dz = (target[i] - start[i] for i in range(3))
    if dx == dy == dz == 0:
        raise ValueError("Light position and target must differ")
    return (math.degrees(math.atan2(dz, math.hypot(dx, dy))),
            math.degrees(math.atan2(dy, dx)), 0.0)


def _rounded_triangle(vertices=RIBBON_VERTICES, trim=0.18, corner_steps=12):
    """Closed planar path: quadratic fillets plus straight, subdivided edges."""
    if len(vertices) != 3 or not 0 < trim < 0.5 or corner_steps < 2:
        raise ValueError("Expected three vertices, 0 < trim < .5 and >=2 steps")
    corners = []
    for i, vertex in enumerate(vertices):
        prev, nxt = vertices[(i - 1) % 3], vertices[(i + 1) % 3]
        entry = tuple(vertex[k] + (prev[k] - vertex[k]) * trim for k in range(2))
        exit_ = tuple(vertex[k] + (nxt[k] - vertex[k]) * trim for k in range(2))
        corners.append((entry, vertex, exit_))
    points = []
    for i, (entry, vertex, exit_) in enumerate(corners):
        for step in range(corner_steps):
            t = step / corner_steps
            points.append(tuple((1 - t) ** 2 * entry[k] +
                                2 * (1 - t) * t * vertex[k] +
                                t * t * exit_[k] for k in range(2)))
        next_entry = corners[(i + 1) % 3][0]
        steps = max(1, math.ceil(math.dist(exit_, next_entry) / 22.0))
        for step in range(steps):
            t = step / steps
            points.append(tuple(exit_[k] + t * (next_entry[k] - exit_[k]) for k in range(2)))
    return points


def _ribbon(ctx):
    box, cyl, materials = (_get(ctx, key) for key in ("box", "cyl", "mat"))
    points = _rounded_triangle()
    for i, start in enumerate(points):
        end = points[(i + 1) % len(points)]
        length = math.dist(start, end)
        yaw = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
        mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
        # Very small overlaps close the joins; geometry does not block light.
        # MEASURED: a single thin diffuser read as a hairline from the hero
        # camera. Deepening it and adding an upper emissive face makes the
        # suspended loop legible from below and from across the room.
        box("Ribbon_Housing_%03d" % i, (*mid, RIBBON_Z + 1.5),
            (length + 0.25, 6.5, 3.0), materials["metal"],
            rotation=(0, yaw, 0), collision=False, folder=FOLDER + "/Ribbon")
        box("Ribbon_Diffuser_%03d" % i, (*mid, RIBBON_Z - 0.5),
            (length + 0.3, 7.0, 3.0), materials["emissive"],
            rotation=(0, yaw, 0), collision=False, folder=FOLDER + "/Ribbon")
        box("Ribbon_DiffuserTop_%03d" % i, (*mid, RIBBON_Z + 3.2),
            (length + 0.3, 5.2, 1.0), materials["emissive"],
            rotation=(0, yaw, 0), collision=False, folder=FOLDER + "/Ribbon")
    # Pick points ON the rounded path rather than the trimmed-away vertices.
    for i in range(3):
        x, y = min(points, key=lambda p: math.dist(p, RIBBON_VERTICES[i]))
        cyl("Ribbon_Suspension_%02d" % i, (x, y, 386.5), (0.45, 0.45, 69),
            materials["black"], collision=False, folder=FOLDER + "/Ribbon")
        cyl("Ribbon_Canopy_%02d" % i, (x, y, 418), (7, 7, 2),
            materials["metal"], collision=False, folder=FOLDER + "/Ribbon")
    return len(points)


def _spawn(ctx, cls, name, position, rotation=(0, 0, 0)):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = subsystem.spawn_actor_from_class(cls, unreal.Vector(*position), rot(*rotation))
    if actor is None:
        raise RuntimeError("Unable to spawn " + name)
    actor.set_actor_label("REF_Light_" + name)
    actor.set_folder_path(FOLDER)
    _get(ctx, "actors").append(actor)
    return actor


def _light(ctx, cls, name, position, target, lumens, temperature, radius, shadows):
    # _aim_angles returns C++ (pitch, yaw, roll); _spawn converts via rot().
    actor = _spawn(ctx, cls, name, position, _aim_angles(position, target))
    comp = actor.get_component_by_class(unreal.LightComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_intensity_units(unreal.LightUnits.LUMENS)
    comp.set_intensity(float(lumens) * LUMEN_SCALE)
    comp.set_attenuation_radius(float(radius))
    comp.set_editor_property("use_temperature", True)
    comp.set_temperature(float(temperature))
    comp.set_cast_shadows(shadows)
    comp.set_editor_property("volumetric_scattering_intensity", 0.0)
    comp.set_editor_property("indirect_lighting_intensity", 1.0)
    comp.set_editor_property("specular_scale", 1.0)
    return actor, comp


def _postprocess(ctx):
    actor = _spawn(ctx, unreal.PostProcessVolume, "PostProcess", (0, 0, 200))
    actor.set_editor_property("unbound", True)
    actor.set_editor_property("enabled", True)
    actor.set_editor_property("priority", 100.0)
    actor.set_editor_property("blend_weight", 1.0)
    settings = unreal.PostProcessSettings()
    values = {
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_MANUAL,
        "auto_exposure_apply_physical_camera_exposure": False,
        "auto_exposure_bias": EXPOSURE_BIAS,
        "auto_exposure_bias_curve": None,
        "dynamic_global_illumination_method": unreal.DynamicGlobalIlluminationMethod.LUMEN,
        "reflection_method": unreal.ReflectionMethod.LUMEN,
        "lumen_scene_lighting_quality": 2.0,
        "lumen_final_gather_quality": 2.0,
        "lumen_reflection_quality": 2.0,
        "bloom_intensity": 0.18,
        "bloom_threshold": 1.0,
        "vignette_intensity": 0.12,
        "motion_blur_amount": 0.0,
        "scene_fringe_intensity": 0.0,
        "film_grain_intensity": 0.0,
        "white_temp": 4200.0,
        "white_tint": 0.0,
        # MEASURED: eye-level shots held 21-34% crushed pixels against the
        # reference's 10%. A sealed room has no ambient term, so contrast is
        # compressed about the 0.5 midpoint to lift the blacks directly.
        "color_contrast": unreal.Vector4(0.74, 0.74, 0.74, 1.0),
        "color_gain": unreal.Vector4(1.14, 1.14, 1.14, 1.0),
        "local_exposure_highlight_contrast_scale": 1.0,
        "local_exposure_shadow_contrast_scale": 1.0,
    }
    for name, value in values.items():
        # Required overrides are deliberately fail-fast, never silently ignored.
        settings.set_editor_property("override_" + name, True)
        settings.set_editor_property(name, value)
    actor.set_editor_property("settings", settings)
    return actor


def _sky_light(ctx):
    """Ambient term for a sealed room.

    Without this there is no uniform fill, so every dark corner has to be chased
    with another bounce light -- which puts a hot spot near that light and leaves
    the next corner dark. This is the root fix for the brightness seesaw.
    """
    actor = _spawn(ctx, unreal.SkyLight, "AmbientFill", (0, 0, 330))
    # A SkyLight does not resolve via get_component_by_class; it owns a typed
    # ASkyLight::LightComponent. Returns None on a generic lookup and the
    # failure surfaces as a confusing AttributeError on None.
    comp = actor.light_component
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_intensity(1.3)
    comp.set_light_color(unreal.LinearColor(0.86, 0.90, 1.0, 1.0))
    comp.set_editor_property("lower_hemisphere_is_black", False)
    # MEASURED: SLS_CAPTURED_SCENE captures this sealed, mostly-dark room and so
    # contributes almost no ambient term (rear-right stayed 74% dark). A
    # specified cubemap gives a genuine uniform fill.
    comp.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    comp.set_editor_property("affects_world", True)
    comp.recapture_sky()
    return actor


def build(ctx):
    """Append this lighting rig to a freshly built map; return actors/settings.

    Geometry helpers register their own actors. This module registers lights and
    post process itself. The caller owns saving and should clear the map before
    rebuilding; this function intentionally never deletes another agent's work.
    """
    # Validate the contract before spawning anything.
    for key in ("box", "cyl", "mat", "actors"):
        _get(ctx, key)
    for key in ("metal", "black", "emissive"):
        _get(ctx, "mat")[key]
    segments = _ribbon(ctx)
    sky = _sky_light(ctx)
    lights = []
    for name, position, target, lumens, temperature, cone, shadows in SPOTS:
        radius = min(650.0, math.dist(position, target) + 145.0)
        actor, comp = _light(ctx, unreal.SpotLight, name, position, target,
                             lumens, temperature, radius, shadows)
        comp.set_editor_property("use_inverse_squared_falloff", True)
        comp.set_inner_cone_angle(cone * 0.55)
        comp.set_outer_cone_angle(float(cone))
        comp.set_editor_property("source_radius", 2.5)
        comp.set_editor_property("soft_source_radius", 3.5)
        lights.append(actor)
    for name, position, target, lumens, width, height, temperature in RECTS:
        actor, comp = _light(ctx, unreal.RectLight, name, position, target,
                             lumens, temperature, 650.0, True)
        comp.set_source_width(float(width))
        comp.set_source_height(float(height))
        # Align the long source with its corresponding triangle edge.
        if name.startswith("Ribbon_"):
            edges = {"Ribbon_Front": (0, 1), "Ribbon_Right": (1, 2), "Ribbon_Left": (2, 0)}
            a, b = (RIBBON_VERTICES[i] for i in edges[name])
            yaw = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - 90.0
            # rot(): the binding's positional order is (roll, pitch, yaw), so this
            # must be built from keywords or the -90 pitch becomes a -90 roll.
            actor.set_actor_rotation(rot(pitch=-90.0, yaw=yaw, roll=0.0), False)
        lights.append(actor)
    for name, position, target, lumens, width, height, temperature in BOUNCE:
        actor, comp = _light(ctx, unreal.RectLight, name, position, target,
                             lumens, temperature, 1400.0, False)
        comp.set_source_width(float(width))
        comp.set_source_height(float(height))
        lights.append(actor)
    postprocess = _postprocess(ctx)
    shadow_count = sum(int(row[-1]) for row in SPOTS) + len(RECTS)
    unreal.log("Reference lighting: %d lights + sky light, %d shadowed, %d ribbon segments; manual bias %.2f" %
               (len(lights), shadow_count, segments, EXPOSURE_BIAS))
    return {"lights": lights, "sky_light": sky, "post_process": postprocess,
            "shadowed_lights": shadow_count, "ribbon_segments": segments,
            "exposure_bias": EXPOSURE_BIAS}

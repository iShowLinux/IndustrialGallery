"""Saved-map technical integration. Call build(ctx) AFTER layout and lighting.

ctx may be a dict/object with optional materials mapping (door/metal),
ambient_audio=True, enable_dust=True, and dust_asset (an existing Niagara path).
Returns actor handles and an honest integration report; caller saves the level.
No runtime scene loader, engine launch, or source compilation happens here.
"""
from pathlib import Path
import array
import math
import sys
import wave

from reference_rotation import rot


DOOR_HINGE = (-549.0, -900.0, 0.0)
DOOR_WIDTH = 178.0
DOOR_HEIGHT = 268.0
PLAYER_START = (-450.0, -680.0, 100.0)  # feet settle ~2cm to floor; eye ~170cm
AUDIO_ASSET = "/Game/ReferenceGallery/Audio/A_ReferenceRoomTone"


def write_ambient_wav(destination):
    """Original quiet periodic HVAC-like room tone, mono PCM16, 8s at 22050Hz."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rate = 22050
    samples = array.array("h")
    # Integer-Hz partials complete whole cycles in eight seconds, avoiding seam clicks.
    for index in range(rate * 8):
        t = index / rate
        value = (0.032 * math.sin(math.tau * 47 * t)
                 + 0.013 * math.sin(math.tau * 94 * t)
                 + 0.007 * math.sin(math.tau * 141 * t)
                 + 0.004 * math.sin(math.tau * 233 * t))
        samples.append(round(32767 * value))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(destination), "wb") as sound:
        sound.setnchannels(1)
        sound.setsampwidth(2)
        sound.setframerate(rate)
        sound.writeframes(samples.tobytes())
    return destination


def _option(ctx, name, default=None):
    return ctx.get(name, default) if isinstance(ctx, dict) else getattr(ctx, name, default)


def _tag(actor, value):
    import unreal
    tags = list(actor.get_editor_property("tags"))
    if unreal.Name(value) not in tags:
        tags.append(unreal.Name(value))
        actor.set_editor_property("tags", tags)


def _ambient_audio(unreal):
    source = Path(unreal.Paths.project_dir()) / "Assets" / "Reference" / "A_ReferenceRoomTone.wav"
    write_ambient_wav(source)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source.resolve()))
    task.set_editor_property("destination_path", "/Game/ReferenceGallery/Audio")
    task.set_editor_property("destination_name", "A_ReferenceRoomTone")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    sound = unreal.load_asset(AUDIO_ASSET)
    if sound is None or not isinstance(sound, unreal.SoundWave):
        raise RuntimeError("Room tone import did not create a SoundWave")
    sound.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(sound)
    return sound


def _optional_dust(unreal, subsystem, ctx):
    """Never fabricate an asset path or use a fire/smoke effect as dust."""
    if not _option(ctx, "enable_dust", True):
        return None, "disabled by caller"
    if not hasattr(unreal, "NiagaraActor") or not hasattr(unreal, "NiagaraSystem"):
        return None, "Niagara plugin/Python classes unavailable; skipped"
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    candidates = []
    explicit = _option(ctx, "dust_asset")
    if explicit:
        candidates.append(str(explicit))
    else:
        assets = registry.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Niagara", "NiagaraSystem"), True)
        for asset in assets:
            package = str(asset.package_name)
            if (package.startswith("/Engine/") or package.startswith("/Niagara/")) and "dust" in str(asset.asset_name).lower():
                candidates.append(package)
    for path in sorted(candidates):
        # Only genuine engine/plugin assets qualify, including explicit requests.
        if not path.startswith(("/Engine/", "/Niagara/")):
            continue
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        system = unreal.load_asset(path)
        if not isinstance(system, unreal.NiagaraSystem):
            continue
        actor = subsystem.spawn_actor_from_class(unreal.NiagaraActor, unreal.Vector(100.0, 100.0, 260.0))
        if not actor:
            continue
        actor.set_actor_label("REF_Technical_Dust")
        _tag(actor, "ReferenceTechnical")
        component = actor.get_component_by_class(unreal.NiagaraComponent)
        component.set_asset(system)
        component.set_auto_activate(True)
        return actor, "existing engine Niagara: " + path
    return None, "no existing built-in dust NiagaraSystem found; skipped (no substitute effect)"


def build(ctx=None):
    import unreal
    ctx = {} if ctx is None else ctx
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not world or "L_ReferenceGallery" not in world.get_name():
        raise RuntimeError("Open/create /Game/ReferenceGallery/L_ReferenceGallery before technical build")
    visitor_class = unreal.load_class(None, "/Script/IndustrialGallery.GalleryVisitor")
    door_class = unreal.load_class(None, "/Script/IndustrialGallery.GalleryInteractiveDoor")
    mode_class = unreal.load_class(None, "/Script/IndustrialGallery.GalleryGameMode")
    if not visitor_class or not door_class or not mode_class:
        raise RuntimeError("Compile/restart editor with GalleryVisitor and GalleryInteractiveDoor before build(ctx)")
    # Idempotent only for actors owned by this technical module.
    for actor in subsystem.get_all_level_actors():
        if actor.actor_has_tag("ReferenceTechnical"):
            subsystem.destroy_actor(actor)
    world.get_world_settings().set_editor_property("default_game_mode", mode_class)
    door = subsystem.spawn_actor_from_class(door_class, unreal.Vector(*DOOR_HINGE), unreal.Rotator(0.0, 0.0, 0.0))
    if not door:
        raise RuntimeError("GalleryInteractiveDoor spawn failed")
    door.set_actor_label("REF_Technical_EntranceDoor")
    _tag(door, "ReferenceTechnical")
    door.set_editor_property("width", DOOR_WIDTH)
    door.set_editor_property("height", DOOR_HEIGHT)
    materials = _option(ctx, "materials", {}) or {}
    for component_name, material_name in (("leaf", "door"), ("handle", "metal")):
        material = materials.get(material_name) if isinstance(materials, dict) else None
        if material:
            if isinstance(material, str):
                material = unreal.load_asset(material)
            if material:
                door.get_editor_property(component_name).set_material(0, material)
    start = subsystem.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(*PLAYER_START),
                                             rot(pitch=0.0, yaw=90.0, roll=0.0))
    if not start:
        raise RuntimeError("Reference PlayerStart spawn failed")
    start.set_actor_label("REF_Technical_PlayerStart")
    start.set_editor_property("player_start_tag", "ReferenceVisitorStart")
    _tag(start, "ReferenceTechnical")
    switchable = 0
    for actor in subsystem.get_all_level_actors():
        components = actor.get_components_by_class(unreal.LightComponent)
        if not components:
            continue
        _tag(actor, "ReferenceSwitchableLight")
        for component in components:
            component.set_mobility(unreal.ComponentMobility.MOVABLE)
        # Authored ReferenceAccentLight tags are preserved: these stay bright in showcase mode.
        switchable += len(components)
    audio_path = None
    if _option(ctx, "ambient_audio", True):
        sound = _ambient_audio(unreal)
        audio_path = sound.get_path_name()
    try:
        dust, dust_status = _optional_dust(unreal, subsystem, ctx)
    except Exception as exc:
        dust, dust_status = None, "optional Niagara integration skipped: " + str(exc)
        unreal.log_warning("ReferenceTechnical: " + dust_status)
    report = {
        "door": door, "player_start": start, "dust": dust,
        "door_hinge_cm": DOOR_HINGE, "door_clear_span_x_cm": (-530.0, -370.0),
        "door_height_cm": DOOR_HEIGHT, "player_start_cm": PLAYER_START,
        "switchable_light_components": switchable, "audio_asset": audio_path,
        "dust_status": dust_status,
    }
    unreal.log("ReferenceTechnical: " + str({k: v for k, v in report.items() if k not in ("door", "player_start", "dust")}))
    unreal.log("ReferenceTechnical: actors authored in current world; CALLER MUST SAVE LEVEL")
    return report

import unreal
import time

unreal.log("=== Force Camera Setup ===")

# Get the editor world
unreal_editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = unreal_editor.get_editor_world()
if not world:
    unreal.log("ERROR: No editor world")
else:
    unreal.log("Editor world: " + str(world))

# Get all actors
actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("Total actors: " + str(len(actors)))

# Find the SceneLoader
scene_loader = None
for a in actors:
    label = a.get_actor_label()
    if "SceneLoader" in label or "GallerySceneLoader" in label:
        scene_loader = a
        unreal.log("Found SceneLoader: " + str(label))
        break

if scene_loader:
    # Call LoadScene to spawn all objects
    try:
        scene_loader.load_scene()
        unreal.log("LoadScene called")
    except Exception as e:
        unreal.log("LoadScene error: " + str(e))

# Find the lighting actor
for a in actors:
    label = a.get_actor_label()
    if "Lighting" in label or "GalleryLighting" in label:
        unreal.log("Found Lighting: " + str(label))
        try:
            a.setup_lighting()
            unreal.log("SetupLighting called")
        except Exception as e:
            unreal.log("SetupLighting error: " + str(e))
        break

# Find the GameMode
for a in actors:
    label = a.get_actor_label()
    if "GameMode" in label or "GalleryGameMode" in label:
        unreal.log("Found GameMode: " + str(label))
        break

# Now spawn a camera at the player start position
# The gallery is roughly 1400x1400cm centered around (100, 50)
# Put the camera at a good vantage point
camera_loc = unreal.Vector(100, -500, 300)
camera_rot = unreal.Rotator(-15, 0, 0)

# Try to spawn a CineCameraActor
try:
    cine_class = unreal.CineCameraActor
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cine_class,
        camera_loc,
        camera_rot
    )
    unreal.log("Camera spawned at: " + str(camera_loc))
except Exception as e:
    unreal.log("CineCamera spawn error: " + str(e))
    # Fallback to regular CameraActor
    try:
        cam_class = unreal.CameraActor
        camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
            cam_class,
            camera_loc,
            camera_rot
        )
        unreal.log("CameraActor spawned at: " + str(camera_loc))
    except Exception as e2:
        unreal.log("CameraActor spawn error: " + str(e2))

# Also spawn a PlayerStart
try:
    ps_class = unreal.PlayerStart
    ps = unreal.EditorLevelLibrary.spawn_actor_from_class(
        ps_class,
        camera_loc,
        camera_rot
    )
    unreal.log("PlayerStart spawned")
except Exception as e:
    unreal.log("PlayerStart spawn error: " + str(e))

# Save
unreal.EditorLevelLibrary.save_current_level()
unreal.log("Level saved")

# Count actors again
actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("Total actors after spawn: " + str(len(actors)))

# List first 20 actors
for a in actors[:20]:
    unreal.log("  " + str(a.get_actor_label()) + " (" + str(a.get_class().get_name()) + ")")

unreal.log("=== Done ===")

import unreal
import math

# Create a new level
level_path = "/Game/Gallery/Maps/L_IndustrialGallery"
unreal.log("Creating level: " + level_path)

# Create the map using new_level (correct UE5.8 API)
unreal.EditorLevelLibrary.new_level("/Game/Gallery/Maps/L_IndustrialGallery")

# Spawn the SceneLoader - C++ UCLASS types are exposed directly in Python
scene_loader_class = unreal.GallerySceneLoader
unreal.log("SceneLoader class: " + str(scene_loader_class))

# Spawn SceneLoader actor
scene_loader = unreal.EditorLevelLibrary.spawn_actor_from_class(
    scene_loader_class,
    unreal.Vector(0, 0, 0),
    unreal.Rotator(0, 0, 0)
)
unreal.log("Spawned SceneLoader: " + str(scene_loader))

# Spawn GalleryLighting
lighting_class = unreal.GalleryLighting
lighting = unreal.EditorLevelLibrary.spawn_actor_from_class(
    lighting_class,
    unreal.Vector(0, 0, 0),
    unreal.Rotator(0, 0, 0)
)
unreal.log("Spawned GalleryLighting: " + str(lighting))

# Spawn a camera at a good vantage point
camera_class = unreal.EditorAssetLibrary.load_asset(
    "/Script/Engine.DefaultPawn"
)
# Use a CineCameraActor for better control
cine_camera_class = unreal.EditorAssetLibrary.load_asset(
    "/Script/CinematicCamera.CineCameraActor"
)
if cine_camera_class:
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cine_camera_class,
        unreal.Vector(0, -500, 200),
        unreal.Rotator(-15, 0, 0)
    )
    unreal.log("Spawned CineCamera: " + str(camera))
else:
    unreal.log("CineCamera not found, using default")

# Save the level
unreal.EditorLevelLibrary.save_current_level()
unreal.log("Level saved")

# Also save the map asset
unreal.EditorAssetLibrary.save_asset(level_path)
unreal.log("Map asset saved")

print("Level created successfully with SceneLoader and Lighting")

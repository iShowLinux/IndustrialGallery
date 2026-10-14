import unreal

unreal.log("=== SceneLoader Debug ===")

# Check if the level loaded
editor_world = unreal.EditorEditorSubsystem.get_editor_world()
unreal.log("Editor world: " + str(editor_world))

# List all actors in the level
actors = unreal.EditorLevelLibrary.get_all_level_actors()
unreal.log("Total actors in level: " + str(len(actors)))
for a in actors[:20]:
    unreal.log("  Actor: " + str(a.get_actor_label()) + " class: " + str(a.get_class().get_name()))

# Try to find and spawn SceneLoader
unreal.log("\n=== Spawning SceneLoader ===")
scene_loader_class = unreal.GallerySceneLoader
unreal.log("SceneLoader class: " + str(scene_loader_class))

if scene_loader_class:
    scene_loader = unreal.EditorLevelLibrary.spawn_actor_from_class(
        scene_loader_class,
        unreal.Vector(0, 0, 0),
        unreal.Rotator(0, 0, 0)
    )
    unreal.log("SceneLoader spawned: " + str(scene_loader))
    if scene_loader:
        unreal.log("SceneLoader label: " + str(scene_loader.get_actor_label()))
        # Try to call LoadScene
        try:
            scene_loader.load_scene()
            unreal.log("LoadScene called successfully")
        except Exception as e:
            unreal.log("LoadScene failed: " + str(e))
else:
    unreal.log("ERROR: GallerySceneLoader class not found!")

# Also spawn GalleryLighting
unreal.log("\n=== Spawning GalleryLighting ===")
lighting_class = unreal.GalleryLighting
unreal.log("Lighting class: " + str(lighting_class))

if lighting_class:
    lighting = unreal.EditorLevelLibrary.spawn_actor_from_class(
        lighting_class,
        unreal.Vector(0, 0, 0),
        unreal.Rotator(0, 0, 0)
    )
    unreal.log("Lighting spawned: " + str(lighting))

# Save
unreal.EditorLevelLibrary.save_current_level()
unreal.log("\n=== Done ===")

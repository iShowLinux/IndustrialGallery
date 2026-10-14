using UnrealBuildTool;

public class IndustrialGallery : ModuleRules
{
	public IndustrialGallery(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",   // Enhanced Input System
			"UMG",             // Unreal Motion Graphics (the UI)
			"Slate",
			"SlateCore"
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			// Editor-only automation: creating the gallery map and saving it.
			// Guarded by WITH_EDITOR in the implementation, but the module
			// dependency has to be declared for the editor target to link.
			"UnrealEd",
			// JSON parsing for scene loading
			"Json",
			"JsonUtilities"
		});
	}
}

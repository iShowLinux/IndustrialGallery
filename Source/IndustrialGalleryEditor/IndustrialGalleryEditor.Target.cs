using UnrealBuildTool;

public class IndustrialGalleryEditorTarget : TargetRules
{
	public IndustrialGalleryEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("IndustrialGallery");
	}
}

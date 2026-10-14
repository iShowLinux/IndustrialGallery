#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "GalleryMaterials.generated.h"

UCLASS()
class INDUSTRIALGALLERY_API UGalleryMaterials : public UObject
{
	GENERATED_BODY()

public:
	static const TCHAR* MasterMaterialPath;

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateMaterialInstance(
		const FString& Name,
		const FLinearColor& BaseColor,
		float Metallic,
		float Roughness,
		const FLinearColor& Emissive = FLinearColor::Black,
		float Tiling = 1.0f,
		float BumpStrength = 0.0f);

	// === Material factory methods ===

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateTrussMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateCeilingMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateDuctMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateWallMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateFloorMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreatePaintingMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateFrameMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreatePlaqueMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateSpotMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreatePedestalMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateSculptureBronzeMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateSculptureGoldMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateSculptureDarkMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateLEDMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateBenchMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateDoorMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateSignMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateGlassMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreatePartitionMaterial();

	UFUNCTION(BlueprintCallable, Category = "Materials")
	UMaterialInstanceDynamic* CreateFloorGuideMaterial();
};

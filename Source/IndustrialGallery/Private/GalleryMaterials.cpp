// GalleryMaterials.cpp
// Implements the UGalleryMaterials factory methods.

#include "GalleryMaterials.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/Engine.h"

const TCHAR* UGalleryMaterials::MasterMaterialPath = TEXT("/Game/Gallery/Materials/M_GallerySurface");

UMaterialInstanceDynamic* UGalleryMaterials::CreateMaterialInstance(
	const FString& Name,
	const FLinearColor& BaseColor,
	float Metallic,
	float Roughness,
	const FLinearColor& Emissive,
	float Tiling,
	float BumpStrength)
{
	UMaterialInterface* Master = Cast<UMaterialInterface>(
		StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, MasterMaterialPath));
	if (!Master)
	{
		UE_LOG(LogTemp, Warning, TEXT("GalleryMaterials: Failed to load master material at %s"), MasterMaterialPath);
		return nullptr;
	}

	UMaterialInstanceDynamic* Instance = UMaterialInstanceDynamic::Create(Master, this);
	if (!Instance)
	{
		return nullptr;
	}

	Instance->SetVectorParameterValue(TEXT("BaseColor"), BaseColor);
	Instance->SetScalarParameterValue(TEXT("Metallic"), Metallic);
	Instance->SetScalarParameterValue(TEXT("Roughness"), Roughness);
	Instance->SetScalarParameterValue(TEXT("Emissive"), Emissive.R);
	Instance->SetVectorParameterValue(TEXT("Tiling"), FLinearColor(Tiling, Tiling, Tiling, 1.0f));
	Instance->SetScalarParameterValue(TEXT("BumpStrength"), BumpStrength);

	return Instance;
}

// === Material factory methods ===

UMaterialInstanceDynamic* UGalleryMaterials::CreateTrussMaterial()
{
	return CreateMaterialInstance(TEXT("Truss"), FLinearColor(0.7f, 0.65f, 0.6f), 0.9f, 0.3f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateCeilingMaterial()
{
	return CreateMaterialInstance(TEXT("Ceiling"), FLinearColor(0.3f, 0.3f, 0.3f), 0.0f, 0.8f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateDuctMaterial()
{
	return CreateMaterialInstance(TEXT("Duct"), FLinearColor(0.6f, 0.62f, 0.65f), 0.8f, 0.4f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateWallMaterial()
{
	return CreateMaterialInstance(TEXT("Wall"), FLinearColor(0.55f, 0.55f, 0.53f), 0.0f, 0.7f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateFloorMaterial()
{
	return CreateMaterialInstance(TEXT("Floor"), FLinearColor(0.15f, 0.15f, 0.15f), 0.1f, 0.08f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreatePaintingMaterial()
{
	return CreateMaterialInstance(TEXT("Painting"), FLinearColor(0.9f, 0.9f, 0.9f), 0.0f, 0.6f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateFrameMaterial()
{
	return CreateMaterialInstance(TEXT("Frame"), FLinearColor(0.05f, 0.05f, 0.05f), 0.7f, 0.3f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreatePlaqueMaterial()
{
	return CreateMaterialInstance(TEXT("Plaque"), FLinearColor(0.7f, 0.6f, 0.3f), 0.9f, 0.2f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateSpotMaterial()
{
	return CreateMaterialInstance(TEXT("Spot"), FLinearColor(0.15f, 0.15f, 0.15f), 0.6f, 0.4f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreatePedestalMaterial()
{
	return CreateMaterialInstance(TEXT("Pedestal"), FLinearColor(0.85f, 0.82f, 0.78f), 0.0f, 0.3f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateSculptureBronzeMaterial()
{
	return CreateMaterialInstance(TEXT("SculptureBronze"), FLinearColor(0.72f, 0.45f, 0.2f), 1.0f, 0.3f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateSculptureGoldMaterial()
{
	return CreateMaterialInstance(TEXT("SculptureGold"), FLinearColor(0.83f, 0.68f, 0.21f), 1.0f, 0.2f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateSculptureDarkMaterial()
{
	return CreateMaterialInstance(TEXT("SculptureDark"), FLinearColor(0.6f, 0.5f, 0.4f), 0.9f, 0.3f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateLEDMaterial()
{
	return CreateMaterialInstance(TEXT("LED"), FLinearColor(1.0f, 1.0f, 1.0f), 0.0f, 0.5f,
		FLinearColor(2.0f, 2.0f, 2.0f));
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateBenchMaterial()
{
	return CreateMaterialInstance(TEXT("Bench"), FLinearColor(0.5f, 0.4f, 0.3f), 0.0f, 0.6f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateDoorMaterial()
{
	return CreateMaterialInstance(TEXT("Door"), FLinearColor(0.2f, 0.15f, 0.1f), 0.0f, 0.5f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateSignMaterial()
{
	return CreateMaterialInstance(TEXT("Sign"), FLinearColor(1.0f, 0.1f, 0.1f), 0.0f, 0.5f,
		FLinearColor(1.0f, 0.1f, 0.1f));
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateGlassMaterial()
{
	return CreateMaterialInstance(TEXT("Glass"), FLinearColor(1.0f, 1.0f, 1.0f), 0.0f, 0.5f,
		FLinearColor(1.0f, 1.0f, 1.0f), 1.5f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreatePartitionMaterial()
{
	return CreateMaterialInstance(TEXT("Partition"), FLinearColor(0.8f, 0.85f, 0.9f), 0.0f, 0.2f);
}

UMaterialInstanceDynamic* UGalleryMaterials::CreateFloorGuideMaterial()
{
	return CreateMaterialInstance(TEXT("FloorGuide"), FLinearColor(1.0f, 1.0f, 1.0f), 0.0f, 0.5f,
		FLinearColor(1.0f, 1.0f, 1.0f));
}

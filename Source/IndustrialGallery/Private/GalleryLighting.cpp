// GalleryLighting.cpp
// Implements the gallery lighting system: sky light, spot lights, art lights,
// emissive ceiling strips, accent lights, and post-process volume.

#include "GalleryLighting.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/SpotLight.h"
#include "Engine/PointLight.h"
#include "Engine/SkyLight.h"
#include "Engine/PostProcessVolume.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

DEFINE_LOG_CATEGORY_STATIC(LogGalleryLighting, Log, All);

AGalleryLighting::AGalleryLighting()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AGalleryLighting::BeginPlay()
{
	Super::BeginPlay();
	if (bSetupOnBeginPlay)
	{
		SetupLighting();
	}
}

void AGalleryLighting::SetupLighting()
{
	// 1. Sky light
	AddSkyLight(FVector(100.0f, 50.0f, 700.0f), 0.6f);

	// 2. 30 spot lights in a 5x6 grid on the ceiling (Z=265)
	for (int32 i = 0; i < 5; ++i)
	{
		float X = -400.0f + (700.0f - (-400.0f)) * i / 4.0f;
		for (int32 j = 0; j < 6; ++j)
		{
			float Y = -500.0f + (600.0f - (-500.0f)) * j / 5.0f;
			FVector Location(X, Y, 265.0f);
			FRotator Rotation(0.0f, 0.0f, 0.0f); // Pointing down
			AddSpotLight(Location, Rotation, 15000.0f, 35.0f);
		}
	}

	// 3. 9 art lights on walls at Z=150, pointing at artwork
	// 5 on X=-400 wall (pointing inward, +X direction)
	for (int32 i = 0; i < 5; ++i)
	{
		float Y = -400.0f + 800.0f * i / 4.0f;
		FVector Location(-400.0f, Y, 150.0f);
		FRotator Rotation(0.0f, -90.0f, 0.0f);
		AddSpotLight(Location, Rotation, 8000.0f, 25.0f);
	}
	// 4 on X=600 wall (pointing inward, -X direction)
	for (int32 i = 0; i < 4; ++i)
	{
		float Y = -300.0f + 600.0f * i / 3.0f;
		FVector Location(600.0f, Y, 150.0f);
		FRotator Rotation(0.0f, 90.0f, 0.0f);
		AddSpotLight(Location, Rotation, 8000.0f, 25.0f);
	}

	// 4. Emissive ceiling strips (5 strips at Z=270, each 800cm long, 10cm wide)
	for (int32 i = 0; i < 5; ++i)
	{
		float Y = -400.0f + 800.0f * i / 4.0f;
		FVector Location(100.0f, Y, 270.0f);
		FVector Size(800.0f, 10.0f, 2.0f);
		FLinearColor Color(1.0f, 0.98f, 0.95f);
		AddEmissiveStrip(Location, Size, Color);
	}

	// 5. Accent point lights near sculptures
	AddPointLight(FVector(200.0f, 0.0f, 100.0f), 5000.0f, 400.0f);
	AddPointLight(FVector(670.0f, 430.0f, 100.0f), 4000.0f, 300.0f);

	// 6. Post-process volume
	FActorSpawnParameters SpawnParams;
	// No SpawnParams.Name — let the engine auto-generate unique names.
	APostProcessVolume* PPV = GetWorld()->SpawnActor<APostProcessVolume>(
		APostProcessVolume::StaticClass(),
		FVector(100.0f, 50.0f, 140.0f),
		FRotator::ZeroRotator,
		SpawnParams
	);
	if (PPV)
	{
		PPV->Settings.bOverride_AutoExposureMethod = true;
		PPV->Settings.AutoExposureMethod = AEM_Manual;
		PPV->Settings.bOverride_BloomIntensity = true;
		PPV->Settings.BloomIntensity = 0.35f;
		PPV->Settings.bOverride_ColorContrast = true;
		PPV->Settings.ColorContrast = FVector4(1.1f, 1.1f, 1.1f, 1.0f);
		PPV->Settings.bOverride_ColorSaturation = true;
		PPV->Settings.ColorSaturation = FVector4(1.05f, 1.05f, 1.05f, 1.0f);
		PPV->bUnbound = true;
	}

	UE_LOG(LogGalleryLighting, Log, TEXT("GalleryLighting: Setup complete"));
}

void AGalleryLighting::AddSpotLight(FVector Location, FRotator Rotation, float Intensity, float ConeAngle)
{
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	ASpotLight* SpotLight = GetWorld()->SpawnActor<ASpotLight>(
		ASpotLight::StaticClass(), Location, Rotation, SpawnParams
	);

	if (SpotLight)
	{
		USpotLightComponent* Comp = SpotLight->SpotLightComponent;
		if (Comp)
		{
			Comp->SetMobility(EComponentMobility::Movable);
			Comp->SetIntensity(Intensity);
			Comp->SetLightColor(FLinearColor(1.0f, 0.98f, 0.95f));
			Comp->SetInnerConeAngle(ConeAngle * 0.5f);
			Comp->SetOuterConeAngle(ConeAngle);
			Comp->SetCastShadows(true);
		}
	}
}

void AGalleryLighting::AddPointLight(FVector Location, float Intensity, float Radius)
{
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	APointLight* PointLight = GetWorld()->SpawnActor<APointLight>(
		APointLight::StaticClass(), Location, FRotator::ZeroRotator, SpawnParams
	);

	if (PointLight)
	{
		UPointLightComponent* Comp = PointLight->PointLightComponent;
		if (Comp)
		{
			Comp->SetMobility(EComponentMobility::Movable);
			Comp->SetIntensity(Intensity);
			Comp->SetAttenuationRadius(Radius);
			Comp->SetLightColor(FLinearColor(1.0f, 0.95f, 0.87f));
		}
	}
}

void AGalleryLighting::AddSkyLight(FVector Location, float Intensity)
{
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	ASkyLight* SkyLight = GetWorld()->SpawnActor<ASkyLight>(
		ASkyLight::StaticClass(), Location, FRotator::ZeroRotator, SpawnParams
	);

	if (SkyLight)
	{
		USkyLightComponent* Comp = SkyLight->GetLightComponent();
		if (Comp)
		{
			Comp->SetMobility(EComponentMobility::Movable);
			Comp->SetIntensity(Intensity);
			Comp->SetLightColor(FLinearColor(1.0f, 0.95f, 0.87f));
		}
	}
}

void AGalleryLighting::AddEmissiveStrip(FVector Location, FVector Size, FLinearColor Color)
{
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AStaticMeshActor* Strip = GetWorld()->SpawnActor<AStaticMeshActor>(
		AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator, SpawnParams
	);

	if (Strip)
	{
		UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		if (CubeMesh)
		{
			Strip->GetStaticMeshComponent()->SetStaticMesh(CubeMesh);
		}

		Strip->SetActorScale3D(Size / 100.0f);

		UMaterial* DefaultMat = UMaterial::GetDefaultMaterial(MD_Surface);
		if (DefaultMat)
		{
			UMaterialInstanceDynamic* DynMat = UMaterialInstanceDynamic::Create(DefaultMat, Strip);
			if (DynMat)
			{
				DynMat->SetVectorParameterValue(TEXT("EmissiveColor"), Color * 2.5f);
				Strip->GetStaticMeshComponent()->SetMaterial(0, DynMat);
			}
		}

		Strip->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
	}
}

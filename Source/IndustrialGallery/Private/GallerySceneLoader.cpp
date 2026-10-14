// GallerySceneLoader.cpp
// Reads all_objects_ue.json and spawns all 746 objects at their exact positions.

#include "GallerySceneLoader.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/Package.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonReader.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManagerGeneric.h"
#include "EngineUtils.h"
#include "Logging/LogMacros.h"

DEFINE_LOG_CATEGORY_STATIC(LogGallery, Log, All);

AGallerySceneLoader::AGallerySceneLoader()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AGallerySceneLoader::BeginPlay()
{
	Super::BeginPlay();
	if (bAutoLoadOnBeginPlay)
	{
		LoadScene();
	}
}

void AGallerySceneLoader::LoadScene()
{
	// Clear any previously spawned actors
	ClearScene();

	// Resolve the JSON file path
	FString ResolvedPath = JsonFilePath;
	if (ResolvedPath.StartsWith(TEXT("/Game/")))
	{
		ResolvedPath = FPaths::ProjectContentDir() + ResolvedPath.RightChop(6);
	}
	if (!FPaths::FileExists(ResolvedPath))
	{
		// Try relative to project dir
		FString AltPath = FPaths::ProjectDir() + JsonFilePath;
		if (FPaths::FileExists(AltPath))
		{
			ResolvedPath = AltPath;
		}
	}

	if (!FPaths::FileExists(ResolvedPath))
	{
		UE_LOG(LogGallery, Error, TEXT("JSON file not found: %s (resolved: %s)"),
			*JsonFilePath, *ResolvedPath);
		return;
	}

	// Read the file
	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *ResolvedPath))
	{
		UE_LOG(LogGallery, Error, TEXT("Failed to read JSON file: %s"), *ResolvedPath);
		return;
	}

	// Parse JSON - the root is an array of objects
	TArray<TSharedPtr<FJsonValue>> RootArray;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, RootArray))
	{
		UE_LOG(LogGallery, Error, TEXT("Failed to parse JSON file: %s"), *ResolvedPath);
		return;
	}
	UE_LOG(LogGallery, Log, TEXT("GallerySceneLoader: Loaded %d objects from JSON"), RootArray.Num());

	int32 Spawned = 0;
	int32 Skipped = 0;
	for (const TSharedPtr<FJsonValue>& Value : RootArray)
	{
		const TSharedPtr<FJsonObject>* ObjPtr;
		if (!Value->TryGetObject(ObjPtr) || !ObjPtr->IsValid())
		{
			Skipped++;
			continue;
		}

		const TSharedPtr<FJsonObject>& Obj = *ObjPtr;

		FString Name;
		if (!Obj->TryGetStringField(TEXT("name"), Name))
		{
			Skipped++;
			continue;
		}

		// Get UE position
		const TArray<TSharedPtr<FJsonValue>>* PosArray;
		if (!Obj->TryGetArrayField(TEXT("ue_position"), PosArray) || PosArray->Num() < 3)
		{
			UE_LOG(LogGallery, Warning, TEXT("Object '%s' missing ue_position, skipping"), *Name);
			Skipped++;
			continue;
		}

		float X = (*PosArray)[0]->AsNumber();
		float Y = (*PosArray)[1]->AsNumber();
		float Z = (*PosArray)[2]->AsNumber();

		float Yaw = 0.0f;
		Obj->TryGetNumberField(TEXT("ue_yaw"), Yaw);

		FVector Position(X, Y, Z);

		FString Category = GetCategoryFromName(Name);
		AActor* SpawnedActor = SpawnObject(Name, Category, Position, Yaw);
		if (SpawnedActor)
		{
			SpawnedActors.Add(SpawnedActor);
			Spawned++;
		}

		// Log progress every 50 objects
		if (Spawned % 50 == 0 && Spawned > 0)
		{
			UE_LOG(LogGallery, Log, TEXT("GallerySceneLoader: Spawned %d / %d objects..."), Spawned, RootArray.Num());
		}
	}

	UE_LOG(LogGallery, Log, TEXT("GallerySceneLoader: Spawned %d / %d objects total (skipped %d)"),
		Spawned, RootArray.Num(), Skipped);

	// 7. Spawn floor plane covering the entire gallery room
	{
		FActorSpawnParameters SpawnParams;
		// No SpawnParams.Name — let the engine auto-generate unique names.
		AStaticMeshActor* FloorActor = GetWorld()->SpawnActor<AStaticMeshActor>(
			AStaticMeshActor::StaticClass(),
			FVector(100.0f, 50.0f, -5.0f),
			FRotator::ZeroRotator,
			SpawnParams
		);
		if (FloorActor)
		{
			UStaticMeshComponent* FloorComp = FloorActor->GetStaticMeshComponent();
			UStaticMesh* FloorMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
			if (FloorMesh)
			{
				FloorComp->SetStaticMesh(FloorMesh);
			}
			FloorActor->SetActorScale3D(FVector(1400.0f, 1400.0f, 10.0f));

			// Dark polished concrete material
			UMaterialInstanceDynamic* FloorMat = CreateMaterialInstance(
				TEXT("Floor"), 0.15f, 0.15f, 0.15f, 0.1f, 0.08f, 0.0f);
			if (FloorMat)
			{
				FloorComp->SetMaterial(0, FloorMat);
			}

			FloorComp->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
			FloorComp->SetCollisionObjectType(ECC_WorldStatic);
			FloorComp->SetCollisionResponseToAllChannels(ECR_Block);

			SpawnedActors.Add(FloorActor);
			UE_LOG(LogGallery, Log, TEXT("GallerySceneLoader: Floor spawned"));
		}
	}
}

void AGallerySceneLoader::ClearScene()
{
	int32 Count = SpawnedActors.Num();
	for (TObjectPtr<AActor>& Actor : SpawnedActors)
	{
		if (Actor != nullptr)
		{
			Actor->Destroy();
		}
	}
	SpawnedActors.Empty();
	UE_LOG(LogGallery, Warning, TEXT("GallerySceneLoader: Cleared %d actors"), Count);
}

FString AGallerySceneLoader::GetCategoryFromName(const FString& ObjectName) const
{
	// Order matters: check more specific patterns first
	if (ObjectName.StartsWith(TEXT("Truss"))) return TEXT("Truss");
	if (ObjectName.StartsWith(TEXT("Ceiling"))) return TEXT("Ceiling");
	if (ObjectName.StartsWith(TEXT("Duct"))) return TEXT("Duct");
	if (ObjectName.StartsWith(TEXT("Wall"))) return TEXT("Wall");
	if (ObjectName.StartsWith(TEXT("Painting"))) return TEXT("Painting");
	if (ObjectName.StartsWith(TEXT("Frame"))) return TEXT("Frame");
	if (ObjectName.StartsWith(TEXT("Plaque"))) return TEXT("Plaque");
	if (ObjectName.StartsWith(TEXT("Spot")) || ObjectName.StartsWith(TEXT("Art Light"))) return TEXT("Spot");
	if (ObjectName.StartsWith(TEXT("Pedestal")) ||
		ObjectName.StartsWith(TEXT("Marble Pedestal")) ||
		ObjectName.StartsWith(TEXT("Small Pedestal")) ||
		ObjectName.StartsWith(TEXT("White Pedestal"))) return TEXT("Pedestal");
	if (ObjectName.StartsWith(TEXT("Sculpture"))) return TEXT("Sculpture");
	if (ObjectName.StartsWith(TEXT("LED"))) return TEXT("LED");
	if (ObjectName.StartsWith(TEXT("Bench"))) return TEXT("Bench");
	if (ObjectName.StartsWith(TEXT("Door"))) return TEXT("Door");
	if (ObjectName.StartsWith(TEXT("Round Sign"))) return TEXT("RoundSign");
	if (ObjectName.StartsWith(TEXT("Back Sphere"))) return TEXT("BackSphere");
	if (ObjectName.StartsWith(TEXT("Back"))) return TEXT("Back");
	if (ObjectName.StartsWith(TEXT("Halo"))) return TEXT("Halo");
	if (ObjectName.StartsWith(TEXT("Rail"))) return TEXT("Rail");
	if (ObjectName.StartsWith(TEXT("Floor Guide"))) return TEXT("FloorGuide");
	if (ObjectName.StartsWith(TEXT("Curved Partition"))) return TEXT("CurvedPartition");
	if (ObjectName.StartsWith(TEXT("Partition"))) return TEXT("Partition");
	// Fallback for unknown objects (color, layer2, CubeGeometry, Marble, Small, White)
	return TEXT("Default");
}

UStaticMesh* AGallerySceneLoader::GetMeshForCategory(const FString& Category) const
{
	if (Category == TEXT("Duct") || Category == TEXT("RoundSign") ||
		Category == TEXT("Spot") || Category == TEXT("Sculpture"))
	{
		return LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	}
	if (Category == TEXT("LED") || Category == TEXT("Halo"))
	{
		return LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	}
	return LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
}

UMaterialInstanceDynamic* AGallerySceneLoader::CreateMaterialInstance(
	const FString& Category,
	float R, float G, float B,
	float Metallic, float Roughness,
	float Emissive)
{
	UMaterialInstanceDynamic* DynMat = nullptr;
	UMaterial* MasterMat = LoadObject<UMaterial>(nullptr, TEXT("/Game/Gallery/Materials/M_GallerySurface.M_GallerySurface"));
	if (MasterMat)
	{
		DynMat = UMaterialInstanceDynamic::Create(MasterMat, this);
	}
	else
	{
		UMaterial* DefaultMat = LoadObject<UMaterial>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
		if (DefaultMat)
		{
			DynMat = UMaterialInstanceDynamic::Create(DefaultMat, this);
		}
	}
	if (DynMat)
	{
		DynMat->SetVectorParameterValue(TEXT("BaseColor"), FLinearColor(R, G, B, 1.0f));
		DynMat->SetScalarParameterValue(TEXT("Metallic"), Metallic);
		DynMat->SetScalarParameterValue(TEXT("Roughness"), Roughness);
		DynMat->SetScalarParameterValue(TEXT("EmissiveColor"), Emissive);
	}
	return DynMat;
}

void AGallerySceneLoader::SetCollisionForCategory(UStaticMeshComponent* MeshComp, const FString& Category) const
{
	// Large structural objects get full collision
	if (Category == TEXT("Wall") || Category == TEXT("Ceiling") ||
		Category == TEXT("Partition") || Category == TEXT("CurvedPartition") ||
		Category == TEXT("Door") || Category == TEXT("Bench") ||
		Category == TEXT("Pedestal") || Category == TEXT("Truss"))
	{
		MeshComp->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		MeshComp->SetCollisionObjectType(ECC_WorldStatic);
		MeshComp->SetCollisionResponseToAllChannels(ECR_Block);
	}
	// Small decorative objects: no collision (paintings, frames, plaques, LEDs, halos, etc.)
	else
	{
		MeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	}
}

void AGallerySceneLoader::SetScaleForCategory(AActor* Actor, const FString& Category) const
{
	FVector Scale(1.0f, 1.0f, 1.0f);

	if (Category == TEXT("Wall"))
	{
		Scale = FVector(10.0f, 10.0f, 0.5f);
	}
	else if (Category == TEXT("Ceiling"))
	{
		Scale = FVector(10.0f, 10.0f, 0.5f);
	}
	else if (Category == TEXT("FloorGuide"))
	{
		Scale = FVector(5.0f, 0.2f, 0.1f);
	}
	else if (Category == TEXT("Painting"))
	{
		Scale = FVector(2.0f, 0.1f, 2.0f);
	}
	else if (Category == TEXT("Frame"))
	{
		Scale = FVector(2.2f, 0.05f, 2.2f);
	}
	else if (Category == TEXT("Plaque"))
	{
		Scale = FVector(0.5f, 0.05f, 0.3f);
	}
	else if (Category == TEXT("Truss"))
	{
		Scale = FVector(0.3f, 0.3f, 5.0f);
	}
	else if (Category == TEXT("Duct"))
	{
		Scale = FVector(1.0f, 1.0f, 5.0f);
	}
	else if (Category == TEXT("Partition") || Category == TEXT("CurvedPartition"))
	{
		Scale = FVector(8.0f, 0.5f, 8.0f);
	}
	else if (Category == TEXT("LED") || Category == TEXT("Halo"))
	{
		Scale = FVector(0.2f, 0.2f, 0.2f);
	}

	Actor->SetActorScale3D(Scale);
}

AActor* AGallerySceneLoader::SpawnObject(const FString& Name, const FString& Category,
	const FVector& Position, float Yaw)
{
	// Spawn an AStaticMeshActor
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	// Do NOT set SpawnParams.Name — let the engine auto-generate unique names.
	// Setting it manually causes fatal "Cannot generate unique name" on re-spawn.

	AStaticMeshActor* Actor = GetWorld()->SpawnActor<AStaticMeshActor>(
		AStaticMeshActor::StaticClass(), Position, FRotator(0.0f, Yaw, 0.0f), SpawnParams);
	if (!Actor)
	{
		UE_LOG(LogGallery, Warning, TEXT("Failed to spawn actor for '%s'"), *Name);
		return nullptr;
	}

	UStaticMeshComponent* MeshComp = Actor->GetStaticMeshComponent();
	if (!MeshComp)
	{
		UE_LOG(LogGallery, Warning, TEXT("No mesh component for '%s'"), *Name);
		Actor->Destroy();
		return nullptr;
	}

	// Set the appropriate mesh for this category
	UStaticMesh* Mesh = GetMeshForCategory(Category);
	if (Mesh)
	{
		MeshComp->SetStaticMesh(Mesh);
	}

	// Determine material color based on category
	float R = 0.5f, G = 0.5f, B = 0.5f;
	float Metallic = 0.0f, Roughness = 0.5f, Emissive = 0.0f;

	if (Category == TEXT("Truss"))
	{
		R = 0.7f; G = 0.65f; B = 0.6f; Metallic = 0.9f; Roughness = 0.3f;
	}
	else if (Category == TEXT("Ceiling"))
	{
		R = 0.3f; G = 0.3f; B = 0.3f; Metallic = 0.0f; Roughness = 0.8f;
	}
	else if (Category == TEXT("Duct"))
	{
		R = 0.6f; G = 0.62f; B = 0.65f; Metallic = 0.8f; Roughness = 0.4f;
	}
	else if (Category == TEXT("Wall"))
	{
		R = 0.55f; G = 0.55f; B = 0.53f; Metallic = 0.0f; Roughness = 0.7f;
	}
	else if (Category == TEXT("Painting"))
	{
		R = 0.9f; G = 0.9f; B = 0.9f; Metallic = 0.0f; Roughness = 0.6f;
	}
	else if (Category == TEXT("Frame"))
	{
		R = 0.05f; G = 0.05f; B = 0.05f; Metallic = 0.7f; Roughness = 0.3f;
	}
	else if (Category == TEXT("Plaque"))
	{
		R = 0.7f; G = 0.6f; B = 0.3f; Metallic = 0.9f; Roughness = 0.2f;
	}
	else if (Category == TEXT("Spot"))
	{
		R = 0.15f; G = 0.15f; B = 0.15f; Metallic = 0.6f; Roughness = 0.4f;
	}
	else if (Category == TEXT("Pedestal"))
	{
		R = 0.85f; G = 0.82f; B = 0.78f; Metallic = 0.0f; Roughness = 0.3f;
	}
	else if (Category == TEXT("Sculpture"))
	{
		if (Name.Contains(TEXT("Gold")))
		{
			R = 0.83f; G = 0.68f; B = 0.21f; Metallic = 1.0f; Roughness = 0.2f;
		}
		else if (Name.Contains(TEXT("Bronze")))
		{
			R = 0.72f; G = 0.45f; B = 0.2f; Metallic = 1.0f; Roughness = 0.3f;
		}
		else
		{
			R = 0.6f; G = 0.5f; B = 0.4f; Metallic = 0.9f; Roughness = 0.3f;
		}
	}
	else if (Category == TEXT("LED"))
	{
		R = 1.0f; G = 1.0f; B = 1.0f; Metallic = 0.0f; Roughness = 0.5f; Emissive = 2.0f;
	}
	else if (Category == TEXT("Bench"))
	{
		R = 0.5f; G = 0.4f; B = 0.3f; Metallic = 0.0f; Roughness = 0.6f;
	}
	else if (Category == TEXT("Door"))
	{
		R = 0.2f; G = 0.15f; B = 0.1f; Metallic = 0.0f; Roughness = 0.5f;
	}
	else if (Category == TEXT("RoundSign"))
	{
		R = 1.0f; G = 0.1f; B = 0.1f; Metallic = 0.0f; Roughness = 0.5f; Emissive = 1.0f;
	}
	else if (Category == TEXT("Back"))
	{
		R = 0.15f; G = 0.15f; B = 0.15f; Metallic = 0.6f; Roughness = 0.4f;
	}
	else if (Category == TEXT("BackSphere"))
	{
		R = 0.9f; G = 0.9f; B = 0.88f; Metallic = 0.0f; Roughness = 0.5f;
	}
	else if (Category == TEXT("Halo"))
	{
		R = 1.0f; G = 1.0f; B = 1.0f; Metallic = 0.0f; Roughness = 0.5f; Emissive = 1.5f;
	}
	else if (Category == TEXT("Rail"))
	{
		R = 0.6f; G = 0.6f; B = 0.6f; Metallic = 0.8f; Roughness = 0.3f;
	}
	else if (Category == TEXT("FloorGuide"))
	{
		R = 1.0f; G = 1.0f; B = 1.0f; Metallic = 0.0f; Roughness = 0.5f; Emissive = 1.0f;
	}
	else if (Category == TEXT("CurvedPartition"))
	{
		R = 0.95f; G = 0.95f; B = 0.93f; Metallic = 0.0f; Roughness = 0.6f;
	}
	else if (Category == TEXT("Partition"))
	{
		R = 0.8f; G = 0.85f; B = 0.9f; Metallic = 0.0f; Roughness = 0.2f;
	}
	// Default category gets a neutral gray

	UMaterialInstanceDynamic* DynMat = CreateMaterialInstance(Category, R, G, B, Metallic, Roughness, Emissive);
	if (DynMat)
	{
		MeshComp->SetMaterial(0, DynMat);
	}

	// Set collision based on category
	SetCollisionForCategory(MeshComp, Category);

	// Set scale based on category
	SetScaleForCategory(Actor, Category);

	return Actor;
}

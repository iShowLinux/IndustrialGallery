// GallerySceneLoader.h
// Reads all_objects_ue.json and spawns all 746 objects at their exact positions.

#pragma once

#include "CoreMinimal.h"
#include "Logging/LogMacros.h"
#include "GameFramework/Actor.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManagerGeneric.h"
#include "UObject/Package.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "GallerySceneLoader.generated.h"

UCLASS()
class INDUSTRIALGALLERY_API AGallerySceneLoader : public AActor
{
	GENERATED_BODY()

public:
	AGallerySceneLoader();

	/** Read the JSON file and spawn all objects. */
	UFUNCTION(BlueprintCallable, Category = "Gallery")
	void LoadScene();

	/** Destroy all spawned actors. */
	UFUNCTION(BlueprintCallable, Category = "Gallery")
	void ClearScene();

	/** Path to the JSON file (UE path, e.g. /Game/Assets/all_objects_ue.json). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gallery")
	FString JsonFilePath = TEXT("/Game/Assets/all_objects_ue.json");

	/** Whether to auto-load the scene on BeginPlay. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gallery")
	bool bAutoLoadOnBeginPlay = true;

	/** All actors spawned by LoadScene(). */
	UPROPERTY(BlueprintReadOnly, Category = "Gallery")
	TArray<TObjectPtr<AActor>> SpawnedActors;

protected:
	virtual void BeginPlay() override;

private:
	/** Determine the category string from an object name. */
	FString GetCategoryFromName(const FString& ObjectName) const;

	/** Pick the appropriate engine basic-shape mesh for a category. */
	UStaticMesh* GetMeshForCategory(const FString& Category) const;

	/** Create a UMaterialInstanceDynamic with the given color parameters. */
	UMaterialInstanceDynamic* CreateMaterialInstance(
		const FString& Category,
		float R, float G, float B,
		float Metallic, float Roughness,
		float Emissive = 0.0f);

	/** Configure collision for a spawned mesh component based on category. */
	void SetCollisionForCategory(UStaticMeshComponent* MeshComp, const FString& Category) const;

	/** Set the world scale for a spawned actor based on category. */
	void SetScaleForCategory(AActor* Actor, const FString& Category) const;

	/** Spawn a single static mesh actor at the given position/yaw. */
	AActor* SpawnObject(const FString& Name, const FString& Category,
		const FVector& Position, float Yaw);
};

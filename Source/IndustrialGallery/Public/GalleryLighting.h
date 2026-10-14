#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/SpotLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "GalleryLighting.generated.h"

UCLASS()
class INDUSTRIALGALLERY_API AGalleryLighting : public AActor
{
	GENERATED_BODY()

public:
	AGalleryLighting();

	UPROPERTY(EditAnywhere)
	bool bSetupOnBeginPlay = true;

	UFUNCTION(BlueprintCallable, Category = "Lighting")
	void SetupLighting();

	UFUNCTION(BlueprintCallable, Category = "Lighting")
	void AddSpotLight(FVector Location, FRotator Rotation, float Intensity, float ConeAngle);

	UFUNCTION(BlueprintCallable, Category = "Lighting")
	void AddPointLight(FVector Location, float Intensity, float Radius);

	UFUNCTION(BlueprintCallable, Category = "Lighting")
	void AddSkyLight(FVector Location, float Intensity);

	UFUNCTION(BlueprintCallable, Category = "Lighting")
	void AddEmissiveStrip(FVector Location, FVector Size, FLinearColor Color);

protected:
	virtual void BeginPlay() override;
};

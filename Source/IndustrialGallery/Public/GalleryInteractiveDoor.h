#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GalleryInteractiveDoor.generated.h"

class USceneComponent;
class UStaticMeshComponent;

/** Hinged door: origin is left hinge at floor, local +X across leaf, +Y into room. */
UCLASS(Blueprintable)
class INDUSTRIALGALLERY_API AGalleryInteractiveDoor : public AActor
{
    GENERATED_BODY()
public:
    AGalleryInteractiveDoor();
    virtual void Tick(float DeltaSeconds) override;
    virtual void OnConstruction(const FTransform& Transform) override;

    UFUNCTION(BlueprintCallable, Category="Gallery|Door")
    bool Interact(AActor* Interactor);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Gallery|Door")
    TObjectPtr<USceneComponent> Hinge;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Gallery|Door")
    TObjectPtr<UStaticMeshComponent> Leaf;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Gallery|Door")
    TObjectPtr<UStaticMeshComponent> Handle;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery|Door", meta=(ClampMin="80", ClampMax="200"))
    float Width = 160.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery|Door", meta=(ClampMin="200", ClampMax="300"))
    float Height = 240.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery|Door")
    float OpenAngle = 95.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery|Door")
    float InteractionDistance = 280.f;
    UPROPERTY(BlueprintReadOnly, Category="Gallery|Door")
    bool bIsOpen = false;

private:
    bool IsSwingAreaOccupied() const;
    float CurrentAngle = 0.f;
};

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GalleryVisitor.generated.h"

class UCameraComponent;
class UAudioComponent;
class USoundBase;
class ULightComponent;

/** Collision-driven first-person visitor. Blueprint subclasses can extend interactions. */
UCLASS(Blueprintable)
class INDUSTRIALGALLERY_API AGalleryVisitor : public ACharacter
{
    GENERATED_BODY()
public:
    AGalleryVisitor();
    virtual void BeginPlay() override;
    virtual void PossessedBy(AController* NewController) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Gallery")
    void Interact();
    UFUNCTION(BlueprintCallable, Category="Gallery")
    void ToggleLightingMode();
    UFUNCTION(BlueprintCallable, Category="Gallery")
    void SetShowcaseLighting(bool bShowcase);

    /** Degrees per second for arrow-key look. Mouse look is a per-frame delta and
     *  is not scaled by this. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery|Input")
    float ArrowLookRate = 150.f;

    /** Degrees per mouse input unit. Never multiplied by frame time. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery|Input", meta=(ClampMin="0"))
    float MouseLookSensitivity = 0.15f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Gallery")
    TObjectPtr<UCameraComponent> Camera;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Gallery")
    TObjectPtr<UAudioComponent> AmbientAudio;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Gallery")
    TObjectPtr<USoundBase> AmbientSound;
    UPROPERTY(BlueprintReadOnly, Category="Gallery")
    bool bShowcaseLighting = false;

private:
    void LookYaw(float Value);
    void LookPitch(float Value);
    void ApplyLookDelta(float YawDegrees, float PitchDegrees);
    TMap<TWeakObjectPtr<ULightComponent>, float> OriginalLightIntensities;
};

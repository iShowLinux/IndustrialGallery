#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GalleryGameMode.generated.h"

class ACameraActor;

/** Reference map walks; legacy maps retain their fixed overview camera. */
UCLASS()
class INDUSTRIALGALLERY_API AGalleryGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AGalleryGameMode();

	virtual void InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Camera spawn position - overlooking the gallery from the south side */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
	FVector CameraLocation = FVector(100.0f, -500.0f, 300.0f);

	/** Point the camera looks at - center of the gallery */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Camera")
	FVector CameraLookAtLocation = FVector(100.0f, 50.0f, 100.0f);

private:
    void SetReferenceShot(int32 Index);
    void RunReferenceProbe();
    /** Exercise the real input path: inject key/axis events and check the
     *  resulting movement and look. Reports PASS/FAIL per check. */
    void RunInputProbe();
    bool bReferenceMap = false;
    bool bReferenceShots = false;
    bool bReferenceProbe = false;
    bool bProbeComplete = false;
    bool bReferenceProbePassed = false;
    bool bInputProbeComplete = false;
    bool bInputProbePassed = true;
    bool bWaitingForScreenshot = false;
    int32 ShotIndex = -1;
    int32 InputProbeStage = 0;
    int32 InputProbeCase = 0;
    int32 InputProbePassedCases = 0;
    bool bInputProbeActionBefore = false;
    float InputProbeLightBefore = 0.f;
    double StageStartedAt = 0.0;
    double PlayStartedAt = 0.0;
    double ProbeStartedAt = 0.0;
    double InputProbeStageAt = 0.0;
    FVector InputProbeStartLocation = FVector::ZeroVector;
    FRotator InputProbeStartRotation = FRotator::ZeroRotator;
    FString PendingScreenshot;
    UPROPERTY()
    TObjectPtr<ACameraActor> CaptureCamera;
};

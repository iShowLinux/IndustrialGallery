#include "GalleryGameMode.h"
#include "GalleryVisitor.h"
#include "GalleryInteractiveDoor.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/LightComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "InputKeyEventArgs.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

namespace ReferenceGallery
{
    static const FVector ShotLocations[] = {
        FVector(-580.f, -780.f, 310.f),
        FVector(-450.f, -680.f, 170.f),
        FVector(100.f, -330.f, 175.f),
        // Steep plan view. A 18.4 m room cannot be covered from below its own
        // ceiling (a 4 m camera height caps coverage at ~9.8 m), so this frames
        // the front two-thirds where the focal content actually is.
        FVector(0.f, -200.f, 405.f),
        // Artwork views, at the same stand-off and FOV that framed the pieces
        // correctly before the arc experiment.
        FVector(-445.f, 90.f, 183.f),
        FVector(-445.f, 600.f, 177.f)
    };
    static const FVector ShotTargets[] = {
        FVector(80.f, 180.f, 170.f),
        FVector(-250.f, 350.f, 170.f),
        FVector(220.f, -120.f, 140.f),
        FVector(0.f, -201.f, 0.f),
        FVector(-688.f, 90.f, 183.f),
        FVector(-688.f, 600.f, 177.f)
    };
    static const float ShotFieldOfView[] = { 70.f, 70.f, 55.f, 130.f, 60.f, 60.f };
    static const TCHAR* ShotNames[] = {
        TEXT("Reference_01_Hero.png"), TEXT("Reference_02_Walkthrough.png"),
        TEXT("Reference_03_Sculpture.png"), TEXT("Reference_04_Plan.png"),
        TEXT("Reference_05_Artwork.png"), TEXT("Reference_06_ArtworkB.png")
    };
    static const int32 ShotCount = UE_ARRAY_COUNT(ShotNames);

    enum class EInputCheck : uint8 { Forward, Strafe, Yaw, Pitch, MouseYaw, MousePitch, Door, Lighting };
    struct FInputCase
    {
        const TCHAR* Name;
        FKey Key;
        EInputCheck Check;
        float Sign;
        float Duration;
    };
    static const FInputCase InputCases[] = {
        { TEXT("W"), EKeys::W, EInputCheck::Forward, 1.f, 0.8f },
        { TEXT("A"), EKeys::A, EInputCheck::Strafe, -1.f, 0.8f },
        { TEXT("S"), EKeys::S, EInputCheck::Forward, -1.f, 0.8f },
        { TEXT("D"), EKeys::D, EInputCheck::Strafe, 1.f, 0.8f },
        { TEXT("Left"), EKeys::Left, EInputCheck::Yaw, -1.f, 0.25f },
        { TEXT("Right"), EKeys::Right, EInputCheck::Yaw, 1.f, 0.25f },
        { TEXT("Up"), EKeys::Up, EInputCheck::Pitch, 1.f, 0.25f },
        { TEXT("Down"), EKeys::Down, EInputCheck::Pitch, -1.f, 0.25f },
        { TEXT("MouseX+"), EKeys::MouseX, EInputCheck::MouseYaw, 1.f, 0.15f },
        { TEXT("MouseX-"), EKeys::MouseX, EInputCheck::MouseYaw, -1.f, 0.15f },
        { TEXT("MouseY+"), EKeys::MouseY, EInputCheck::MousePitch, 1.f, 0.15f },
        { TEXT("MouseY-"), EKeys::MouseY, EInputCheck::MousePitch, -1.f, 0.15f },
        { TEXT("E-open"), EKeys::E, EInputCheck::Door, 1.f, 0.25f },
        { TEXT("E-close"), EKeys::E, EInputCheck::Door, -1.f, 0.25f },
        { TEXT("L-showcase"), EKeys::L, EInputCheck::Lighting, 1.f, 0.25f },
        { TEXT("L-normal"), EKeys::L, EInputCheck::Lighting, -1.f, 0.25f }
    };

    static void InjectKey(APlayerController* PC, const FKey& Key, EInputEvent Event, float Value)
    {
        FInputKeyEventArgs Args = FInputKeyEventArgs::CreateSimulated(Key, Event, Value, 1);
        Args.DeltaTime = PC->GetWorld()->GetDeltaSeconds();
        PC->InputKey(Args);
    }
}

AGalleryGameMode::AGalleryGameMode()
{
    DefaultPawnClass = nullptr;
    PrimaryActorTick.bCanEverTick = true;
}

void AGalleryGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    // EndsWith also accepts Unreal's UEDPIE_0_ map-name prefix.
    bReferenceMap = FPackageName::GetShortName(MapName).EndsWith(TEXT("L_ReferenceGallery"));
    DefaultPawnClass = bReferenceMap ? AGalleryVisitor::StaticClass() : nullptr;
    Super::InitGame(MapName, Options, ErrorMessage);
    UE_LOG(LogTemp, Log, TEXT("GalleryGameMode: map=%s reference=%d walking_pawn=%s"),
        *MapName, bReferenceMap, *GetNameSafe(DefaultPawnClass.Get()));
}

void AGalleryGameMode::BeginPlay()
{
    Super::BeginPlay();
    PlayStartedAt = FPlatformTime::Seconds();
    ProbeStartedAt = GetWorld()->GetTimeSeconds();
    if (bReferenceMap)
    {
        bReferenceShots = FParse::Param(FCommandLine::Get(), TEXT("ReferenceShots"));
        bReferenceProbe = FParse::Param(FCommandLine::Get(), TEXT("ReferenceProbe"));
        if (bReferenceShots && GEngine) GEngine->Exec(GetWorld(), TEXT("DisableAllScreenMessages"));
        UE_LOG(LogTemp, Log, TEXT("ReferenceGallery: saved-world mode (no runtime loader), shots=%d probe=%d"),
            bReferenceShots, bReferenceProbe);
        return;
    }
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ACameraActor* CameraActor = GetWorld()->SpawnActor<ACameraActor>(
        ACameraActor::StaticClass(), CameraLocation, (CameraLookAtLocation - CameraLocation).Rotation(), Params);
    if (CameraActor)
    {
        if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
            PC->SetViewTargetWithBlend(CameraActor, 0.f);
        UE_LOG(LogTemp, Log, TEXT("GalleryGameMode: legacy overview camera at %s"), *CameraLocation.ToString());
    }
}

void AGalleryGameMode::SetReferenceShot(int32 Index)
{
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC || !CaptureCamera) return;
    const FVector Location = ReferenceGallery::ShotLocations[Index];
    const FRotator Rotation = (ReferenceGallery::ShotTargets[Index] - Location).Rotation();
    CaptureCamera->SetActorLocationAndRotation(Location, Rotation);
    CaptureCamera->GetCameraComponent()->SetFieldOfView(ReferenceGallery::ShotFieldOfView[Index]);
    PC->SetViewTarget(CaptureCamera);
    ShotIndex = Index;
    StageStartedAt = FPlatformTime::Seconds();
    bWaitingForScreenshot = false;
    UE_LOG(LogTemp, Log, TEXT("ReferenceShots: warmup 15s shot=%d eye=%s target=%s"),
        Index + 1, *Location.ToString(), *ReferenceGallery::ShotTargets[Index].ToString());
}

void AGalleryGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bReferenceMap) return;
    const double Now = FPlatformTime::Seconds();
    if (bReferenceProbe && !bProbeComplete && GetWorld()->GetTimeSeconds() - ProbeStartedAt >= 4.0) RunReferenceProbe();
    if (bReferenceProbe && bProbeComplete && !bInputProbeComplete)
    {
        RunInputProbe();
        return;
    }
    if (!bReferenceShots) return;
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (!PC || !PC->GetPawn())
    {
        if (Now - PlayStartedAt > 30.0)
        {
            UE_LOG(LogTemp, Error, TEXT("ReferenceShots: no possessed visitor after 30 seconds"));
            FPlatformMisc::RequestExitWithStatus(false, 1);
        }
        return;
    }
    if (ShotIndex < 0)
    {
        FActorSpawnParameters Params;
        Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        CaptureCamera = GetWorld()->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator, Params);
        if (!CaptureCamera)
        {
            UE_LOG(LogTemp, Error, TEXT("ReferenceShots: capture camera spawn failed"));
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        PC->SetIgnoreMoveInput(true);
        PC->SetIgnoreLookInput(true);
        SetReferenceShot(0);
        return;
    }
    if (!bWaitingForScreenshot && Now - StageStartedAt >= 15.0)
    {
        const FString Folder = FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots/WindowsEditor")));
        IFileManager::Get().MakeDirectory(*Folder, true);
        PendingScreenshot = FPaths::Combine(Folder, ReferenceGallery::ShotNames[ShotIndex]);
        if (IFileManager::Get().FileExists(*PendingScreenshot)
            && !IFileManager::Get().Delete(*PendingScreenshot, false, true))
        {
            UE_LOG(LogTemp, Error, TEXT("ReferenceShots: cannot remove stale screenshot %s"), *PendingScreenshot);
            FPlatformMisc::RequestExitWithStatus(false, 1);
            return;
        }
        FScreenshotRequest::RequestScreenshot(PendingScreenshot, false, false);
        bWaitingForScreenshot = true;
        StageStartedAt = Now;
        UE_LOG(LogTemp, Log, TEXT("ReferenceShots: request %s"), *PendingScreenshot);
    }
    else if (bWaitingForScreenshot && Now - StageStartedAt >= 2.0)
    {
        const int64 Size = IFileManager::Get().FileSize(*PendingScreenshot);
        if (!FScreenshotRequest::IsScreenshotRequested() && Size > 0)
        {
            UE_LOG(LogTemp, Log, TEXT("ReferenceShots: saved %s bytes=%lld"), *PendingScreenshot, static_cast<long long>(Size));
            if (ShotIndex < ReferenceGallery::ShotCount - 1) SetReferenceShot(ShotIndex + 1);
            else
            {
                bReferenceShots = false;
                UE_LOG(LogTemp, Log, TEXT("ReferenceShots: complete %d/%d"), ReferenceGallery::ShotCount, ReferenceGallery::ShotCount);
                FPlatformMisc::RequestExit(false);
            }
        }
        else if (Now - StageStartedAt > 30.0)
        {
            UE_LOG(LogTemp, Error, TEXT("ReferenceShots: capture timed out: %s"), *PendingScreenshot);
            FPlatformMisc::RequestExitWithStatus(false, 1);
        }
    }
}

void AGalleryGameMode::RunInputProbe()
{
    using namespace ReferenceGallery;
    // All timing is simulation time, never wall time. Tick after the controller,
    // pawn and movement solver; inject events for the NEXT input-processing tick.
    const double Now = GetWorld()->GetTimeSeconds();
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    AGalleryVisitor* Visitor = Cast<AGalleryVisitor>(PC ? PC->GetPawn() : nullptr);
    if (!PC || !PC->PlayerInput || !Visitor)
    {
        UE_LOG(LogTemp, Error, TEXT("InputProbe: result=FAIL no player input or visitor"));
        bInputProbeComplete = true;
        FPlatformMisc::RequestExitWithStatus(false, 1);
        return;
    }
    UCharacterMovementComponent* Movement = Visitor->GetCharacterMovement();
    const FInputCase& Test = InputCases[InputProbeCase];
    const bool bMouse = Test.Check == EInputCheck::MouseYaw || Test.Check == EInputCheck::MousePitch;
    const bool bMove = Test.Check == EInputCheck::Forward || Test.Check == EInputCheck::Strafe;
    const bool bYaw = Test.Check == EInputCheck::Yaw || Test.Check == EInputCheck::MouseYaw;
    AGalleryInteractiveDoor* Door = nullptr;
    for (TActorIterator<AGalleryInteractiveDoor> It(GetWorld()); It; ++It)
    {
        if (!Door || FVector::DistSquared(Visitor->GetActorLocation(), It->GetActorLocation())
            < FVector::DistSquared(Visitor->GetActorLocation(), Door->GetActorLocation())) Door = *It;
    }
    float LightIntensity = 0.f;
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("ReferenceSwitchableLight")) || It->ActorHasTag(TEXT("ReferenceAccentLight"))) continue;
        TInlineComponentArray<ULightComponent*> Lights;
        It->GetComponents(Lights);
        for (ULightComponent* Light : Lights) LightIntensity += Light->Intensity;
    }

    if (InputProbeStage == 0)
    {
        if (InputProbeCase == 0)
        {
            AddTickPrerequisiteActor(PC);
            AddTickPrerequisiteActor(Visitor);
            AddTickPrerequisiteComponent(Movement);
            UE_LOG(LogTemp, Log, TEXT("InputProbe: start cases=%d player_input=%s input_component=%s simulation_time=1"),
                UE_ARRAY_COUNT(InputCases), *GetNameSafe(PC->PlayerInput->GetClass()),
                Visitor->InputComponent ? *GetNameSafe(Visitor->InputComponent->GetClass()) : TEXT("none"));
        }
        // Reset EVERY case, including pitch/yaw, queued inputs and residual
        // velocity. No collision-free fly mode: tests use the real walking solver.
        for (const FInputCase& Other : InputCases)
            InjectKey(PC, Other.Key, Other.Key.IsAnalog() ? IE_Axis : IE_Released, 0.f);
        PC->FlushPressedKeys();
        PC->ResetIgnoreMoveInput();
        PC->ResetIgnoreLookInput();
        PC->RotationInput = FRotator::ZeroRotator;
        PC->SetViewTarget(Visitor);
        PC->bShowMouseCursor = false;
        PC->SetInputMode(FInputModeGameOnly());
        Movement->StopMovementImmediately();
        Visitor->ConsumeMovementInputVector();
        const bool bAction = Test.Check == EInputCheck::Door || Test.Check == EInputCheck::Lighting;
        const FVector Fixture(bAction ? -450.f : -400.f, bAction ? -680.f : -600.f,
            Visitor->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 2.f);
        // Deliberately cross 0/360 in both yaw directions.
        const float StartYaw = bYaw ? (Test.Sign > 0.f ? 350.f : 10.f) : 0.f;
        const FRotator StartRotation(0.f, StartYaw, 0.f);
        Visitor->SetActorLocationAndRotation(Fixture, StartRotation, false, nullptr, ETeleportType::TeleportPhysics);
        PC->SetControlRotation(StartRotation);
        if (bMove)
        {
            const FVector Direction = Test.Check == EInputCheck::Forward ? FVector::ForwardVector : FVector::RightVector;
            FCollisionQueryParams Query(SCENE_QUERY_STAT(InputProbeClearance), false, Visitor);
            FHitResult Hit;
            const bool bBlocked = GetWorld()->SweepSingleByChannel(Hit, Fixture, Fixture + Direction * Test.Sign * 210.f,
                FQuat::Identity, ECC_Pawn, Visitor->GetCapsuleComponent()->GetCollisionShape(), Query);
            bInputProbePassed &= !bBlocked;
            UE_LOG(LogTemp, Log, TEXT("InputProbe: fixture key=%s clear_210cm=%d blocker=%s"),
                Test.Name, !bBlocked, *GetNameSafe(Hit.GetActor()));
        }
        InputProbeStage = 1;
        InputProbeStageAt = Now;
        return;
    }

    if (InputProbeStage == 1 && Now - InputProbeStageAt + 0.00001 >= 0.15)
    {
        Movement->StopMovementImmediately();
        Visitor->ConsumeMovementInputVector();
        InputProbeStartLocation = Visitor->GetActorLocation();
        InputProbeStartRotation = PC->GetControlRotation();
        bInputProbePassed &= Movement->IsMovingOnGround();
        UE_LOG(LogTemp, Log, TEXT("InputProbe: ready case=%s location=%s rotation=%s grounded=%d"),
            Test.Name, *InputProbeStartLocation.ToString(), *InputProbeStartRotation.ToString(), Movement->IsMovingOnGround());
        bInputProbeActionBefore = Test.Check == EInputCheck::Door ? (Door && Door->bIsOpen) : Visitor->bShowcaseLighting;
        InputProbeLightBefore = LightIntensity;
        // Mouse is ONE raw delta, not a rate repeated every frame.
        InjectKey(PC, Test.Key, bMouse ? IE_Axis : IE_Pressed, bMouse ? Test.Sign * 120.f : 1.f);
        InputProbeStage = 2;
        InputProbeStageAt = Now;
        return;
    }
    if (InputProbeStage != 2 || Now - InputProbeStageAt + 0.00001 < Test.Duration) return;

    InjectKey(PC, Test.Key, bMouse ? IE_Axis : IE_Released, 0.f);
    const float Elapsed = static_cast<float>(Now - InputProbeStageAt);
    const FVector Delta = Visitor->GetActorLocation() - InputProbeStartLocation;
    const FRotator End = PC->GetControlRotation();
    const float YawDelta = FMath::FindDeltaAngleDegrees(InputProbeStartRotation.Yaw, End.Yaw);
    const float PitchDelta = FMath::FindDeltaAngleDegrees(InputProbeStartRotation.Pitch, End.Pitch);
    bool bPassed = false;
    if (bMove)
    {
        const FRotator Basis(0.f, InputProbeStartRotation.Yaw, 0.f);
        const float Forward = FVector::DotProduct(Delta, Basis.Vector());
        const float Right = FVector::DotProduct(Delta, FRotationMatrix(Basis).GetUnitAxis(EAxis::Y));
        const float Along = Test.Check == EInputCheck::Forward ? Forward : Right;
        const float Across = Test.Check == EInputCheck::Forward ? Right : Forward;
        bPassed = Test.Sign * Along > 100.f && FMath::Abs(Across) < 5.f && FMath::Abs(Delta.Z) < 6.f
            && FMath::Abs(YawDelta) < 1.f && FMath::Abs(PitchDelta) < 1.f && Movement->IsMovingOnGround();
        UE_LOG(LogTemp, Log, TEXT("InputProbe: case=%s sim_s=%.4f forward_cm=%.3f right_cm=%.3f dz_cm=%.3f -> %s"),
            Test.Name, Elapsed, Forward, Right, Delta.Z, bPassed ? TEXT("PASS") : TEXT("FAIL"));
    }
    else if (Test.Check == EInputCheck::Door)
    {
        bPassed = Door && Door->bIsOpen != bInputProbeActionBefore && Door->bIsOpen == (Test.Sign > 0.f);
        UE_LOG(LogTemp, Log, TEXT("InputProbe: case=%s injected=E before=%d after=%d -> %s"),
            Test.Name, bInputProbeActionBefore, Door && Door->bIsOpen, bPassed ? TEXT("PASS") : TEXT("FAIL"));
    }
    else if (Test.Check == EInputCheck::Lighting)
    {
        const float ExpectedScale = Test.Sign > 0.f ? 0.35f : 1.f / 0.35f;
        bPassed = Visitor->bShowcaseLighting != bInputProbeActionBefore && Visitor->bShowcaseLighting == (Test.Sign > 0.f)
            && InputProbeLightBefore > 0.f && FMath::IsNearlyEqual(LightIntensity / InputProbeLightBefore, ExpectedScale, 0.001f);
        UE_LOG(LogTemp, Log, TEXT("InputProbe: case=%s injected=L before=%d after=%d light_before=%.2f light_after=%.2f -> %s"),
            Test.Name, bInputProbeActionBefore, Visitor->bShowcaseLighting, InputProbeLightBefore, LightIntensity,
            bPassed ? TEXT("PASS") : TEXT("FAIL"));
    }
    else
    {
        // The contract is 150 degrees/second for keys (ArrowLookRate), and
        // 0.15 degrees per raw mouse unit. Wrong sign/rate/DT must all go red.
        const float Expected = Test.Sign * (bMouse ? 120.f * 0.15f : Visitor->ArrowLookRate * Elapsed);
        const float Along = bYaw ? YawDelta : PitchDelta;
        const float Across = bYaw ? PitchDelta : YawDelta;
        const float MinimumAngle = bMouse || !bYaw ? 10.f : 20.f;
        bPassed = Test.Sign * Along > MinimumAngle && FMath::Abs(Along - Expected) < 2.f
            && FMath::Abs(Across) < 1.f && Delta.Size2D() < 2.f;
        UE_LOG(LogTemp, Log, TEXT("InputProbe: case=%s sim_s=%.4f yaw_start=%.3f yaw_end=%.3f pitch_start=%.3f pitch_end=%.3f yaw_delta=%.3f pitch_delta=%.3f expected=%.3f -> %s"),
            Test.Name, Elapsed, InputProbeStartRotation.Yaw, End.Yaw, InputProbeStartRotation.Pitch, End.Pitch,
            YawDelta, PitchDelta, Expected, bPassed ? TEXT("PASS") : TEXT("FAIL"));
    }
    bInputProbePassed &= bPassed;
    InputProbePassedCases += bPassed ? 1 : 0;
    Movement->StopMovementImmediately();
    Visitor->ConsumeMovementInputVector();
    InputProbeStage = 0;
    ++InputProbeCase;
    if (InputProbeCase == UE_ARRAY_COUNT(InputCases))
    {
        const bool bAll = bReferenceProbePassed && bInputProbePassed && InputProbePassedCases == UE_ARRAY_COUNT(InputCases);
        UE_LOG(LogTemp, Log, TEXT("InputProbe: result=%s passed=%d total=%d floor=%d fixtures_and_cases=%d"),
            bAll ? TEXT("PASS") : TEXT("FAIL"), InputProbePassedCases, UE_ARRAY_COUNT(InputCases),
            bReferenceProbePassed, bInputProbePassed);
        bInputProbeComplete = true;
        // A failed floor/input probe must not be masked by a later screenshot exit.
        if (!bAll || !bReferenceShots) FPlatformMisc::RequestExitWithStatus(false, bAll ? 0 : 1);
    }
}

void AGalleryGameMode::RunReferenceProbe()
{
    bProbeComplete = true;
    const AGalleryVisitor* Visitor = Cast<AGalleryVisitor>(UGameplayStatics::GetPlayerPawn(this, 0));
    bool bPassed = Visitor != nullptr;
    if (Visitor)
    {
        const float FeetZ = Visitor->GetActorLocation().Z - Visitor->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
        const bool bWalking = Visitor->GetCharacterMovement()->IsMovingOnGround();
        const bool bCollision = Visitor->GetActorEnableCollision() && Visitor->GetCharacterMovement()->GravityScale > 0.f;
        FCollisionQueryParams Query(SCENE_QUERY_STAT(ReferenceProbe), false, Visitor);
        FHitResult Floor;
        // Test-only trace override permits a real missed-floor negative control
        // (e.g. 1 cm) without altering/saving the level or disabling collision.
        float FloorTraceDistance = 180.f;
        FParse::Value(FCommandLine::Get(), TEXT("ReferenceProbeFloorTraceDistance="), FloorTraceDistance);
        const bool bFloor = GetWorld()->LineTraceSingleByChannel(Floor,
            Visitor->GetActorLocation(), Visitor->GetActorLocation() - FVector(0.f, 0.f, FloorTraceDistance), ECC_Visibility, Query);
        bPassed = bWalking && bCollision && bFloor && FMath::Abs(FeetZ - Floor.ImpactPoint.Z) < 6.f;
        UE_LOG(LogTemp, Log, TEXT("ReferenceProbe: grounded=%d collision=%d floor=%d feet_z=%.2f floor_z=%.2f trace_cm=%.2f result=%s"),
            bWalking, bCollision, bFloor, FeetZ, Floor.ImpactPoint.Z, FloorTraceDistance, bPassed ? TEXT("PASS") : TEXT("FAIL"));
    }
    else UE_LOG(LogTemp, Error, TEXT("ReferenceProbe: FAIL no GalleryVisitor"));
    // Persist the floor result: the input probe owns the combined final exit.
    bReferenceProbePassed = bPassed;
}


#include "GalleryVisitor.h"
#include "GalleryInteractiveDoor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/AudioComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/LightComponent.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Sound/SoundBase.h"

AGalleryVisitor::AGalleryVisitor()
{
    PrimaryActorTick.bCanEverTick = true;
    GetCapsuleComponent()->InitCapsuleSize(28.f, 98.f);
    GetCapsuleComponent()->SetCollisionProfileName(TEXT("Pawn"));
    bUseControllerRotationYaw = true;
    bUseControllerRotationPitch = false;
    GetCharacterMovement()->GravityScale = 1.f;
    GetCharacterMovement()->MaxWalkSpeed = 220.f;
    GetCharacterMovement()->MaxStepHeight = 30.f;
    GetCharacterMovement()->bOrientRotationToMovement = false;
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("VisitorCamera"));
    Camera->SetupAttachment(GetCapsuleComponent());
    Camera->SetRelativeLocation(FVector(0.f, 0.f, 72.f));
    Camera->bUsePawnControlRotation = true;
    Camera->FieldOfView = 70.f;
    BaseEyeHeight = 72.f;
    AmbientAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("InteriorRoomTone"));
    AmbientAudio->SetupAttachment(GetRootComponent());
    AmbientAudio->bAutoActivate = false;
    AmbientAudio->bAllowSpatialization = false;
    AmbientAudio->SetVolumeMultiplier(0.18f);
}

void AGalleryVisitor::PossessedBy(AController* NewController)
{
    Super::PossessedBy(NewController);
    if (APlayerController* PC = Cast<APlayerController>(NewController))
    {
        PC->bShowMouseCursor = false;
        PC->SetInputMode(FInputModeGameOnly());
        if (PC->PlayerCameraManager)
        {
            PC->PlayerCameraManager->ViewPitchMin = -75.f;
            PC->PlayerCameraManager->ViewPitchMax = 75.f;
        }
    }
}

void AGalleryVisitor::BeginPlay()
{
    Super::BeginPlay();
    if (!AmbientSound)
    {
        AmbientSound = LoadObject<USoundBase>(nullptr,
            TEXT("/Game/ReferenceGallery/Audio/A_ReferenceRoomTone.A_ReferenceRoomTone"));
    }
    if (AmbientSound)
    {
        AmbientAudio->SetSound(AmbientSound);
        AmbientAudio->Play();
    }
    else
    {
        UE_LOG(LogTemp, Warning, TEXT("ReferenceVisitor: room tone not imported; audio disabled"));
    }
    UE_LOG(LogTemp, Log, TEXT("ReferenceVisitor: gravity=1 capsule=(28,98) eye=170cm; WASD mouse/arrows E door L showcase"));
    if (GEngine)
    {
        GEngine->AddOnScreenDebugMessage(-1, 8.f, FColor::White,
            TEXT("WASD walk  |  Mouse / Arrows look  |  E door (stand back)  |  L showcase lighting"));
    }
}

void AGalleryVisitor::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    // Mouse axes are deltas; digital movement/look keys are polled in Tick.
    // Digital arrows are NOT Axis1D keys and must never use BindAxisKey.
    // Native bindings need neither InputAction assets nor named axis mappings.
    PlayerInputComponent->BindAxisKey(EKeys::MouseX, this, &AGalleryVisitor::LookYaw);
    PlayerInputComponent->BindAxisKey(EKeys::MouseY, this, &AGalleryVisitor::LookPitch);
    PlayerInputComponent->BindKey(EKeys::E, IE_Pressed, this, &AGalleryVisitor::Interact);
    PlayerInputComponent->BindKey(EKeys::L, IE_Pressed, this, &AGalleryVisitor::ToggleLightingMode);
    UE_LOG(LogTemp, Log, TEXT("ReferenceVisitor: input ready -- WASD/arrows polling, 2 mouse axes, E/L actions"));
}

void AGalleryVisitor::LookYaw(float Value) { ApplyLookDelta(Value * MouseLookSensitivity, 0.f); }
void AGalleryVisitor::LookPitch(float Value) { ApplyLookDelta(0.f, Value * MouseLookSensitivity); }

void AGalleryVisitor::ApplyLookDelta(float YawDegrees, float PitchDegrees)
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC || !PC->IsLocalController() || PC->IsLookInputIgnored()
        || (YawDegrees == 0.f && PitchDegrees == 0.f)) return;
    // Explicit degrees avoid the legacy controller multipliers (+2.5 yaw,
    // -2.5 pitch) and avoid queuing RotationInput after the controller's tick.
    FRotator Rotation = PC->GetControlRotation();
    Rotation.Yaw = FRotator::NormalizeAxis(Rotation.Yaw + YawDegrees);
    const float MinPitch = PC->PlayerCameraManager ? PC->PlayerCameraManager->ViewPitchMin : -75.f;
    const float MaxPitch = PC->PlayerCameraManager ? PC->PlayerCameraManager->ViewPitchMax : 75.f;
    Rotation.Pitch = FMath::Clamp(FRotator::NormalizeAxis(Rotation.Pitch) + PitchDegrees, MinPitch, MaxPitch);
    PC->SetControlRotation(Rotation);
}

void AGalleryVisitor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC || !PC->IsLocalController()) return;
    // Positive yaw turns right; positive UE pitch looks up. Opposites cancel.
    const float Turn = (PC->IsInputKeyDown(EKeys::Right) ? 1.f : 0.f) - (PC->IsInputKeyDown(EKeys::Left) ? 1.f : 0.f);
    const float Pitch = (PC->IsInputKeyDown(EKeys::Up) ? 1.f : 0.f) - (PC->IsInputKeyDown(EKeys::Down) ? 1.f : 0.f);
    ApplyLookDelta(Turn * ArrowLookRate * DeltaSeconds, Pitch * ArrowLookRate * DeltaSeconds);
    // Ignore-move and ignore-look are independent (e.g. a stationary camera).
    if (PC->IsMoveInputIgnored()) return;
    // Poll digital movement keys, still feed the actual CharacterMovement sweep/gravity solver.
    const float Forward = (PC->IsInputKeyDown(EKeys::W) ? 1.f : 0.f) - (PC->IsInputKeyDown(EKeys::S) ? 1.f : 0.f);
    const float Right = (PC->IsInputKeyDown(EKeys::D) ? 1.f : 0.f) - (PC->IsInputKeyDown(EKeys::A) ? 1.f : 0.f);
    const FRotator Yaw(0.f, PC->GetControlRotation().Yaw, 0.f);
    const FVector Direction = (Yaw.Vector() * Forward + FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y) * Right).GetClampedToMaxSize(1.f);
    AddMovementInput(Direction, 1.f);
}

void AGalleryVisitor::Interact()
{
    AGalleryInteractiveDoor* Nearest = nullptr;
    float BestDistance = TNumericLimits<float>::Max();
    for (TActorIterator<AGalleryInteractiveDoor> It(GetWorld()); It; ++It)
    {
        const float Distance = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
        if (Distance < BestDistance) { Nearest = *It; BestDistance = Distance; }
    }
    if (Nearest) Nearest->Interact(this);
}

void AGalleryVisitor::ToggleLightingMode() { SetShowcaseLighting(!bShowcaseLighting); }

void AGalleryVisitor::SetShowcaseLighting(bool bShowcase)
{
    bShowcaseLighting = bShowcase;
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("ReferenceSwitchableLight"))) continue;
        TInlineComponentArray<ULightComponent*> Lights;
        It->GetComponents(Lights);
        for (ULightComponent* Light : Lights)
        {
            const TWeakObjectPtr<ULightComponent> Key(Light);
            if (!OriginalLightIntensities.Contains(Key)) OriginalLightIntensities.Add(Key, Light->Intensity);
            const float Scale = bShowcase && !It->ActorHasTag(TEXT("ReferenceAccentLight")) ? 0.35f : 1.f;
            Light->SetIntensity(OriginalLightIntensities.FindChecked(Key) * Scale);
        }
    }
    UE_LOG(LogTemp, Log, TEXT("ReferenceVisitor: lighting=%s tracked_components=%d"),
        bShowcase ? TEXT("showcase") : TEXT("normal"), OriginalLightIntensities.Num());
}

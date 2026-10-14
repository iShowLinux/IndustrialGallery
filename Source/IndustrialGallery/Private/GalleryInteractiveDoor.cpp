#include "GalleryInteractiveDoor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "UObject/ConstructorHelpers.h"

AGalleryInteractiveDoor::AGalleryInteractiveDoor()
{
    PrimaryActorTick.bCanEverTick = true;
    Hinge = CreateDefaultSubobject<USceneComponent>(TEXT("DoorHinge"));
    SetRootComponent(Hinge);
    Hinge->SetMobility(EComponentMobility::Movable);
    Leaf = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorLeaf"));
    Leaf->SetupAttachment(Hinge);
    Leaf->SetMobility(EComponentMobility::Movable);
    Leaf->SetCollisionProfileName(TEXT("BlockAll"));
    Handle = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorHandle"));
    Handle->SetupAttachment(Hinge);
    Handle->SetMobility(EComponentMobility::Movable);
    Handle->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded())
    {
        Leaf->SetStaticMesh(Cube.Object);
        Handle->SetStaticMesh(Cube.Object);
    }
}

void AGalleryInteractiveDoor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    Leaf->SetRelativeLocation(FVector(Width * 0.5f, 0.f, Height * 0.5f));
    Leaf->SetRelativeScale3D(FVector(Width / 100.f, 0.06f, Height / 100.f));
    Handle->SetRelativeLocation(FVector(Width - 15.f, 6.f, 110.f));
    Handle->SetRelativeScale3D(FVector(0.12f, 0.08f, 0.035f));
}

bool AGalleryInteractiveDoor::IsSwingAreaOccupied() const
{
    // A conservative safety zone prevents a rotating leaf from trapping a visitor.
    // Rotation sweeps do not provide continuous collision detection in UE.
    for (TActorIterator<ACharacter> It(GetWorld()); It; ++It)
    {
        if (FVector::Dist2D(It->GetActorLocation(), GetActorLocation()) < Width + 45.f
            && FMath::Abs(It->GetActorLocation().Z - GetActorLocation().Z) < Height)
        {
            return true;
        }
    }
    return false;
}

bool AGalleryInteractiveDoor::Interact(AActor* Interactor)
{
    if (!Interactor) return false;
    const FVector Center = GetActorTransform().TransformPosition(FVector(Width * 0.5f, 0.f, Height * 0.5f));
    if (FVector::Dist(Interactor->GetActorLocation(), Center) > InteractionDistance) return false;
    if (IsSwingAreaOccupied())
    {
        UE_LOG(LogTemp, Log, TEXT("ReferenceDoor: swing zone occupied; step back before opening/closing"));
        return false;
    }
    bIsOpen = !bIsOpen;
    UE_LOG(LogTemp, Log, TEXT("ReferenceDoor: target=%s"), bIsOpen ? TEXT("open") : TEXT("closed"));
    return true;
}

void AGalleryInteractiveDoor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    const float Target = bIsOpen ? OpenAngle : 0.f;
    if (FMath::IsNearlyEqual(CurrentAngle, Target, 0.05f) || IsSwingAreaOccupied()) return;
    CurrentAngle = FMath::FInterpConstantTo(CurrentAngle, Target, DeltaSeconds, 75.f);
    // Root stays fixed at the hinge. Rotate both meshes around their common origin.
    const FRotator Rotation(0.f, CurrentAngle, 0.f);
    Leaf->SetRelativeLocation(Rotation.RotateVector(FVector(Width * 0.5f, 0.f, Height * 0.5f)));
    Leaf->SetRelativeRotation(Rotation);
    Handle->SetRelativeLocation(Rotation.RotateVector(FVector(Width - 15.f, 6.f, 110.f)));
    Handle->SetRelativeRotation(Rotation);
}

"""Argument-order-safe unreal.Rotator construction.

The Python binding's POSITIONAL order is (roll, pitch, yaw) -- verified against
the installed engine, not assumed:

    unreal.Rotator(0, 90, 0)  ->  pitch=90, yaw=0, roll=0

Authoring a rotation tuple in C++ order (pitch, yaw, roll) and passing it
positionally therefore turns every intended YAW into a PITCH. The failure is
silent and global: wall artwork lies flat on its back, ceiling ducts point
straight up, suspended fixtures roll onto their edges, and every aimed light
fires along world +X instead of at its target -- while every parameter readback
and every "it built successfully" log line still passes.

Always construct through rot() so the authored order is C++ order everywhere.
"""


def rot(pitch=0.0, yaw=0.0, roll=0.0):
    """Build an unreal.Rotator from C++ argument order (pitch, yaw, roll)."""
    import unreal
    return unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)

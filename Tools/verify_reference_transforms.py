"""Read-only saved-map orientation checks. Execute with UnrealEditor-Cmd.

This inspects engine vectors, not the builder's claimed intended transforms.
It does not save or mutate the level. A success marker is emitted only if every
check passes; inspect Saved/ReferenceVerification/transforms.json on failure.
"""
from pathlib import Path
import json
import math
import sys
import unreal

ROOT = Path(unreal.Paths.project_dir())
sys.path.insert(0, str(ROOT / 'Tools'))
import reference_props
import reference_lighting

LEVEL = '/Game/ReferenceGallery/L_ReferenceGallery'
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL)
actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
by_label = {a.get_actor_label(): a for a in actors}
checks = []

def check(name, passed, observed):
    checks.append({'check': name, 'pass': bool(passed), 'observed': observed})
    unreal.log('TRANSFORM_CHECK ' + name + ' ' + ('PASS' if passed else 'FAIL') + ' ' + str(observed))

def xyz(v):
    return [round(v.x, 5), round(v.y, 5), round(v.z, 5)]

# Establish this installed engine's constructor behavior without an assumption.
r = unreal.Rotator(0, 90, 0)
unreal.log('ROTATOR_POSITIONAL_API ' + str(r))

for name, _loc, _w, _h, _tex, _label, yaw in reference_props.ART_HANGINGS:
    a = by_label.get(name + '_Canvas')
    if a is None:
        check(name, False, 'missing canvas')
        continue
    up = a.get_actor_up_vector()
    normal = a.get_actor_right_vector() * -1.0
    angle = math.radians(yaw)
    desired = (math.sin(angle), -math.cos(angle), 0)
    dot = sum(x*y for x,y in zip(xyz(normal), desired))
    check(name + '_upright_and_wall_facing', up.z > .999 and dot > .999,
          {'up': xyz(up), 'normal': xyz(normal), 'expected_normal':desired})

mains = [a for a in actors if a.get_actor_label().startswith('Spiral_Duct_Main')]
check('two_main_ducts', len(mains) == 2, len(mains))
for index, a in enumerate(mains):
    up = a.get_actor_up_vector()
    check('main_duct_' + str(index) + '_axis_Y', abs(up.y) > .999, xyz(up))
a = by_label.get('Cross_Duct')
check('cross_duct_axis_X', a is not None and abs(a.get_actor_up_vector().x) > .999,
      xyz(a.get_actor_up_vector()) if a else 'missing')

ribbon = [a for a in actors if a.get_actor_label().startswith('Ribbon_') and
          any(s in a.get_actor_label() for s in ('Housing_', 'Diffuser_', 'DiffuserTop_'))]
bad = [{'label':a.get_actor_label(), 'up':xyz(a.get_actor_up_vector())} for a in ribbon
       if a.get_actor_up_vector().z < .999]
check('suspended_ribbon_horizontal', len(ribbon) > 0 and not bad,
      {'segments':len(ribbon), 'bad_count':len(bad), 'examples':bad[:6]})

for row in reference_lighting.SPOTS + reference_lighting.RECTS + reference_lighting.BOUNCE:
    name, pos, target = row[:3]
    a = by_label.get('REF_Light_' + name)
    if a is None:
        check('light_' + name, False, 'missing')
        continue
    expected = [target[i]-pos[i] for i in range(3)]
    length = math.sqrt(sum(x*x for x in expected))
    forward = a.get_actor_forward_vector()
    dot = sum(x*y/length for x,y in zip(xyz(forward),expected))
    check('light_' + name + '_aim', dot > .999, {'cosine':round(dot,6),'forward':xyz(forward)})

start = by_label.get('REF_Technical_PlayerStart')
if start:
    r = start.get_actor_rotation()
    check('player_start_level_facing_north', abs(r.pitch) < .01 and abs(r.roll) < .01 and abs(r.yaw-90) < .01, str(r))
else:
    check('player_start_level_facing_north', False, 'missing')

rejected = [a.get_actor_label() for a in actors if 'Partition' in a.get_actor_label() and
            any(t in a.get_actor_label() for t in ('Arc', 'Curve', 'Sweep'))]
check('rejected_wall_not_restored', not rejected, rejected)

# --- truss ceiling and curved partition (added from the reference's own data) ---
truss = by_label.get('Ceiling_Trusses')
if truss:
    comps = truss.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
    n = comps[0].get_instance_count() if comps else 0
    # 3 trusses x (2 chords + 26 webs)
    check('truss_instance_count', n == 84, n)
else:
    check('truss_instance_count', False, 'Ceiling_Trusses missing')

curved = by_label.get('Curved_Partition')
if curved:
    origin = curved.get_actor_location()
    bb = curved.static_mesh_component.static_mesh.get_bounding_box()
    lo = bb.min + origin
    hi = bb.max + origin
    # Reference bounds in Spline units, mapped by the authored offset (-390, 0, 0).
    expect = {'x': (-390.0 + 51.0, -390.0 + 560.0), 'y': (0.0, 185.0), 'z': (-229.0, 150.0)}
    got = {'x': (lo.x, hi.x), 'y': (lo.y, hi.y), 'z': (lo.z, hi.z)}
    ok = all(abs(got[k][0] - expect[k][0]) < 2.0 and abs(got[k][1] - expect[k][1]) < 2.0
             for k in expect)
    check('curved_partition_matches_reference_bounds', ok,
          {'expected': {k: [round(v, 1) for v in expect[k]] for k in expect},
           'got': {k: [round(v, 1) for v in got[k]] for k in got}})
    # A fillet, not a chorded arc: the swept surface must be a single closed mesh
    # with many sections. 700 triangles over 88 sections is the swept solid.
    tris = curved.static_mesh_component.static_mesh.get_num_triangles(0)
    check('curved_partition_is_swept_solid', tris >= 500, tris)
else:
    check('curved_partition_matches_reference_bounds', False, 'Curved_Partition missing')
    check('curved_partition_is_swept_solid', False, 'Curved_Partition missing')

report = {'map':LEVEL, 'actor_count':len(actors), 'checks':checks,
          'passed':all(c['pass'] for c in checks), 'check_count':len(checks)}
path = ROOT / 'Saved/ReferenceVerification/transforms.json'
path.parent.mkdir(parents=True,exist_ok=True)
path.write_text(json.dumps(report,indent=2),encoding='utf-8')
if not report['passed']:
    raise RuntimeError('REFERENCE_TRANSFORMS_FAILED: ' + str(sum(not c['pass'] for c in checks)) + ' checks; ' + str(path))
unreal.log('REFERENCE_TRANSFORMS_SUCCESS ' + str(len(checks)))

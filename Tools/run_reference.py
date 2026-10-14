"""Local UE build/author/capture runner. Never treats stale output as success."""
from pathlib import Path
import argparse
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path('C:/Program Files/Epic Games/UE_5.8/Engine')
PROJECT = ROOT / 'IndustrialGallery.uproject'
LOGS = ROOT / 'Saved' / 'ReferenceVerification'
LOGS.mkdir(parents=True, exist_ok=True)


def run(stage, args, timeout=900, required=None):
    if stage in ('author', 'capture', 'probe', 'transforms'):
        dll = ROOT / 'Binaries/Win64/UnrealEditor-IndustrialGallery.dll'
        sources = [p for p in (ROOT / 'Source').rglob('*') if p.suffix in ('.cpp', '.h')]
        if not dll.is_file() or not sources or dll.stat().st_mtime < max(p.stat().st_mtime for p in sources):
            raise RuntimeError('Missing or stale module; compile successfully before '+stage)
    log = LOGS / (stage + '.log')
    env = os.environ.copy()
    env['DOTNET_ROOT'] = str(ENGINE / 'Binaries/ThirdParty/DotNet/10.0/win-x64')
    env['DOTNET_MULTILEVEL_LOOKUP'] = '0'
    env['DOTNET_ROLL_FORWARD'] = 'LatestMajor'
    start = time.time()
    with log.open('w',encoding='utf-8') as out:
        p = subprocess.run([str(a) for a in args], cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT,timeout=timeout)
    text=log.read_text(encoding='utf-8',errors='replace')
    important=[s for s in text.splitlines() if any(k.lower() in s.lower() for k in ['error','warning:','Reference','Result:','fatal','Exception','screenshot'])]
    print('\n'.join(important[-100:]))
    print('LOG:', log, 'EXIT:',p.returncode,'SECONDS:',round(time.time()-start,1))
    if p.returncode != 0 or (required and required not in text):
        raise RuntimeError(stage + ' failed; inspect log ' + str(log))
    if any(token in text for token in ('Failed to compile Material', 'missing usage flag', 'Fatal error:')):
        raise RuntimeError('Render/material failure in '+str(log))
    if stage == 'probe':
        probe_lines = [line for line in text.splitlines()
                       if 'ReferenceProbe:' in line or 'InputProbe:' in line]
        if any('FAIL' in line for line in probe_lines):
            raise RuntimeError('A probe case failed even if the process/summary reported success: '+str(log))
        if not any('ReferenceProbe:' in line and 'result=PASS' in line for line in probe_lines):
            raise RuntimeError('Missing successful floor/collision probe: '+str(log))
        if not any('InputProbe: result=PASS' in line for line in probe_lines):
            raise RuntimeError('Missing successful input probe: '+str(log))
    return start


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['compile','author','capture','probe'])
    args=ap.parse_args()
    if args.stage=='compile':
        run('compile',[ENGINE/'Binaries/ThirdParty/DotNet/10.0/win-x64/dotnet.exe',ENGINE/'Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll','IndustrialGalleryEditor','Win64','Development','-Project='+str(PROJECT),'-WaitMutex'],required='Result: Succeeded')
        dll=ROOT/'Binaries/Win64/UnrealEditor-IndustrialGallery.dll'
        latest=max(p.stat().st_mtime for p in (ROOT/'Source').rglob('*') if p.suffix in ['.cpp','.h'])
        if dll.stat().st_mtime < latest:
            raise RuntimeError('Compiled DLL older than source')
        print('DLL_FRESH',dll)
    elif args.stage=='author':
        run('author',[ENGINE/'Binaries/Win64/UnrealEditor-Cmd.exe',PROJECT,'-ExecutePythonScript='+str(ROOT/'Tools/build_reference.py'),'-unattended','-nopause','-nosplash','-nullrhi','-stdout','-FullStdOutLogOutput'],required='REFERENCE_BUILD_SUCCESS')
    else:
        flag='-ReferenceShots' if args.stage=='capture' else '-ReferenceProbe'
        if args.stage=='capture':
            # Clear previous shots first: fixed filenames mean a renamed shot
            # leaves a stale PNG that silently pollutes the comparison set.
            for stale in (ROOT/'Saved/Screenshots').rglob('Reference_*.png'):
                stale.unlink()
        start=run(args.stage,[ENGINE/'Binaries/Win64/UnrealEditor.exe',PROJECT,'/Game/ReferenceGallery/L_ReferenceGallery','-game',flag,'-windowed','-ResX=1600','-ResY=900','-unattended','-nosplash','-stdout','-FullStdOutLogOutput'],timeout=600)
        if args.stage=='capture':
            shots=[p for p in (ROOT/'Saved/Screenshots').rglob('*.png') if p.stat().st_mtime>=start]
            print('FRESH_SCREENSHOTS',len(shots),*[str(p) for p in shots],sep='\n')
            if len(shots)<6:
                raise RuntimeError('Expected at least 6 fresh screenshots')

if __name__=='__main__':
    main()

"""Distinguish public-source integrity from availability of all local build inputs."""
import argparse,hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
def pin(p):
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    return dict(size=size,sha256=h.hexdigest())
def main():
    p=argparse.ArgumentParser();p.add_argument('--public-only',action='store_true');a=p.parse_args()
    manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text(encoding='utf8'));bad=[]
    for row in manifest['files']:
        path=ROOT/row['path'];expected=dict(size=row['bytes'],sha256=row['sha256'])
        if not path.is_file() or pin(path)!=expected:bad.append(row['path'])
    if bad:print(json.dumps(dict(status='FAIL_PUBLIC_SOURCE_INTEGRITY',paths=bad)));return 1
    if a.public_only:
        print(json.dumps(dict(status='PASS_PUBLIC_SOURCE_INTEGRITY',files=len(manifest['files']),full_game_build_verified=False)));return 0
    inputs=json.loads((ROOT/'workspace/reproduction/current27_inputs_20261030/manifest.json').read_text(encoding='utf8'))['inputs']
    missing=[];different=[]
    for n,v in inputs.items():
        p=ROOT/n
        if not p.is_file():missing.append(n)
        elif pin(p)!=v:different.append(n)
    print(json.dumps(dict(status='LOCAL_INPUTS_READY' if not missing and not different else 'LOCAL_INPUTS_INCOMPLETE',
        declared_inputs=len(inputs),missing=missing,different=different,full_game_build_verified=False)))
    return 0 if not missing and not different else 2
if __name__=='__main__':sys.exit(main())

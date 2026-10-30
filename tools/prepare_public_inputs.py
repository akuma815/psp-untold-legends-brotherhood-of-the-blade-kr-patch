"""Restore published metadata/fonts to ignored local paths without overwriting."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parent.parent
def pin(p):
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    return dict(size=size,sha256=h.hexdigest())
def member(n):
    p=PurePosixPath(n)
    if not n or '\\' in n or ':' in n or p.is_absolute() or any(v in ['.','..',''] for v in n.split('/')):raise ValueError('Unsafe path')
    out=ROOT.joinpath(*p.parts)
    if not out.resolve().is_relative_to(ROOT):raise ValueError('Escaping path')
    t=out
    while t!=ROOT:
        if t.is_symlink() or t.is_junction():raise ValueError('Linked path')
        t=t.parent
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--extract-text',action='store_true');a=p.parse_args()
    data=json.loads((ROOT/'inputs/PUBLIC_INPUTS.json').read_text(encoding='utf8'));copied=existing=0
    for row in data['restore_files']:
        source=member(row['source']);dest=member(row['target']);expected={k:row[k] for k in ['size','sha256']}
        if pin(source)!=expected:raise ValueError('Published input hash differs: '+row['source'])
        if dest.exists():
            if pin(dest)!=expected:raise ValueError('Existing different file;not overwritten: '+row['target'])
            existing+=1;continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        with source.open('rb') as f,dest.open('xb') as g:shutil.copyfileobj(f,g,2**20)
        if pin(dest)!=expected:raise ValueError('Copy verification failed')
        copied+=1
    if a.extract_text:
        for row in data['regenerate_from_owned_source']:
            if row['path'].startswith('extracted/disc/') and pin(member(row['path']))!={k:row[k] for k in ['size','sha256']}:raise ValueError('Original extraction differs')
        sys.path.insert(0,str(ROOT/'scripts'))
        from analyze_assets import locale
        locale('en_us')
        for row in data['regenerate_from_owned_source']:
            if row['path'].startswith('extracted/text/') and pin(member(row['path']))!={k:row[k] for k in ['size','sha256']}:raise ValueError('Regenerated text differs')
    print(json.dumps(dict(status='PASS_PUBLIC_INPUT_PREPARATION',copied=copied,existing_identical=existing,source_text_regenerated=a.extract_text,
        full_build_ready=False,note='Run check_inputs.py;excluded local graphics and assembler remain separate prerequisites.')))
if __name__=='__main__':main()

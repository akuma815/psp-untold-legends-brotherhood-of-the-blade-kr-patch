"""Recover frozen graphics inputs from owned textures plus original-relative deltas."""
import argparse,hashlib,io,json,shutil,subprocess,sys,tempfile
from pathlib import Path,PurePosixPath
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
def pin(p):
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    return dict(size=size,sha256=h.hexdigest())
def safe(n):
    r=PurePosixPath(n)
    if not n or '\\' in n or ':' in n or r.is_absolute() or any(x in ['.','..',''] for x in n.split('/')):raise ValueError('Unsafe input path')
    p=ROOT.joinpath(*r.parts)
    if not p.resolve().is_relative_to(ROOT):raise ValueError('Escaping input path')
    c=p
    while c!=ROOT:
        if c.is_symlink() or c.is_junction():raise ValueError('Linked input path')
        c=c.parent
    return p
def bases():
    sys.path.insert(0,str(ROOT/'scripts'))
    from map_texture_import_20261024 import source
    from ui_texture_inventory_20261024 import decode
    rows=source();im=Image.new('RGBA',(1024,1024))
    for row in rows:
        rgba=bytes(v for i in row['pixels'] for v in row['palette'][i]);tile=Image.frombytes('RGBA',(128,128),rgba)
        n=row['number']-1;im.paste(tile,(n%8*128,n//8*128))
    out=io.BytesIO();im.save(out,format='PNG');result={'map_png':out.getvalue()}
    entries=json.loads(safe('workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'))['entries']
    wad=safe('extracted/disc/PSP_GAME/USRDIR/resource.wad')
    with wad.open('rb') as f:
        for key,index in [('title_record',5419),('loading_record',5080)]:
            e=entries[index];f.seek(e['offset']);b=f.read(e['size_candidate'])
            if hashlib.sha256(b).hexdigest()!=e['sha256']:raise ValueError('Original texture mismatch')
            result[key]=b
    b=result['title_record'];palette=[b[i:i+4] for i in range(32,1056,4)];indices=decode(b[1056:],512,512,8)
    rgba=b''.join(palette[i] for i in indices);out=io.BytesIO();Image.frombytes('RGBA',(512,512),rgba).save(out,format='PNG');result['title_png']=out.getvalue()
    return result
def main():
    parser=argparse.ArgumentParser();parser.parse_args()
    spec=json.loads(safe('inputs/BUILD_INPUT_RECOVERY.json').read_text(encoding='utf8'))
    for n,v in spec['licensed_tools'].items():
        if pin(safe(n))!=v:raise ValueError('Licensed tool hash mismatch: '+n)
    data=bases();created=[]
    decoder=safe('tools/bin/xdelta3.exe')
    with tempfile.TemporaryDirectory(prefix='.input-recovery-',dir=ROOT) as temp:
        temp=Path(temp)
        if temp.resolve().parent!=ROOT.resolve():raise ValueError('Temporary recovery directory outside checkout')
        for key,b in data.items():(temp/key).write_bytes(b)
        for row in spec['graphics_inputs']:
            target=safe(row['target']);expected=row['result'];patch=safe(row['patch'])
            if pin(patch)!=row['patch_pin'] or pin(temp/row['base'])!=row['base_pin']:raise ValueError('Input recovery source differs')
            if target.exists():
                if pin(target)!=expected:raise ValueError('Existing input differs;not overwritten: '+row['target'])
                continue
            decoded=temp/'decoded';p=subprocess.run([str(decoder),'-d','-s',str(temp/row['base']),str(patch),str(decoded)],capture_output=True)
            if p.returncode:raise ValueError('Input delta failed: '+p.stderr.decode('utf8','replace'))
            if pin(decoded)!=expected:raise ValueError('Recovered graphics hash differs')
            target.parent.mkdir(parents=True,exist_ok=True)
            with decoded.open('rb') as src,target.open('xb') as out:shutil.copyfileobj(src,out,2**20)
            decoded.unlink();created.append(row['target'])
    tool=spec['assembler'];target=safe(tool['target']);source=safe(tool['source'])
    if pin(source)!=tool['pin']:raise ValueError('Assembler differs')
    if target.exists():
        if pin(target)!=tool['pin']:raise ValueError('Existing assembler differs;not overwritten')
    else:target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);created.append(tool['target'])
    print(json.dumps(dict(status='PASS_GIT_BUILD_INPUT_RECOVERY',graphics_inputs=10,assembler=1,created=created,original_texture_bases_verified=True,full_game_build_verified=False)))
if __name__=='__main__':main()

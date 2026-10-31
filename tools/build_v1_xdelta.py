"""Build v1.0 from translation sources and owned ISO, then encode a standalone patch."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def pin(p):
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    return dict(size=size,sha256=h.hexdigest())
def run(args):subprocess.run([str(x) for x in args],cwd=ROOT,check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    source=a.source.resolve();output=a.output.resolve()
    if output.suffix.lower()!='.xdelta' or output.exists() or not output.parent.is_dir():raise ValueError('Choose a new .xdelta output in an existing directory')
    report=output.with_suffix('.xdelta.json')
    if report.exists():raise ValueError('Existing report;not overwritten')
    run([sys.executable,'-B','tools/prepare_public_inputs.py'])
    run([sys.executable,'-B','scripts/survey.py','--source',source,'--extract'])
    run([sys.executable,'-B','tools/prepare_public_inputs.py','--extract-text'])
    run([sys.executable,'-B','tools/prepare_build_inputs.py'])
    run([sys.executable,'-B','tools/check_inputs.py'])
    name='git_v1_source_rebuild';folder=ROOT/'workspace/runtime'/name
    args=[sys.executable,'-B','scripts/build_map_crisp27_20261030.py','--variant','unicode_hangul_alias_fallback','--name',name,'--diagnostic-config','config/development_map_crisp27_20261030.json']
    if folder.exists():args.append('--verify')
    run(args)
    frozen=read(ROOT/'manifests/private_review_frozen_20261030.json')
    artifact=read(folder/'artifact.json')
    if artifact['files']!=frozen['game_files80']:raise ValueError('Rebuilt game differs from v1.0')
    spec=read(ROOT/'inputs/BUILD_INPUT_RECOVERY.json');decoder=ROOT/'tools/bin/xdelta3.exe'
    if pin(decoder)!=spec['licensed_tools']['tools/bin/xdelta3.exe']:raise ValueError('xdelta3 tool differs')
    sys.path.insert(0,str(ROOT/'scripts'));import release_iso
    with tempfile.TemporaryDirectory(prefix='.iso-xdelta-',dir=ROOT) as temp:
        temp=Path(temp);iso=temp/'Korean.iso'
        if temp.resolve().parent!=ROOT.resolve():raise ValueError('Temporary ISO directory outside checkout')
        built=release_iso.build(source,folder/'disc',iso,frozen['original_source_files80'],frozen['game_files80'])
        if pin(iso)!=dict(size=410986496,sha256='d12edc5bac1d71bfa9ef6aa78eab4991749b4aa09022106a93c0957a1711faf8'):raise ValueError('ISO differs from v1.0')
        # Disable the filename application header for path-independent output.
        run([decoder,'-e','-A','-s',source,iso,output])
        applied=temp/'Applied.iso';run([decoder,'-d','-s',source,output,applied])
        if pin(applied)!=pin(iso):raise ValueError('Generated xdelta roundtrip differs')
    report.write_text(json.dumps(dict(status='PASS_GIT_SOURCE_BUILD_XDELTA_ROUNDTRIP',patch=pin(output),source=pin(source),
        target=dict(size=built['size'],sha256=built['sha256']),game_files=80,private_workspace_inputs_used=False,
        translation_source_build=True,released_game_deltas_used=False,new_emulator_launch=False),indent=2)+'\n',encoding='utf8')
    print(str(report))
if __name__=='__main__':main()

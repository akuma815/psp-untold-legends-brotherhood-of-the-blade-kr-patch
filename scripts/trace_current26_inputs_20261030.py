"""Trace a real in-memory derivation; redirect generated files to a new owned tree.

Python file mutations outside the owned tree are rejected by an audit hook.
The sole admitted child is the pinned assembler with an owned input/cwd.
This is IO instrumentation, not an OS sandbox or native gameplay evidence.
"""
import argparse,builtins,hashlib,io,json,os,re,subprocess,sys,time,traceback
from pathlib import Path
from survey import ROOT,digest,save_json
import survey,catalog_survey034
from allegrex_profile import Profile,ASSEMBLER
from book_role_runtime_20261024 import artifact
from psp_folder import verify_tree
from PIL import ImageFont

def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',type=int,default=1);a=p.parse_args();assert 1<=a.attempt<=9
    work=ROOT/f'workspace/analysis/current26_input_trace_20261030_attempt{a.attempt:02d}'
    assert not work.exists();work.mkdir(parents=True);(work/'temp').mkdir()
    current=ROOT/'workspace/runtime/second_review_apply_20261030';source=ROOT/'extracted/disc'
    before=artifact('second_review_apply_20261030');verify_tree(source)
    guards={str(x.relative_to(ROOT)):digest(x.read_bytes()) for x in [current/'artifact.json',current/'expected_writes.json',ROOT/'workspace/translation/entries.jsonl',ROOT/'workspace/translation/terminology.json',ROOT/'config/development_second_review_apply_20261030.json']}
    old_open,old_io,old_mkdir=builtins.open,io.open,Path.mkdir
    old_assemble,old_protected=Profile.assemble,catalog_survey034.protected_write
    old_popen,old_font=subprocess.Popen,ImageFont.truetype
    reads={};read_phases={};redirects={};original_write_guards={};children=[];blocked=[];process_events=[];recording=True;admitted_child=False
    phase='import_and_derive';project_modules=[]
    def runtime_disc(path):return path.is_relative_to(ROOT/'workspace/runtime') and 'disc' in path.relative_to(ROOT/'workspace/runtime').parts
    def read_seen(path):
        reads[str(path)]=reads.get(str(path),0)+1
        counts=read_phases.setdefault(str(path),{});counts[phase]=counts.get(phase,0)+1
    def absolute(path):
        if isinstance(path,int):return None
        try:return Path(os.fsdecode(path)).resolve()
        except (TypeError,ValueError):return None
    def owned(path):return path is not None and path.is_relative_to(work)
    def sha_file(path):
        h=hashlib.sha256()
        with old_open(path,'rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
        return h.hexdigest()
    def view(path,write=False):
        full=absolute(path)
        if full is None or owned(full):return path
        if not full.is_relative_to(ROOT):
            if write:raise PermissionError('External generated-file path rejected:'+str(full))
            return path
        target=work/'overlay'/full.relative_to(ROOT)
        if write:
            if full.is_file() and str(full) not in original_write_guards:original_write_guards[str(full)]=sha_file(full)
            redirects[str(full)]=str(target);old_mkdir(target.parent,parents=True,exist_ok=True);return target
        return target if target.is_file() else path
    def is_write(mode):return isinstance(mode,str) and any(c in mode for c in 'wax+')
    def fopen(file,mode='r',*args,**kwargs):return old_open(view(file,is_write(mode)),mode,*args,**kwargs)
    def iopen(file,mode='r',*args,**kwargs):return old_io(view(file,is_write(mode)),mode,*args,**kwargs)
    def mkdir(path,mode=0o777,parents=False,exist_ok=False):return old_mkdir(view(path,True),mode=mode,parents=parents,exist_ok=exist_ok)
    def audit(event,args):
        if event=='open':
            full=absolute(args[0])
            if full is None:return
            flags=args[2] if len(args)>2 else 0
            writing=bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing and not owned(full):blocked.append(dict(event=event,path=str(full)));raise PermissionError('Unisolated open:'+str(full))
            if not writing and recording:
                if runtime_disc(full):blocked.append(dict(event='runtime_disc_read',path=str(full)));raise PermissionError('Runtime disc is not a derivation input:'+str(full))
                read_seen(full)
        elif event in ['os.mkdir','os.remove','os.rmdir','os.rename']:
            paths=[absolute(args[0])]+([absolute(args[1])] if event=='os.rename' else [])
            if any(not owned(x) for x in paths):blocked.append(dict(event=event,paths=list(map(str,paths))));raise PermissionError('Unisolated mutation:'+event)
        elif event=='subprocess.Popen':
            process_events.append(dict(executable=args[0],command=str(args[1]),cwd=str(args[2]),factory_validated=admitted_child))
            # Windows may expose executable=None after validating the argv list;
            # admit only the already-validated factory call,never a generic None.
            if not admitted_child or (args[0] is not None and absolute(args[0])!=ASSEMBLER.resolve()):raise PermissionError('Unregistered build child')
        elif event=='socket.connect':raise PermissionError('Network not needed for frozen derivation')
    def assembler(self,text,origin,folder,stem,symbols=False):
        if re.search(r'(?im)^\s*\.(?:open|create|close|include|incbin|loadelf|importobj|importlib)\b',text):raise PermissionError('Unexpected assembler file directive')
        dest=Path(view(folder,True));old_mkdir(dest,parents=True,exist_ok=True)
        return old_assemble(self,text,origin,dest,stem,symbols=symbols)
    def protected(path,text):return old_protected(Path(view(path,True)),text)
    def popen(args,*rest,**kwargs):
        nonlocal admitted_child
        assert isinstance(args,(list,tuple)) and absolute(args[0])==ASSEMBLER.resolve()
        assert owned(absolute(args[1])) and Path(args[1]).suffix=='.asm' and owned(absolute(kwargs['cwd']))
        child=dict(arguments=list(map(str,args)),cwd=str(kwargs['cwd']),only_pinned_assembler=True,spawned=False);children.append(child)
        admitted_child=True
        try:
            proc=old_popen(args,*rest,**kwargs);child.update(spawned=True,pid=proc.pid);return proc
        finally:admitted_child=False
    def font(*args,**kwargs):
        requested=absolute(args[0] if args else kwargs.get('font'))
        if requested and runtime_disc(requested):raise PermissionError('Runtime disc font input rejected')
        result=old_font(*args,**kwargs);path=absolute(getattr(result,'path',None))
        if path and path.is_file() and recording:read_seen(path)
        return result
    old_temp={k:os.environ.get(k) for k in ['TEMP','TMP']}
    for k in old_temp:os.environ[k]=str(work/'temp')
    builtins.open=fopen;io.open=iopen;Path.mkdir=mkdir;Profile.assemble=assembler
    catalog_survey034.protected_write=protected;subprocess.Popen=popen;ImageFont.truetype=font
    sys.addaudithook(audit);started=time.monotonic();failure=None;outputs=None;plan=None;comparison=[]
    try:
        from build_font_folder import derive
        cfg=json.loads((ROOT/'config/development_second_review_apply_20261030.json').read_text(encoding='utf8'))
        plan,outputs=derive('unicode_hangul_alias_fallback',diagnostic=cfg)
        project_modules=sorted({str(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).suffix=='.py' and Path(m.__file__).resolve().is_relative_to(ROOT)})
        phase='compare80'
        expected=json.loads((current/'artifact.json').read_text(encoding='utf8'))
        assert set(outputs)<=set(expected['files'])
        for rel,pin in expected['files'].items():
            raw=outputs[rel] if rel in outputs else (source/rel).read_bytes()
            actual=digest(raw);assert len(raw)==pin['size'] and actual==pin['sha256'],rel
            comparison.append(dict(path=rel,size=len(raw),sha256=actual,derived_in_memory=rel in outputs))
    except BaseException as exc:failure=dict(type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    finally:
        recording=False
        builtins.open=old_open;io.open=old_io;Path.mkdir=old_mkdir;Profile.assemble=old_assemble
        catalog_survey034.protected_write=old_protected;subprocess.Popen=old_popen;ImageFont.truetype=old_font
        for k,v in old_temp.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
    assert all(sha_file(Path(path))==pin for path,pin in original_write_guards.items())
    assert all(digest((ROOT/rel).read_bytes())==pin for rel,pin in guards.items())
    assert artifact('second_review_apply_20261030')==before;verify_tree(source)
    inputs=[]
    for filename,count in sorted(reads.items()):
        path=Path(filename)
        if owned(path) or not path.is_file():continue
        logical=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        runtime=path.is_relative_to(ROOT/'workspace/runtime')
        inputs.append(dict(path=logical,bytes=path.stat().st_size,sha256=sha_file(path),open_events=count,
            read_phases=read_phases[filename],
            runtime_disc_input=runtime and 'disc' in path.relative_to(ROOT/'workspace/runtime').parts,
            runtime_metadata_input=runtime and 'disc' not in path.relative_to(ROOT/'workspace/runtime').parts))
    expected_plan=json.loads((current/'expected_writes.json').read_text(encoding='utf8'))
    assert not any('/__pycache__/' in x['path'].replace('\\','/') and x['path'].startswith('scripts/') for x in inputs),'Use a fresh -X pycache_prefix for source-only import tracing.'
    module_pins=[dict(path=Path(x).relative_to(ROOT).as_posix(),sha256=sha_file(Path(x)),observed_loaded_project_module=True) for x in project_modules]
    if plan is not None:save_json(work/'derived_plan.json',plan)
    report=dict(status='PASS_ALL80_SOURCE_DERIVED_IN_MEMORY_EQUAL_CURRENT26' if failure is None else 'INPUT_TRACE_INCOMPLETE_PRESERVED_FAILURE',
        failure=failure,seconds=time.monotonic()-started,artifact_sha256=before,compared_files=comparison,
        original_inputs=inputs,redirected_generated_paths=redirects,existing_original_generated_files_preserved=original_write_guards,
        pinned_assembler_children=children,process_audit_events=process_events,blocked_mutations=blocked,expected_writes_structure_equal=plan==expected_plan,
        project_module_sources=module_pins,sys_pycache_prefix=sys.pycache_prefix,no_runtime_disc_inputs_admitted=True,
        explicit_builder_destination_assignment_equal=(dict(plan,disc_folder=expected_plan['disc_folder'])==expected_plan) if plan is not None else False,
        expected_writes_top_level_differences=sorted(set(plan or {})^set(expected_plan)) if plan is None else [k for k in set(plan)|set(expected_plan) if plan.get(k)!=expected_plan.get(k)],
        current80_original80_SSOT_config_and_existing_analysis_outputs_unchanged=True,
        scope='Python IO audit and original assembler output redirection,not an OS sandbox. Native font path explicitly observed through truetype;not every native library file read traced.',
        no_new_game_disc_or_ISO_written=True,no_emulator_or_savedata_or_deletion=True,release_eligible=False)
    save_json(work/'report.json',report)
    print(json.dumps(dict(status=report['status'],seconds=round(report['seconds'],2),compared=len(comparison),input_files=len(inputs),generated_paths=len(redirects),blocked=len(blocked),failure=failure and failure['error'],report=str((work/'report.json').relative_to(ROOT))),ensure_ascii=False))
    if failure:raise RuntimeError('Derivation trace incomplete;originals preserved. See isolated report.')

if __name__=='__main__':main()

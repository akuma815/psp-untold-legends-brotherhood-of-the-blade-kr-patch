"""Windows v1.0 applicator: registered original ISO -> verified Korean ISO."""
import argparse,hashlib,importlib.util,json,os,queue,struct,sys,tempfile,threading,uuid
from pathlib import Path,PurePosixPath
import release_iso

VERSION='1.0'
sys.dont_write_bytecode=True
ISO_SIZE=407601152
ISO_SHA='27bdf09512f138ed40f76f4c575fd9d373a95026355e6c8d97e300c2d4a0c621'
DEFAULT_PACKAGE=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent

def pin(p):
    h=hashlib.sha256();size=0
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);size+=len(b)
    return dict(size=size,sha256=h.hexdigest())
def read(p):return json.loads(p.read_text(encoding='utf8'))
def exists(p):return p.exists() or p.is_symlink() or p.is_junction()
def member(root,n):
    r=PurePosixPath(n)
    if not n or '\\' in n or ':' in n or r.is_absolute() or any(v in ['.','..',''] for v in n.split('/')):raise ValueError('안전하지 않은 파일 경로입니다.')
    p=root.joinpath(*r.parts)
    if not p.resolve().is_relative_to(root):raise ValueError('파일 경로가 지정 폴더를 벗어납니다.')
    t=p
    while t!=root:
        if t.is_symlink() or t.is_junction():raise ValueError('연결된 파일/폴더는 사용할 수 없습니다.')
        t=t.parent
    return p
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def check_package(package):
    m=read(package/'manifest.json')
    if m['version']!=VERSION or m['game_artifact_sha256']!='e8b97741db23f8a32d4eabe649fb7b58f18ea5c009fd9609692761cdb5f5b61a':raise ValueError('패치 버전 또는 게임 구성이 다릅니다.')
    for n,v in m['files'].items():
        if pin(member(package,n))!=v:raise ValueError('패치 파일이 손상되었습니다: '+n)
    data=package/'data';app=module('release_delta',data/'apply_folder_delta.py');gate=module('release_gate',data/'rebuild_scoped_review26.py')
    return m,app,gate
def iso_extents(raw):
    if raw[16*2048:16*2048+7]!=b'\x01CD001\x01':raise ValueError('지원하는 ISO9660 이미지가 아닙니다.')
    files={};visited=set()
    def both32(b,at):
        lo=struct.unpack_from('<I',b,at)[0];hi=struct.unpack_from('>I',b,at+4)[0]
        if lo!=hi:raise ValueError('ISO 주소 형식이 다릅니다.')
        return lo
    def walk(rec,parent):
        lba,n=both32(rec,2),both32(rec,10)
        if lba in visited or lba*2048+n>len(raw):raise ValueError('ISO 폴더 범위가 다릅니다.')
        visited.add(lba);block=raw[lba*2048:lba*2048+n];at=0
        while at<len(block):
            size=block[at]
            if not size:at=(at//2048+1)*2048;continue
            r=block[at:at+size];at+=size
            if size<34 or len(r)!=size or 33+r[32]>size:raise ValueError('ISO 레코드가 손상되었습니다.')
            name=r[33:33+r[32]]
            if name in [b'\0',b'\1']:continue
            name=name.decode('ascii').removesuffix(';1')
            if not name or name in ['.','..'] or any(c in name for c in '/\\:'):raise ValueError('ISO 파일 이름이 다릅니다.')
            path=parent+'/'+name if parent else name
            if r[25]&128:raise ValueError('분할 ISO 레코드는 지원하지 않습니다.')
            if r[25]&2:walk(r,path)
            else:
                off,n=both32(r,2)*2048,both32(r,10)
                if off+n>len(raw) or path in files:raise ValueError('ISO 파일 범위 또는 이름이 다릅니다.')
                files[path]=(off,n)
    walk(raw[16*2048+156:16*2048+190],'')
    return files
def remove_owned_work(work,allowed):
    """Remove only known files in the unique owned scratch tree, never recursively."""
    if not exists(work):return
    if work.is_symlink() or work.is_junction():raise ValueError('임시 작업 경로가 바뀌었습니다.')
    actual=[];dirs=[]
    for p in work.rglob('*'):
        if p.is_symlink() or p.is_junction():raise ValueError('임시 작업 경로에 연결 파일이 있습니다.')
        if p.is_file():
            n=p.relative_to(work).as_posix()
            if n not in allowed:raise ValueError('알 수 없는 임시 파일을 보존했습니다: '+str(p))
            actual.append(p)
        elif p.is_dir():dirs.append(p)
    for p in actual:p.unlink()
    for p in sorted(dirs,key=lambda x:len(x.parts),reverse=True):p.rmdir()
    work.rmdir()
def apply(package,source,output=None,verify_target=None,progress=lambda s:None):
    package=package.resolve();source=source.resolve();output=output.resolve() if output is not None else None
    if not source.is_file():raise ValueError('원본 추출 폴더 대신 등록된 원본 ISO 파일을 선택해 주세요.')
    if (output is None)==(verify_target is None):raise ValueError('새 ISO 파일 또는 기존 ISO 검사 중 하나를 지정해 주세요.')
    if output is not None:
        if exists(output):raise ValueError('출력 파일이 이미 있습니다. 새 ISO 파일 이름을 골라 주세요.')
        if output.suffix.lower()!='.iso':raise ValueError('출력 파일 확장자는 .iso여야 합니다.')
        if not output.parent.is_dir():raise ValueError('ISO를 저장할 상위 폴더가 없습니다.')
        if output.is_relative_to(package):raise ValueError('ISO는 패치 폴더 밖에 저장해 주세요.')
    elif not verify_target.is_file():raise ValueError('검사할 한글 ISO 파일이 없습니다.')
    progress('패치 파일 확인 중…');release,app,gate=check_package(package);data=package/'data';manifest=data/'manifest.json';decoder=package/'tools/xdelta3.exe'
    legacy=read(manifest);work=None;allowed=set();iso_pin=None
    try:
        if source.is_file():
            if source.stat().st_size!=ISO_SIZE:raise ValueError('지원하는 원본 ISO 크기가 아닙니다.')
            progress('원본 ISO 크기와 SHA-256 확인 중…');raw=source.read_bytes();iso_pin=dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if iso_pin!=dict(size=ISO_SIZE,sha256=ISO_SHA):raise ValueError('지원하는 원본 ISO가 아닙니다. 한국판 ULKS46015 v1.01의 지정 원본이 필요합니다.')
            extents=iso_extents(raw)
            if set(extents)!=set(legacy['source_files']):raise ValueError('원본 ISO의 파일 구성이 다릅니다.')
            for n,(off,size) in extents.items():
                if dict(size=size,sha256=hashlib.sha256(raw[off:off+size]).hexdigest())!=legacy['source_files'][n]:raise ValueError('원본 ISO 내용이 다릅니다: '+n)
            parent=output.parent if output is not None else None
            work=Path(tempfile.mkdtemp(prefix='.UntoldLegends_KR_',dir=parent)).resolve()
            if parent is not None and not work.is_relative_to(parent):raise ValueError('임시 경로가 출력 위치를 벗어났습니다.')
            original=work/'original';original.mkdir();allowed.update('original/'+n for n in extents)
            progress('검증된 원본 파일 준비 중…')
            for n,(off,size) in extents.items():
                p=member(original,n);p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(raw[off:off+size])
            del raw
        else:raise ValueError('원본 ISO를 선택해 주세요.')
        progress('원본 80파일과 승인된 문안·그래픽 범위 확인 중…')
        m,_,_=app.preflight(manifest,original,decoder,None);spec,approved,graphics=gate.metadata(data,m,app)
        if output is not None:
            if work is None:work=Path(tempfile.mkdtemp(prefix='.UntoldLegends_KR_',dir=output.parent)).resolve()
            stage=work/'result';allowed.update('result/'+n for n in m['target_files'])
            progress('한글패치 적용 중…');application=app.run(manifest,original,decoder,stage);target=stage
        else:
            progress('패치 차분 전체 검증 중…');application=app.run(manifest,original,decoder,None)
            packed=verify_target.read_bytes();entries,_=release_iso.parse(packed)
            if set(entries)!=set(m['target_files']):raise ValueError('한글 ISO의 80파일 구성이 다릅니다.')
            target=work/'result';target.mkdir();allowed.update('result/'+n for n in entries)
            for n,v in entries.items():
                b=packed[v['lba']*2048:v['lba']*2048+v['size']]
                if dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())!=m['target_files'][n]:raise ValueError('한글 ISO 파일이 다릅니다: '+n)
                p=member(target,n);p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:f.write(b)
            del packed
        progress('결과 80파일과 문안·지도·글꼴·쓰기 범위 검증 중…')
        scoped=gate.validate(data,original,target,m,app,spec,approved,graphics)
        if output is not None:
            progress('원본 구조를 유지한 한글 ISO 생성·검증 중…');iso_stage=work/'result.iso';allowed.add('result.iso')
            image=release_iso.build(source,stage,iso_stage,m['source_files'],m['target_files'])
            if release.get('ISO_artifact') and {k:image[k] for k in ['size','sha256']}!=release['ISO_artifact']:raise ValueError('예상한 한글 ISO와 다릅니다.')
            if exists(output):raise ValueError('출력 위치에 다른 파일이 생겨 덮어쓰지 않았습니다.')
            iso_stage.rename(output)
        else:
            image=dict(status='PASS_EXISTING_KOREAN_ISO_80',**pin(verify_target))
            if release.get('ISO_artifact') and {k:image[k] for k in ['size','sha256']}!=release['ISO_artifact']:raise ValueError('예상한 한글 ISO와 다릅니다.')
        return dict(status='PASS_KOREAN_PATCH_V1_0',version=VERSION,source_kind='ISO' if iso_pin else 'extracted_folder',
            source_ISO=iso_pin,artifact_sha256=m['artifact_sha256'],output=str(output) if output else None,
            complete_result_files=80,changed_files=11,unchanged_files=69,wordings=3571,map_tiles=25,loading_images=1,
            scoped_validation=scoped,application=application,ISO=image,ISO_created=output is not None,new_runtime_test=False,
            original_modified=False,source_saves_modified=False,public_release_created=False)
    finally:
        if work is not None:remove_owned_work(work,allowed)
def write_report(path,value,source=None,output=None,package=None):
    path=path.resolve()
    if exists(path):raise ValueError('결과 기록 파일이 이미 있습니다.')
    for protected in [source if source is not None and source.is_dir() else None,output,package]:
        if protected is not None and path.is_relative_to(protected.resolve()):raise ValueError('기록 파일은 게임/패치 폴더 밖에 지정해 주세요.')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def gui(package,initial=None):
    import tkinter as tk
    from tkinter import ttk,filedialog,messagebox
    root=tk.Tk();root.title('언톨드 레전드 한글패치 v1.0 · ISO');root.geometry('660x350');root.resizable(False,False)
    source=tk.StringVar(value=str(initial or ''));output=tk.StringVar();status=tk.StringVar(value='원본 ISO를 선택해 주세요.');events=queue.Queue();busy=[False]
    frame=ttk.Frame(root,padding=18);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Untold Legends · 한글패치 v1.0',font=('맑은 고딕',15,'bold')).pack(anchor='w')
    ttk.Label(frame,text='한국판 ULKS46015 v1.01 전용 · 원본을 보존하고 새 한글 ISO를 만듭니다.').pack(anchor='w',pady=(6,14))
    ttk.Label(frame,text='원본 ISO').pack(anchor='w');ttk.Entry(frame,textvariable=source).pack(fill='x')
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=7)
    def select():
        p=filedialog.askopenfilename(title='원본 ISO 선택',filetypes=[('PSP ISO','*.iso'),('모든 파일','*')])
        if p:
            source.set(p);output.set(str(Path(p).with_name(Path(p).stem+'_Korean_v1.0.iso')))
    def save_as():
        p=filedialog.asksaveasfilename(title='새 한글 ISO 저장 위치',defaultextension='.iso',filetypes=[('PSP ISO','*.iso')])
        if p:output.set(p)
    ttk.Button(buttons,text='ISO 선택',command=select).pack(side='left');ttk.Button(buttons,text='출력 위치',command=save_as).pack(side='left',padx=7)
    ttk.Label(frame,text='새 한글 ISO 파일 (기존 파일은 덮어쓰지 않습니다)').pack(anchor='w');ttk.Entry(frame,textvariable=output).pack(fill='x')
    ttk.Label(frame,textvariable=status,wraplength=620).pack(anchor='w',pady=13)
    def worker(s,o):
        try:
            result=apply(package,s,o,progress=lambda s:events.put(('status',s)))
            report=o.parent/('UntoldLegends_apply_'+uuid.uuid4().hex[:12]+'.json');write_report(report,result,package=package,source=s,output=o)
            events.put(('done',str(o)))
        except Exception as e:events.put(('error',str(e)))
    def start():
        if busy[0]:return
        if not source.get() or not output.get():messagebox.showerror('경로 확인','원본과 새 ISO 경로를 지정해 주세요.',parent=root);return
        busy[0]=True;go.config(state='disabled');threading.Thread(target=worker,args=(Path(source.get()),Path(output.get())),daemon=True).start()
    go=ttk.Button(frame,text='한글패치 적용',command=start);go.pack(anchor='e')
    def poll():
        while not events.empty():
            kind,value=events.get()
            if kind=='status':status.set(value)
            else:
                busy[0]=False;go.config(state='normal')
                if kind=='done':status.set('적용 완료');messagebox.showinfo('완료','PPSSPP에서 다음 ISO 파일을 열어 주세요.\n\n'+value+'\n\n완전히 재실행한 뒤 게임의 일반 불러오기를 사용하세요.',parent=root)
                else:status.set('적용하지 못했습니다.');messagebox.showerror('적용 실패',value,parent=root)
        root.after(100,poll)
    def close():
        if busy[0]:messagebox.showinfo('적용 중','적용을 마칠 때까지 기다려 주세요.',parent=root)
        else:root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);root.after(100,poll)
    if initial:output.set(str(initial.with_name(initial.stem+'_Korean_v1.0.iso')))
    root.mainloop()
def main():
    p=argparse.ArgumentParser();p.add_argument('input',nargs='?',type=Path);p.add_argument('--source',type=Path);p.add_argument('--package',type=Path,default=DEFAULT_PACKAGE)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--output',type=Path);mode.add_argument('--verify-target',type=Path)
    p.add_argument('--report',type=Path);p.add_argument('--self-test',action='store_true');p.add_argument('--gui',action='store_true');a=p.parse_args()
    package=a.package.resolve();source=a.source or a.input
    try:
        if a.report is not None and exists(a.report):raise ValueError('기록 파일이 이미 있습니다.')
        if a.self_test:
            m,_,_=check_package(package)
            import tkinter
            result=dict(status='PASS_V1_0_PACKAGE_SELFTEST',version=VERSION,files_verified=len(m['files']),tkinter_available=True,interactive_GUI_tested=False)
        elif a.gui or source is None or a.input is not None and a.source is None and a.output is None and a.verify_target is None:gui(package,source);return 0
        else:
            output=a.output or (None if a.verify_target else source.resolve().with_name(source.stem+'_Korean_v1.0.iso'))
            if a.report is not None:
                report=a.report.resolve()
                if report.is_relative_to(package) or source.is_dir() and report.is_relative_to(source.resolve()) or output is not None and report.is_relative_to(output.resolve()):raise ValueError('기록 파일은 게임/패치 폴더 밖에 지정해 주세요.')
            result=apply(package,source,output,a.verify_target)
        if a.report:write_report(a.report,result,source,a.output,package)
        if sys.stdout is not None:print(json.dumps(result,ensure_ascii=True))
        return 0
    except Exception as e:
        result=dict(status='REJECTED_V1_0_APPLICATION',version=VERSION,error=str(e))
        if a.report and not exists(a.report):
            try:write_report(a.report,result,source,a.output,package)
            except Exception:pass
        if sys.stderr is not None:print(json.dumps(result,ensure_ascii=True),file=sys.stderr)
        if source is None:
            try:
                from tkinter import messagebox
                messagebox.showerror('한글패치 오류',str(e))
            except Exception:pass
        return 2
if __name__=='__main__':sys.exit(main())

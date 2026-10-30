"""Visible user-controlled PPSSPP, verified map-repair27 folder, persistent private profile."""
import argparse,json,socket,subprocess,time,configparser,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
import psutil
from survey import ROOT,digest,save_json
from book_role_runtime_20261024 import artifact
from psp_folder import external_snapshot
from ppsspp_analog109 import NativeInput,process_identity

EMULATOR=Path('H:/ppsspp/PPSSPPWindows64.exe')
PROFILE=ROOT/'workspace/manual_play_20261024/profile'
CONTENT=ROOT/'workspace/runtime/map_crisp27_20261030/disc'
EXPECTED='e8b97741db23f8a32d4eabe649fb7b58f18ea5c009fd9609692761cdb5f5b61a'

def launch():
    assert EMULATOR.is_file() and artifact('map_crisp27_20261030')==EXPECTED
    current=PROFILE.parent/'current.json'
    if current.exists():
        old=json.loads(current.read_text(encoding='utf8'))
        try:
            if process_identity(old['pid'])==old['start_identity'] and Path(psutil.Process(old['pid']).exe()).resolve()==EMULATOR.resolve():
                print('Manual PPSSPP is already running;PID',old['pid']);return
        except (psutil.NoSuchProcess,OSError):pass
    i=1
    while (ROOT/f'qa/runtime/20261024_manual_play_gui_attempt{i:02d}').exists():i+=1
    q=ROOT/f'qa/runtime/20261024_manual_play_gui_attempt{i:02d}';q.mkdir(parents=True)
    save_json(q/'external_before.json',external_snapshot())
    hidden=subprocess.STARTUPINFO();hidden.dwFlags|=subprocess.STARTF_USESHOWWINDOW;hidden.wShowWindow=0
    help_run=subprocess.run([str(EMULATOR),'--help'],capture_output=True,startupinfo=hidden,creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
    help_text=help_run.stdout.decode('utf8',errors='strict').replace('\r','')
    (q/'emulator_help.txt').write_text(help_text,encoding='utf8')
    assert help_run.returncode==0 and all(x in help_text for x in ['--memstick','--nand','--windowed','--debugger']),help_text
    version_run=subprocess.run([str(EMULATOR),'--version'],capture_output=True,startupinfo=hidden,creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
    version_text=version_run.stdout.decode('utf8',errors='strict');assert version_run.returncode==0
    commit=re.search(r'g([0-9a-f]{7,40})',version_text);assert commit,version_text
    url=f'https://raw.githubusercontent.com/hrydgard/ppsspp/{commit[1]}/Core/CmdLine.cpp'
    source=urllib.request.urlopen(url,timeout=15).read();text=source.decode('utf8')
    assert 'configOption = "--config="' in text and 'controlsOption = "--controlconfig="' in text
    (q/'PPSSPP_CmdLine.cpp').write_bytes(source)
    save_json(q/'cli_source.json',dict(installed_version=version_text.strip(),source_url=url,sha256=digest(source),hidden_config_options_verified=True))
    PROFILE.mkdir(parents=True,exist_ok=True)
    for d in ['memstick','nand']:(PROFILE/d).mkdir(exist_ok=True)
    ini=PROFILE/'ppsspp.ini';controls=PROFILE/'controls.ini'
    if not ini.exists():
        ini.write_text('[General]\nFirstRun = False\nLanguage = ko_KR\nCheckForNewVersion = False\nRemoteDebuggerLocal = True\nAutoSaveLoadSymbols = False\n[Graphics]\nGraphicsBackend = 2\nInternalResolution = 2\n[Sound]\nEnableSound = True\n[SystemParam]\nGameLanguage = 9\n',encoding='utf8')
    if not controls.exists():
        choices=[EMULATOR.parent/'memstick/PSP/SYSTEM/controls.ini',Path.home()/'Documents/PPSSPP/PSP/SYSTEM/controls.ini']
        existing=next((p for p in choices if p.is_file()),None)
        controls.write_bytes(existing.read_bytes() if existing else b'[ControlMapping]\n')
        save_json(PROFILE.parent/'control_source.json',dict(source=str(existing) if existing else 'PPSSPP default mappings',copy_sha256=digest(controls.read_bytes())))
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    args=[str(EMULATOR),f'--config={ini}',f'--controlconfig={controls}',f'--memstick={PROFILE/"memstick"}',f'--nand={PROFILE/"nand"}',f'--debugger={port}',f'--log={q/"ppsspp.log"}','--windowed',str(CONTENT)]
    visible=subprocess.STARTUPINFO();visible.dwFlags|=subprocess.STARTF_USESHOWWINDOW;visible.wShowWindow=1
    with (q/'stdout.log').open('wb') as out,(q/'stderr.log').open('wb') as err:
        p=subprocess.Popen(args,cwd=q,stdout=out,stderr=err,startupinfo=visible)
    record=dict(status='MANUAL_VISIBLE_GUI_STARTED_USER_OWNS_INPUT',pid=p.pid,start_identity=process_identity(p.pid),
        executable=str(EMULATOR),executable_sha256=digest(EMULATOR.read_bytes()),port=port,arguments=args,
        artifact_name='map_crisp27_20261030',artifact_sha256=EXPECTED,content=str(CONTENT),profile=str(PROFILE),
        started_utc=datetime.now(timezone.utc).isoformat(),qa_path=q.relative_to(ROOT).as_posix(),
        automated_inputs=0,native_memory_state_or_execution_controls=0,old_headless_state_auto_imported=False,
        rationale='Installed interactive GUI revision differs from controlled headless56c694d;start normal cold game instead of auto-importing a cross-revision state.',
        isolated_game_saves_persist=True,ISO_created=False,leave_running_for_user=True)
    save_json(q/'session.json',record);save_json(current,record)
    native=None
    try:
        for _ in range(100):
            if p.poll() is not None:raise RuntimeError('Visible PPSSPP exited:'+str(p.returncode))
            try:native=NativeInput(port);break
            except (OSError,ConnectionError):time.sleep(.1)
        assert native is not None,'Debugger not available;inspect session before another launch'
        record['version']=native.call('version',name='Untold user manual play')
        for _ in range(100):
            game=native.call('game.status')
            if (game.get('game') or {}).get('id')=='ULKS46015':break
            time.sleep(.1)
        assert (game.get('game') or {}).get('id')=='ULKS46015',game
        record['game_status']=game;record['status']='VERIFIED_VISIBLE_GUI_CONTENT_USER_OWNS_INPUT'
    finally:
        if native is not None:native.close()
        save_json(q/'session.json',record);save_json(current,record)
    save_json(q/'external_after_launch.json',external_snapshot())
    assert json.loads((q/'external_before.json').read_text(encoding='utf8'))==json.loads((q/'external_after_launch.json').read_text(encoding='utf8'))
    print(json.dumps(dict(pid=p.pid,profile=str(PROFILE),content=str(CONTENT),version=record['version'],status=record['status']),ensure_ascii=False))

def verify_current():
    current=PROFILE.parent/'current.json';record=json.loads(current.read_text(encoding='utf8'))
    assert process_identity(record['pid'])==record['start_identity']
    assert Path(psutil.Process(record['pid']).exe()).resolve()==EMULATOR.resolve()
    native=NativeInput(record['port'])
    try:
        game=native.call('game.status');version=native.call('version',name='Untold manual verify')
    finally:native.close()
    assert (game.get('game') or {}).get('id')=='ULKS46015',game
    q=ROOT/record['qa_path'];assert not (q/'verified_game_status.json').exists()
    external=external_snapshot();before=json.loads((q/'external_before.json').read_text(encoding='utf8'));assert external==before
    save_json(q/'verified_game_status.json',dict(game=game,version=version,external_unchanged_at_handoff=True,
        automatic_input_or_state_execution_control=0,process_identity=record['start_identity']))
    save_json(q/'external_after_launch.json',external)
    record.update(status='VERIFIED_VISIBLE_GUI_CONTENT_USER_OWNS_INPUT',game_status=game,version=version)
    save_json(current,record)
    print(json.dumps(dict(status=record['status'],pid=record['pid'],game=game,version=version,profile=str(PROFILE)),ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verify-current',action='store_true');a=p.parse_args()
    verify_current() if a.verify_current else launch()

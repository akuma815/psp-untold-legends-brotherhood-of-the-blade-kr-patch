"""Historical ISO-era debugger client. New-launch CLI retired; next workflow is folder based."""
import argparse
import base64
import hashlib
import json
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import websocket

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT/'qa/runtime/20261016_003'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

class Client:
    def __init__(self):
        self.session = json.loads((SESSION/'session.json').read_text(encoding='utf-8'))
        self.ws = websocket.create_connection(f"ws://127.0.0.1:{self.session['port']}/debugger",
            subprotocols=['debugger.ppsspp.org'], timeout=15, http_proxy_host=None)
    def close(self):
        self.ws.close()
    def call(self, event, **params):
        request = {'event':event, **params}
        self.ws.send(json.dumps(request))
        deadline = time.monotonic()+20
        while time.monotonic()<deadline:
            reply = json.loads(self.ws.recv())
            if reply.get('event')=='error':
                self.log(request,reply)
                raise RuntimeError(reply)
            # A breakpoint may stop the CPU again before a resume broadcast can be observed.
            if reply.get('event')==event or (event=='cpu.resume' and reply.get('event')=='cpu.stepping'):
                self.log(request,reply)
                return reply
        raise TimeoutError(event)
    def log(self, request, reply):
        summary = {k:(f'<{len(v)} characters>' if k in ('uri','base64') else v) for k,v in reply.items()}
        with (SESSION/'requests.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(), 'request':request,
                                'response':summary},ensure_ascii=False)+'\n')
    def pause(self):
        state = self.call('cpu.status')
        return state if state.get('stepping') else self.call('cpu.stepping')
    def resume(self):
        state = self.call('cpu.status')
        return self.call('cpu.resume') if state.get('stepping') else state
    def read(self, address, size):
        reply = self.call('memory.read', address=address, size=size, replacements=False)
        data = base64.b64decode(reply['base64'])
        if len(data)!=size:
            raise ValueError('Memory response size mismatch')
        return data
    def screenshot(self, name):
        self.pause()
        reply = self.call('gpu.buffer.screenshot',type='uri')
        data = base64.b64decode(reply['uri'].split(',',1)[1])
        path = SESSION/(name+'.png')
        if path.exists():
            raise FileExistsError(path)
        path.write_bytes(data)
        save(SESSION/(name+'.json'), {k:v for k,v in reply.items() if k!='uri'} |
             {'sha256':sha(path),'game':self.call('game.status'),'cpu':self.call('cpu.status')})
        return path

def launch(emulator, gui=False, artifact_manifest=None):
    SESSION.mkdir(parents=True,exist_ok=True)
    session_file=SESSION/'session.json'
    if session_file.exists():
        raise FileExistsError('Session already exists; inspect before relaunch')
    source=json.loads((ROOT/'manifests/source.json').read_text(encoding='utf-8'))
    iso=ROOT/source['path']
    assert iso.stat().st_size==source['size'] and sha(iso)==source['sha256']
    artifact=None
    if artifact_manifest is not None:
        artifact=json.loads(artifact_manifest.read_text(encoding='utf-8'))
        assert artifact['original_source_sha256']==source['sha256']
        assert artifact['policy']=='development_poc_non_distributable' and artifact['release_eligible'] is False
        iso=(ROOT/artifact['iso_path']).resolve()
        assert (ROOT/'build').resolve() in iso.parents
        assert iso.stat().st_size==artifact['iso_size'] and sha(iso)==artifact['iso_sha256']
    portable=SESSION/'portable'
    portable.mkdir()
    target=portable/emulator.name
    shutil.copy2(emulator,target)
    # Windows headless uses exePath/memstick; copying exe/assets isolates it without env overrides.
    shutil.copytree(emulator.parent/'assets', portable/'assets')
    for path in emulator.parent.glob('*.dll'):
        shutil.copy2(path,portable/path.name)
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    if gui:
        profile=portable/'memstick/PSP/SYSTEM'
        profile.mkdir(parents=True,exist_ok=True)
        ini=profile/'ppsspp.ini'
        ini.write_text('[General]\nFirstRun = False\nLanguage = en_US\nRemoteDebuggerOnStartup = True\n'
            f'RemoteISOPort = {port}\nRemoteDebuggerLocal = True\nCheckForNewVersion = False\n'
            '[Graphics]\nGraphicsBackend = 2\nInternalResolution = 1\n[Sound]\nEnableSound = False\n'
            '[SystemParam]\nGameLanguage = 1\n',encoding='utf-8')
        args=[str(target),f'--config={ini}',str(iso)]
    else:
        args=[str(target),f'--debugger={port}','--graphics=software','-i','-l',str(iso)]
    startup=subprocess.STARTUPINFO()
    startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow=0
    with (SESSION/'stdout.log').open('wb') as out,(SESSION/'stderr.log').open('wb') as err:
        proc=subprocess.Popen(args,cwd=portable,stdout=out,stderr=err,
            creationflags=subprocess.CREATE_NO_WINDOW,startupinfo=startup)
    meta={'pid':proc.pid,'port':port,'arguments':args,'source_sha256':source['sha256'],
          'active_content_sha256':sha(iso),'artifact_manifest':str(artifact_manifest) if artifact else None,
          'emulator_source':str(emulator),'emulator_sha256':sha(target),
          'profile':str(portable/'memstick'),'started_utc':datetime.now(timezone.utc).isoformat(),
          'debugger':'stock PPSSPP WebSocket; emucap launch unavailable',
          'cpu_backend':'GUI default JIT' if gui else 'plain interpreter for stock headless breakpoint invalidation behavior',
          'frontend':'Windows GUI hidden' if gui else 'headless'}
    save(session_file,meta)
    for _ in range(80):
        if proc.poll() is not None:
            raise RuntimeError(f'Emulator exited {proc.returncode}; see stderr.log')
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=.2):break
        except OSError:time.sleep(.1)
    else:raise TimeoutError('Debugger port unavailable')
    client=Client()
    try:
        meta['version']=client.call('version',name='Untold Legends localization QA')
        meta['initial_game_status']=client.call('game.status')
        meta['initial_cpu_status']=client.call('cpu.status')
        save(session_file,meta)
        print(json.dumps(meta,ensure_ascii=True))
    finally:client.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=['launch','status','pause','resume','screenshot'])
    parser.add_argument('--emulator',type=Path,default=Path('H:/ppsspp/PPSSPPHeadless.exe'))
    parser.add_argument('--name',default='capture')
    parser.add_argument('--session',default='20261016_003')
    parser.add_argument('--gui',action='store_true')
    parser.add_argument('--artifact-manifest',type=Path)
    args=parser.parse_args()
    if Path(args.session).name!=args.session:
        raise ValueError('Session must be a single safe directory name')
    SESSION=ROOT/'qa/runtime'/args.session
    if args.operation=='launch':
        raise SystemExit('Historical ISO/portable-copy launcher retired by user instruction. Future PPSSPP tests must launch a folder with separate project settings.')
    else:
        c=Client()
        try:
            if args.operation=='status':print(json.dumps([c.call('game.status'),c.call('cpu.status')]))
            elif args.operation=='pause':print(json.dumps(c.pause()))
            elif args.operation=='resume':print(json.dumps(c.resume()))
            else:print(c.screenshot(args.name))
        finally:c.close()

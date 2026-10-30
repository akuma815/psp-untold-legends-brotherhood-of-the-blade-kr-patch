"""Verified source-folder boot using the installed PPSSPP; never writes an ISO.

The reusable workspace disc is a separate copy (not hardlinks). This baseline
launcher refuses modified inputs; future patches need their own write manifest.
"""
import argparse
import ctypes
import hashlib
import json
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import psp_debugger as debug

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / 'workspace/runtime/disc'
EMULATOR = Path('H:/ppsspp/PPSSPPWindows64.exe')
EMU_SHA = '56d27a191abbadf02927021ea2bc1b0bf0bb82fbbdb4a9bc6fa0b08c727ab01a'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def entries():
    return json.loads((ROOT / 'manifests/iso_inventory.json').read_text(encoding='utf-8'))['files']


def verify_tree(tree):
    expected = {f['path']: f for f in entries()}
    actual = {p.relative_to(tree).as_posix(): p for p in tree.rglob('*') if p.is_file()}
    if set(actual) != set(expected):
        raise ValueError(f'Unexpected file set in {tree}')
    for name, item in expected.items():
        path = actual[name]
        if path.is_symlink() or path.stat().st_size != item['size'] or sha(path) != item['sha256']:
            raise ValueError(f'Baseline hash mismatch: {path}')
    return len(actual)


def prepare():
    source = ROOT / 'extracted/disc'
    verify_tree(source)
    for item in entries():
        dest = DISC / item['path']
        if dest.exists():
            if sha(dest) != item['sha256']:
                raise ValueError(f'Refusing to overwrite existing changed file: {dest}')
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / item['path'], dest)
        if (source / item['path']).stat().st_ino == dest.stat().st_ino:
            raise ValueError('Hardlinked original is forbidden')
    return verify_tree(DISC)


def external_snapshot():
    # Scope to installation assets, settings and saves, excluding game libraries.
    roots = [EMULATOR.parent / 'assets']
    direct = [EMULATOR.parent]
    for base in [EMULATOR.parent / 'memstick', Path.home() / 'Documents/PPSSPP']:
        roots.append(base / 'PSP/SAVEDATA')
        direct.extend([base, base / 'PSP/SYSTEM'])
    result = {}
    for folder in direct:
        if folder.exists():
            for path in folder.iterdir():
                if path.is_file():
                    result[str(path)] = {'size': path.stat().st_size, 'sha256': sha(path)}
    for root in roots:
        if root.exists():
            for path in root.rglob('*'):
                if path.is_file():
                    result[str(path)] = {'size': path.stat().st_size, 'sha256': sha(path)}
    return result


def startup():
    info = subprocess.STARTUPINFO()
    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    info.wShowWindow = 0
    return info


def launch(session):
    run = ROOT / 'qa/runtime' / session
    if run.exists():
        raise FileExistsError('Use a new session name; existing evidence is preserved')
    if sha(EMULATOR) != EMU_SHA:
        raise ValueError('Installed emulator changed; revalidate version/options first')
    source = json.loads((ROOT / 'manifests/source.json').read_text(encoding='utf-8'))
    if sha(ROOT / source['path']) != source['sha256']:
        raise ValueError('Original ISO identity mismatch')
    count = prepare()
    run.mkdir(parents=True)
    save(run / 'external_before.json', external_snapshot())
    help_run = subprocess.run([str(EMULATOR), '--help'], capture_output=True,
                              startupinfo=startup(), creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
    help_text = help_run.stdout.decode('utf-8').replace('\r', '')
    (run / 'emulator_help.txt').write_text(help_text, encoding='utf-8')
    assert help_run.returncode == 0 and '--memstick' in help_text and '--nand' in help_text
    profile = run / 'profile'
    memstick = profile / 'memstick'
    nand = profile / 'nand'
    memstick.mkdir(parents=True)
    nand.mkdir()
    ini = profile / 'ppsspp.ini'
    controls = profile / 'controls.ini'
    controls.write_text('[ControlMapping]\n', encoding='utf-8')
    ini.write_text('[General]\nFirstRun = False\nLanguage = en_US\nRemoteDebuggerLocal = True\n'
                   'CheckForNewVersion = False\nEnableLogging = True\nAutoSaveLoadSymbols = False\n'
                   '[Graphics]\nGraphicsBackend = 2\nInternalResolution = 1\n'
                   '[Sound]\nEnableSound = False\n[SystemParam]\nGameLanguage = 1\n', encoding='utf-8')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    args = [str(EMULATOR), f'--config={ini}', f'--controlconfig={controls}',
            f'--memstick={memstick}', f'--nand={nand}', f'--debugger={port}',
            f'--log={run / "ppsspp.log"}', '--windowed', str(DISC)]
    with (run / 'stdout.log').open('wb') as out, (run / 'stderr.log').open('wb') as err:
        proc = subprocess.Popen(args, cwd=run, stdout=out, stderr=err,
                                startupinfo=startup(), creationflags=subprocess.CREATE_NO_WINDOW)
    meta = {'pid': proc.pid, 'port': port, 'arguments': args, 'source_sha256': source['sha256'],
            'emulator_source': str(EMULATOR), 'emulator_sha256': EMU_SHA,
            'disc_folder': str(DISC), 'baseline_verified_files': count,
            'profile': str(profile), 'started_utc': datetime.now(timezone.utc).isoformat(),
            'iso_created': False, 'emulator_copied': False, 'memory_writes': False,
            'savestate_loaded': False, 'claim': 'original-content extracted-folder cold boot'}
    save(run / 'session.json', meta)
    for _ in range(150):
        if proc.poll() is not None:
            raise RuntimeError(f'PPSSPP exited: {proc.returncode}; inspect session logs')
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=.2):
                break
        except OSError:
            time.sleep(.1)
    else:
        raise TimeoutError('Debugger port did not open; inspect process before retry')
    debug.SESSION = run
    client = debug.Client()
    try:
        meta['version'] = client.call('version', name='Untold Legends folder QA')
        for _ in range(100):
            status = client.call('game.status')
            if status.get('game'):
                break
            time.sleep(.1)
        assert status['game']['id'] == 'ULKS46015'
        meta['initial_game_status'] = status
        save(run / 'session.json', meta)
    finally:
        client.close()
    print(json.dumps(meta, ensure_ascii=True))


def stop(session):
    run = ROOT / 'qa/runtime' / session
    meta = json.loads((run / 'session.json').read_text(encoding='utf-8'))
    # Gracefully close only the recorded PID's windows and wait for actual exit.
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def close_window(hwnd, _):
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(ctypes.c_void_p(hwnd), ctypes.byref(pid))
        if pid.value == meta['pid']:
            user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)
        return True
    user32.EnumWindows(callback_type(close_window), 0)
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = ctypes.c_void_p
    handle = kernel32.OpenProcess(0x00100000, False, meta['pid'])
    if handle:
        try:
            if kernel32.WaitForSingleObject(ctypes.c_void_p(handle), 15000) != 0:
                raise TimeoutError('Emulator has not exited; do not finalize audit')
        finally:
            kernel32.CloseHandle(ctypes.c_void_p(handle))
    after = external_snapshot()
    save(run / 'external_after.json', after)
    before = json.loads((run / 'external_before.json').read_text(encoding='utf-8'))
    changes = [p for p in before.keys() | after.keys() if before.get(p) != after.get(p)]
    result = {'process_exited': True, 'shared_install_and_default_profile_changes': changes,
              'source_extract_verified_files': verify_tree(ROOT / 'extracted/disc'),
              'workspace_disc_verified_files': verify_tree(DISC),
              'finished_utc': datetime.now(timezone.utc).isoformat()}
    save(run / 'stop_audit.json', result)
    if changes:
        raise ValueError(f'Unexpected external profile changes: {changes}')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'launch', 'stop', 'verify'])
    parser.add_argument('--session')
    args = parser.parse_args()
    if args.operation in ('launch', 'stop') and not args.session:
        parser.error('--session is required for launch/stop; choose a fresh name for launch')
    if args.session and (Path(args.session).name != args.session or args.session in ('.', '..')):
        raise ValueError('Session must be one safe directory name')
    if args.operation == 'prepare':
        print(json.dumps({'verified_files': prepare(), 'disc': str(DISC)}))
    elif args.operation == 'verify':
        print(json.dumps({'verified_files': verify_tree(DISC)}))
    elif args.operation == 'launch':
        launch(args.session)
    else:
        stop(args.session)

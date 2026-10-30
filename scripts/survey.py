"""Read-only ISO9660 survey for the registered local source; Python 3.12 stdlib."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def iso_files(data):
    pvd = data[16*2048:17*2048]
    if pvd[:7] != b'\x01CD001\x01':
        raise ValueError('Unsupported primary volume descriptor')
    if struct.unpack_from('<H', pvd, 128)[0] != 2048:
        raise ValueError('Unsupported logical block size')
    files, visited = [], set()
    def both32(record, offset):
        a, b = struct.unpack_from('<I', record, offset)[0], struct.unpack_from('>I', record, offset+4)[0]
        if a != b:
            raise ValueError('ISO dual-endian field mismatch')
        return a
    def walk(record, parent):
        lba, size = both32(record, 2), both32(record, 10)
        if lba in visited:
            raise ValueError('Directory cycle')
        visited.add(lba)
        start = lba*2048
        if start+size > len(data):
            raise ValueError('Directory outside ISO')
        block, pos = data[start:start+size], 0
        while pos < size:
            n = block[pos]
            if not n:
                pos = (pos//2048+1)*2048
                continue
            rec = block[pos:pos+n]
            if n < 34 or len(rec) != n or 33+rec[32] > n:
                raise ValueError('Truncated directory record')
            pos += n
            name = rec[33:33+rec[32]]
            if name in (b'\0', b'\1'):
                continue
            name = name.decode('ascii').removesuffix(';1')
            if name in ('', '.', '..') or any(c in name for c in '/\\:'):
                raise ValueError('Unsafe ISO path')
            path = parent/name
            if rec[25] & 128:
                raise ValueError('Multi-extent record unsupported')
            if rec[25] & 2:
                walk(rec, path)
            else:
                extent, length = both32(rec, 2), both32(rec, 10)
                if extent*2048+length > len(data):
                    raise ValueError('File outside ISO')
                payload = data[extent*2048:extent*2048+length]
                files.append({'path':path.as_posix(), 'lba':extent, 'iso_offset':extent*2048,
                              'size':length, 'sha256':digest(payload), 'magic_hex':payload[:16].hex()})
    walk(pvd[156:156+pvd[156]], Path())
    if len({f['path'] for f in files}) != len(files):
        raise ValueError('Duplicate paths')
    return files

def sfo(data):
    magic, version, keys, values, count = struct.unpack_from('<5I', data)
    if magic != 0x46535000:
        raise ValueError('Invalid SFO')
    result = {}
    for i in range(count):
        key, fmt, length, capacity, offset = struct.unpack_from('<HHIII', data, 20+16*i)
        name = data[keys+key:].split(b'\0', 1)[0].decode('utf-8')
        raw = data[values+offset:values+offset+length]
        result[name] = int.from_bytes(raw, 'little') if fmt == 0x404 else raw.rstrip(b'\0').decode('utf-8')
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--extract', action='store_true')
    parser.add_argument('--verify-source-only', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'manifests/source.json').read_text(encoding='utf-8'))
    source = args.source or ROOT/manifest['path']
    data = source.read_bytes()
    if len(data) != manifest['size'] or digest(data) != manifest['sha256']:
        raise ValueError('Unregistered source: size/SHA-256 mismatch')
    if args.verify_source_only:
        print(json.dumps({'source_verified':True, 'size':len(data), 'sha256':digest(data)}))
        return
    files = iso_files(data)
    for f in files:
        payload = data[f['iso_offset']:f['iso_offset']+f['size']]
        target = ROOT/'extracted/disc'/f['path']
        if args.extract:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and digest(target.read_bytes()) != f['sha256']:
                raise ValueError('Refusing to overwrite changed extraction: '+f['path'])
            if not target.exists():
                target.write_bytes(payload)
        if not target.exists() or digest(target.read_bytes()) != f['sha256']:
            raise ValueError('Extracted payload mismatch: '+f['path'])
    metadata = sfo((ROOT/'extracted/disc/PSP_GAME/PARAM.SFO').read_bytes())
    save_json(ROOT/'manifests/iso_inventory.json', {'schema_version':1, 'source_sha256':manifest['sha256'], 'files':files})
    save_json(ROOT/'qa/reports/source_and_extraction.json', {
        'schema_version':1, 'source_sha256':digest(data), 'source_size':len(data),
        'file_count':len(files), 'all_file_payload_hashes_match':True, 'param_sfo':metadata,
        'validation_class':'static extraction only', 'iso_rebuild_tested':False, 'runtime_tested':False})
    print(json.dumps({'file_count':len(files), 'source_verified':True, 'all_extracted_hashes_match':True, 'param_sfo':metadata}, ensure_ascii=True))

if __name__ == '__main__':
    main()

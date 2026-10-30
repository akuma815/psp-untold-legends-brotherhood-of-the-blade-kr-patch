"""Static candidate parsing and lossless checks; does not produce a game patch."""
import collections
import json
import re
import struct
import sys
from pathlib import Path
from survey import ROOT, digest, save_json

DISC = ROOT/'extracted/disc'
USR = DISC/'PSP_GAME/USRDIR'

def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in records), encoding='utf-8')

def string_record(asset, key, raw, offset, encoding):
    try:
        text = raw.decode(encoding, errors='strict')
    except UnicodeDecodeError:
        if encoding != 'utf-8':
            raise
        # Byte-preserving analysis view only, not a claim about the game decoder.
        encoding = 'latin-1'
        text = raw.decode(encoding, errors='strict')
    assert text.encode(encoding, errors='strict') == raw
    return {'id':f'{asset}:{key}', 'source_asset':asset, 'key':key,
            'offset':offset, 'byte_length':len(raw), 'encoding_candidate':encoding,
            'source_text':text, 'source_hex':raw.hex(), 'source_sha256':digest(raw),
            'token_candidates':re.findall(r'\[[^\]\r\n]*\]|\{[^}\r\n]*\}|\$[A-Za-z]', text),
            'status':'analysis_candidate_not_approved_for_translation',
            'consumer_encoding_verified':False}

def locale(name):
    prefix = USR/'locale'/name
    paths = {kind:prefix.with_name(name+'_'+kind+'.dat') for kind in ('dir','eng','trans','static')}
    data = {kind:p.read_bytes() for kind,p in paths.items()}
    directory, eng, trans = data['dir'], data['eng'], data['trans']
    assert len(directory) % 20 == 0
    rebuilt_dir, rebuilt_eng, rebuilt_trans = bytearray(), bytearray(), bytearray()
    records, ids, lengths = [], [], []
    for i in range(len(directory)//20):
        rec = struct.unpack_from('<IIIHHHH', directory, i*20)
        key, eo, to, el, tl, flags, reserved = rec
        assert eo == len(rebuilt_eng) and to == len(rebuilt_trans)
        e, t = eng[eo:eo+el], trans[to:to+tl]
        assert len(e) == el and len(t) == tl
        er = string_record(name+'/eng', key, e, eo, 'utf-8')
        tr = string_record(name+'/trans', key, t, to, 'utf-8')
        tr['directory_record_offset'] = i*20
        tr['directory_fields'] = list(rec)
        tr['english_text'] = er['source_text']
        tr['english_hex'] = er['source_hex']
        tr['english_encoding_candidate'] = er['encoding_candidate']
        records.append(tr)
        ids.append(key)
        lengths.append(tl)
        rebuilt_eng.extend(er['source_text'].encode(er['encoding_candidate']))
        rebuilt_trans.extend(tr['source_text'].encode(tr['encoding_candidate']))
        rebuilt_dir.extend(struct.pack('<IIIHHHH', *rec))
    assert len(ids) == len(set(ids))
    assert rebuilt_eng == eng and rebuilt_trans == trans and rebuilt_dir == directory
    static = data['static']
    header = struct.unpack_from('<I', static)[0]
    rebuilt_static = bytearray(struct.pack('<I', header))
    pos, static_records = 4, []
    occurrences = collections.Counter()
    while pos < len(static):
        rec_offset = pos
        key, length = struct.unpack_from('<IH', static, pos)
        pos += 6
        raw = static[pos:pos+length]
        assert len(raw) == length
        item = string_record(name+'/static', key, raw, pos, 'utf-8')
        occurrences[key] += 1
        item['key_occurrence'] = occurrences[key]
        item['id'] += f':occurrence{occurrences[key]}'
        item['record_offset'] = rec_offset
        static_records.append(item)
        rebuilt_static.extend(struct.pack('<IH', key, length))
        rebuilt_static.extend(item['source_text'].encode(item['encoding_candidate']))
        pos += length
    assert pos == len(static) and rebuilt_static == static
    static_ids = [v['key'] for v in static_records]
    if name == 'en_us':
        write_jsonl(ROOT/'extracted/text/en_us_trans_candidates.jsonl', records)
        write_jsonl(ROOT/'extracted/text/en_us_static_candidates.jsonl', static_records)
    return {'locale':name, 'directory_records':len(records), 'static_records':len(static_records),
            'static_header_raw':header, 'static_max_id':max(static_ids),
            'static_header_semantics':'unconfirmed; not a record count',
            'static_duplicate_ids':{str(k):n for k,n in occurrences.items() if n>1},
            'id_overlap_trans_static':sorted(set(ids)&set(static_ids)),
            'trans_bytes':len(trans), 'eng_bytes':len(eng), 'static_bytes':len(static),
            'max_trans_entry_bytes':max(lengths),
            'trans_larger_than_eng_entries':sum(r['directory_fields'][4]>r['directory_fields'][3] for r in records),
            'trans_encoding_candidates':dict(collections.Counter(r['encoding_candidate'] for r in records)),
            'eng_encoding_candidates':dict(collections.Counter(r['english_encoding_candidate'] for r in records)),
            'static_encoding_candidates':dict(collections.Counter(r['encoding_candidate'] for r in static_records)),
            'all_four_file_roundtrips_exact':True,
            'trans_unique_codepoints':len(set(''.join(r['source_text'] for r in records))),
            'hangul_syllable_count':sum(0xAC00<=ord(c)<=0xD7A3 for r in records+static_records for c in r['source_text']),
            'sha256':{kind:digest(value) for kind,value in data.items()}}

def rsc():
    path = USR/'res/strings.rsc'
    data = path.read_bytes()
    count = struct.unpack_from('<I', data)[0]
    offsets = list(struct.unpack_from('<'+str(count)+'I', data, 4))
    assert offsets[0] == 4+count*4 and offsets == sorted(offsets)
    rebuilt = bytearray(struct.pack('<I', count)+struct.pack('<'+str(count)+'I', *offsets))
    records = []
    for i, offset in enumerate(offsets):
        assert len(rebuilt) == offset
        length = struct.unpack_from('<I', data, offset)[0]
        assert length >= 2 and length % 2 == 0
        raw = data[offset+4:offset+4+length]
        assert len(raw) == length and raw[-2:] == b'\0\0'
        item = string_record('strings.rsc', i, raw[:-2], offset+4, 'utf-16le')
        end = offsets[i+1] if i+1<count else len(data)
        pad = data[offset+4+length:end]
        assert 0 <= len(pad) <= 3 and not any(pad)
        item.update({'length_field':length, 'record_offset':offset, 'padding_hex':pad.hex()})
        records.append(item)
        rebuilt.extend(struct.pack('<I', length))
        rebuilt.extend(item['source_text'].encode('utf-16le')+b'\0\0'+pad)
    assert rebuilt == data
    write_jsonl(ROOT/'extracted/text/ui_rsc_candidates.jsonl', records)
    return {'count':count, 'size':len(data), 'sha256':digest(data),
            'roundtrip_exact':True, 'encoding_candidate':'utf-16le',
            'hangul_syllable_count':sum(0xAC00<=ord(c)<=0xD7A3 for r in records for c in r['source_text'])}

def wad():
    data = (USR/'resource.wad').read_bytes()
    assert data[:4] == b'WADF'
    count = struct.unpack_from('<I', data, 8)[0]
    raw_records = [struct.unpack_from('<4I', data, 16+i*16) for i in range(count)]
    records, fonts = [], []
    for i, (key1,key2,offset,size) in enumerate(raw_records):
        end = raw_records[i+1][2] if i+1<count else len(data)
        assert 16+count*16 <= offset <= offset+size <= end <= len(data)
        name_raw = data[offset+size:end].split(b'\0',1)[0]
        try:
            label = name_raw.decode('ascii')
            if not label or not all(32<=v<127 for v in name_raw):
                label = None
        except UnicodeDecodeError:
            label = None
        payload = data[offset:offset+size]
        item = {'index':i, 'key1_hex':f'{key1:08x}', 'key2_hex':f'{key2:08x}',
                'offset':offset, 'size_candidate':size, 'next_offset':end,
                'trailing_label_candidate':label, 'sha256':digest(payload),
                'header_u32':list(struct.unpack_from('<4I', payload)) if size>=16 else []}
        records.append(item)
        if label and label.startswith('Fonts\\'):
            font = dict(item)
            font['raw_u32_at_0x150'] = list(struct.unpack_from('<4I', payload, 0x150))
            font['record_id_sequence_0_to_255_at_0x17c_stride32'] = all(
                struct.unpack_from('<I', payload, 0x17c+j*32)[0] == j for j in range(256))
            font['mapping_and_texture_format_verified'] = False
            fonts.append(font)
    save_json(ROOT/'workspace/analysis/wad_index_candidates.json', {'schema_version':1,
        'source_sha256':digest(data), 'scope':'static table candidates; no rebuild or consumer validation',
        'count':count, 'entries':records})
    return {'size':len(data), 'sha256':digest(data), 'entry_count_candidate':count,
            'all_extents_in_bounds_nonoverlapping':True,
            'trailing_ascii_labels':sum(r['trailing_label_candidate'] is not None for r in records),
            'fonts':fonts, 'rebuilt_or_runtime_verified':False}

def executable_evidence():
    import capstone
    from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
    b = (DISC/'PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    assert b[:6] == b'\x7fELF\x01\x01'
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
    # Fixed observed windows, not a complete MIPS/Allegrex analysis.
    windows = [(0xfa3bc,0xfa538), (0xfa7a0,0xfa808)]
    lines = ['Static selected MIPS32 instruction windows; ELF-relative addresses, not live RAM.',
             'BOOT .text file offset = ELF virtual address + 0x80.',
             'Unknown instructions abort each window; no full ISA or call graph coverage claimed.', '']
    for start,end in windows:
        code = b[start+0x80:end+0x80]
        instructions = list(md.disasm(code, start))
        assert sum(i.size for i in instructions) == len(code)
        for ins in instructions:
            lines.append(f'{ins.address:08x} {ins.bytes.hex()}  {ins.mnemonic} {ins.op_str}')
        lines.append('')
    for offset in (0x13e860,0x13e870,0x13e880,0x13e8b0,0x13e900,0x13e9b0):
        lines.append(f'file {offset:08x}: '+repr(b[offset:].split(b'\0',1)[0]))
    (ROOT/'workspace/analysis/locale_code_windows.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'boot_sha256':digest(b), 'boot_magic':'ELF32 little endian',
            'eboot_magic_hex':(DISC/'PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes()[:4].hex(),
            'capstone_version':capstone.__version__,
            'selected_windows_elf_relative':[[hex(s),hex(e)] for s,e in windows],
            'locale_path_helper_elf_relative':'0xfa7a0',
            'locale_code_selector_elf_relative':'0xfa494',
            'ko_kr_string_present':True, 'ko_kr_assets_present':False,
            'runtime_loader_encoding_and_font_consumer_unresolved':True}

def main():
    # Verify every extracted file against the registered ISO inventory before analysis.
    source = json.loads((ROOT/'manifests/source.json').read_text(encoding='utf-8'))
    inventory = json.loads((ROOT/'manifests/iso_inventory.json').read_text(encoding='utf-8'))
    assert inventory['source_sha256'] == source['sha256']
    for item in inventory['files']:
        payload = (DISC/item['path']).read_bytes()
        assert len(payload)==item['size'] and digest(payload)==item['sha256'], item['path']
    locales = [locale(n) for n in ('en_us','de_de','es_es','fr_fr','it_it')]
    ui = rsc()
    wad_info = wad()
    exe = executable_evidence()
    report = {'schema_version':1, 'source_sha256':source['sha256'],
        'validation_class':'static candidates and byte roundtrips only',
        'python_version':sys.version, 'locales':locales, 'ui_rsc':ui,
        'english_candidate_record_count':locales[0]['directory_records']+locales[0]['static_records']+ui['count'],
        'wad':wad_info, 'executable':exe,
        'all_game_text_extracted':False, 'font_renderer_verified':False,
        'iso_rebuild_verified':False, 'runtime_tested':False,
        'decision':'conditional_go_for_font_and_runtime_PoC_not_full_translation'}
    save_json(ROOT/'qa/reports/asset_analysis.json', report)
    print(json.dumps({'english_candidate_records':report['english_candidate_record_count'],
        'locale_roundtrips_exact':all(x['all_four_file_roundtrips_exact'] for x in locales),
        'ui_roundtrip_exact':ui['roundtrip_exact'], 'wad_entries':wad_info['entry_count_candidate'],
        'font_candidates':len(wad_info['fonts']), 'decision':report['decision']}))

if __name__ == '__main__':
    main()

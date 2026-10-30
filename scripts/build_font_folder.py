"""Expected-Write guarded folder diagnostics. No ISO generation or source writes.

growth: two extra metric records and relocated texture; original pixels/code/text.
glyphs: explicit two-character diagnostic encoding, two new cells, one fixed
selector-bound instruction, same-length diagnostic prologue prefix.
Neither variant is a release candidate or a final font/encoding adoption.
"""
import argparse
import json
import shutil
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from survey import ROOT, digest, save_json
from psp_folder import sha, verify_tree
from morpheus_font import decode, encode

WAD = 'PSP_GAME/USRDIR/resource.wad'
FONT_OFFSET, FONT_SIZE, SLOT_END = 0x22a5800, 0xa1e0, 0x22b0000
FONT_SHA = 'edf979667560f0562e2073e05b7d97437a1762e231c927318e07294c3557508e'
SOURCE = ROOT / 'extracted/disc'
MAPPING = [{'unicode': 0xd55c, 'slot': 0x100}, {'unicode': 0xae00, 'slot': 0x101}]


def derive(variant,diagnostic=None,font_route_probe=None):
    if diagnostic is not None and diagnostic.get('schema_version')==26:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from second_review_apply_20261030 import derive_second_review
        return derive_second_review(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==25:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from optional_layout_20261030 import derive_optional_layout
        return derive_optional_layout(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==24:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from dialogue3541_20261026 import derive_dialogue3541
        return derive_dialogue3541(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==23:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from optional6_20261025 import derive_optional6
        return derive_optional6(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==22:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from title_original_20261025 import derive_original_title
        return derive_original_title(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==21:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from review17_20261024 import derive_review17
        return derive_review17(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==20:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from property_grouping_build_20261024 import derive_grouping
        return derive_grouping(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==19:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from controls_visibility_20261024 import derive_controls
        return derive_controls(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==18:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from title_geography_20261024 import derive_title
        return derive_title(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==17:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from map_generated_korean_20261024 import derive_generated
        return derive_generated(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==16:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from map_korean_20261024 import derive_map
        return derive_map(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==15:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from loading_korean_20261024 import derive_loading
        return derive_loading(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==14:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from marker_footer_20261024 import derive_markers
        return derive_markers(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==13:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from retained_numeric_formats_20261024 import derive_retained
        return derive_retained(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==12:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from victory_korean_20261024 import derive_victory
        return derive_victory(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==11:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from mode3_korean_20261024 import derive_mode3
        return derive_mode3(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==10:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from book_role_compat_20261024 import derive_compatible
        return derive_compatible(diagnostic)
    if diagnostic is not None and diagnostic.get('schema_version')==9:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        from book_role_split_20261024 import derive_split
        return derive_split(diagnostic)
    assert font_route_probe is None or font_route_probe in ('small','arial10','arial13') and variant=='unicode_hangul_alias_fallback'
    assert diagnostic is None or variant in ('single_unit','single_unit_sprite','single_unit_mixed','unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback')
    if variant in ('atlas', 'columns', 'columns_growth', 'single_unit','single_unit_sprite','single_unit_mixed','unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback'):
        from font_atlas_candidate import derive_atlas
        single=variant in ('single_unit','single_unit_sprite','single_unit_mixed','unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback')
        return derive_atlas(columns=variant in ('columns','columns_growth') or single, loader_growth=variant=='columns_growth', single_unit=single, diagnostic=diagnostic,sprites=variant in ('single_unit_sprite','single_unit_mixed','unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback'),mixed=variant in ('single_unit_mixed','unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback'),unicode_hangul=variant in ('unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback'),single_lane=variant in ('unicode_hangul_single_lane','unicode_hangul_alias_fallback'),alias_fallback=variant=='unicode_hangul_alias_fallback',font_route_probe=font_route_probe)
    inventory = json.loads((ROOT / 'manifests/iso_inventory.json').read_text(encoding='utf-8'))
    items = {f['path']: f for f in inventory['files']}
    source_files = {}
    def original(name):
        if name not in source_files:
            data = (SOURCE / name).read_bytes()
            assert digest(data) == items[name]['sha256'] and len(data) == items[name]['size']
            source_files[name] = data
        return source_files[name]
    wad = original(WAD)
    source_font = wad[FONT_OFFSET:FONT_OFFSET + FONT_SIZE]
    assert digest(source_font) == FONT_SHA
    assert struct.unpack_from('<II', source_font, 0x150) == (256, 0x2180)
    assert struct.unpack_from('<4I', wad, 16 + 952 * 16)[2:] == (FONT_OFFSET, FONT_SIZE)
    tail = wad[FONT_OFFSET + FONT_SIZE:SLOT_END]
    label, zeros = tail.split(b'\0', 1)
    assert label == b'Fonts\\fon_Morpheus' and not any(zeros) and len(zeros) >= 64
    records = []
    texture = source_font[0x21e0:]
    assert encode(decode(texture)) == texture
    font_meta = {'source_font_sha256': FONT_SHA, 'original_records_preserved': 256,
                 'record_count': 258, 'texture_header_relative': 0x21c0,
                 'texture_relative': 0x2220, 'payload_size': 0xa220,
                 'managed_header_preserved': True, 'trailing_label_preserved_and_moved': True}
    if variant == 'growth':
        for mapping in MAPPING:
            rec = bytearray(source_font[0x17c + 63 * 32:0x17c + 64 * 32])
            struct.pack_into('<I', rec, 0, mapping['slot'])
            records.append(bytes(rec))
        font_meta['glyphs_are_question_mark_diagnostics'] = True
    else:
        fmt = json.loads((ROOT / 'qa/reports/font_capacity_20261017.json').read_text(encoding='utf-8'))
        cells = next(f for f in fmt['fonts'] if f['font'].endswith('fon_Morpheus'))['row_major_cells']
        assert len(cells) == 2
        protected = set()
        for code in range(256):
            uv = struct.unpack_from('<4f', source_font, 0x17c + code * 32 + 16)
            x0, y0, x1, y1 = [int(v * 256) for v in uv]
            protected.update((x, y) for x in range(x0, x1) for y in range(y0, y1))
        pixels = decode(texture)
        original_pixels = bytes(pixels)
        font_path = ROOT / 'workspace/font/morpheus_stage003/source_galmuri_2.40.4/Galmuri11.ttf'
        assert sha(font_path) == 'e24256f42e43713d2ea086a1e1669d78b968f5b3cc547e5c157f0606ffa5def1'
        font = ImageFont.truetype(str(font_path), 16)
        allowed = set()
        glyph_meta = []
        for mapping, cell in zip(MAPPING, cells):
            x0, y0, w, h = cell
            cell_pixels = {(x, y) for x in range(x0, x0 + w) for y in range(y0, y0 + h)}
            assert not cell_pixels & protected and not cell_pixels & allowed
            allowed |= cell_pixels
            mask = Image.new('L', (w, h))
            ImageDraw.Draw(mask).text((1, 2), chr(mapping['unicode']), font=font, fill=255)
            mask = mask.point(lambda value: 255 if value >= 128 else 0)
            bounds = mask.getbbox()
            assert bounds and bounds[0] >= 1 and bounds[1] >= 1 and bounds[2] < w and bounds[3] < h
            outline = mask.filter(ImageFilter.MaxFilter(3))
            for y in range(h):
                for x in range(w):
                    pixels[(y0 + y) * 256 + x0 + x] = 11 if mask.getpixel((x, y)) else 15 if outline.getpixel((x, y)) else 1
            records.append(struct.pack('<Iiii4f', mapping['slot'], 0, w, 0,
                                       x0 / 256, y0 / 256, (x0 + w) / 256, (y0 + h) / 256))
            glyph_meta.append(mapping | {'cell': cell, 'ink_bounds': list(bounds)})
        assert all(a == b or (i % 256, i // 256) in allowed
                   for i, (a, b) in enumerate(zip(original_pixels, pixels)))
        texture = encode(pixels)
        assert decode(texture) == pixels
        font_meta.update({'glyphs': glyph_meta, 'glyph_source': str(font_path.relative_to(ROOT)),
                          'glyph_source_sha256': sha(font_path), 'protected_uv_pixels_unchanged': True})
    new_font = bytearray(source_font[:0x217c] + b''.join(records) + source_font[0x217c:])
    assert len(new_font) == 0xa220
    struct.pack_into('<II', new_font, 0x150, 258, 0x21c0)
    new_font[0x2220:] = texture
    assert new_font[0x17c:0x217c] == source_font[0x17c:0x217c]
    assert new_font[0x15c:0x17c] == source_font[0x15c:0x17c]
    assert new_font[0x21c0:0x2220] == source_font[0x2180:0x21e0]
    new_slot = bytes(new_font) + label + b'\0' + zeros[64:]
    assert len(new_slot) == SLOT_END - FONT_OFFSET
    writes = []
    def write(owner, name, offset, final, derivation):
        raw = original(name)
        assert 0 <= offset <= offset + len(final) <= len(raw)
        expected = raw[offset:offset + len(final)]
        writes.append({'owner': owner, 'path': name, 'offset': offset, 'size': len(final),
                       'expected_sha256': digest(expected), 'final_sha256': digest(final),
                       'derivation': derivation, 'data': final})
    write('Morpheus WAD payload length', WAD, 0x3b9c, struct.pack('<I', 0xa220), 'Original index 952 size grows by 64; keys/offset protected')
    write('Morpheus metric count and texture offset', WAD, FONT_OFFSET + 0x150,
          bytes(new_font[0x150:0x158]), 'count258, relative texture header0x21c0')
    write('Morpheus appended records, relocated texture and label', WAD, FONT_OFFSET + 0x217c,
          new_slot[0x217c:], 'Append two metrics before original 4-byte pad; shift texture header/palette/data/label by64; shorten verified zero suffix64. Existing metrics/header protected; pixel writes only declared cells.')
    if variant == 'glyphs':
        boot_name, eboot_name = 'PSP_GAME/SYSDIR/BOOT.BIN', 'PSP_GAME/SYSDIR/EBOOT.BIN'
        boot = bytearray(original(boot_name))
        assert boot[0xc965c:0xc9660] == bytes.fromhex('0001a628')
        before, final = bytes.fromhex('0001a628'), bytes.fromhex('0201a628')
        dis = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
        assert [(i.mnemonic, i.op_str) for i in dis.disasm(before, 0xc95dc)] == [('slti', '$a2, $a1, 0x100')]
        assert [(i.mnemonic, i.op_str) for i in dis.disasm(final, 0xc95dc)] == [('slti', '$a2, $a1, 0x102')]
        boot[0xc965c:0xc9660] = final
        eboot = bytes(boot).ljust(len(original(eboot_name)), b'\0')
        assert len(eboot) == len(original(eboot_name))
        write('Plain ELF EBOOT and fixed selector bound', eboot_name, 0, eboot,
              'Immutable BOOT ELF plus exact fixed slti threshold256->258 at same location; zero pad to original EBOOT size. No moved instructions/branches. Original BOOT file protected.')
        rows = [json.loads(line) for line in (ROOT / 'extracted/text/en_us_trans_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
        row = next(r for r in rows if r['key'] == 3881)
        raw = bytes.fromhex(row['source_hex'])
        assert digest(raw) == row['source_sha256']
        trans_name = 'PSP_GAME/USRDIR/locale/en_us_trans.dat'
        assert original(trans_name)[row['offset']:row['offset'] + len(raw)] == raw
        prefix = b'The streets of Aven'
        position = raw.index(prefix)
        diagnostic = '\u0100\u0101 \u0101\u0100 A9! Test '.encode('utf-8')
        assert len(prefix) == len(diagnostic) == 19
        write('Explicit two-glyph diagnostic prefix', trans_name, row['offset'] + position, diagnostic,
              'Record3881 source prefix The streets of Aven replaced by custom slot encoding for HanGeul GeulHan A9! Test; same19bytes, directory/length/tokens protected. Diagnostic, not approved translation.')
        font_meta['diagnostic'] = {'source_record': 3881, 'source_prefix_hex': prefix.hex(),
                                   'encoded_prefix_hex': diagnostic.hex(), 'mapping': MAPPING,
                                   'mapping_scope': 'Declared prologue diagnostic only; UTF-8 encodes temporary slot IDs U+0100/U+0101, not native Hangul. Original0..255 preserved.',
                                   'selector_instruction': {'offset': 0xc965c, 'before_hex': before.hex(), 'after_hex': final.hex()}}
    writes.sort(key=lambda w: (w['path'], w['offset']))
    outputs = {}
    for name in {w['path'] for w in writes}:
        selected = [w for w in writes if w['path'] == name]
        assert all(a['offset'] + a['size'] <= b['offset'] for a, b in zip(selected, selected[1:]))
        raw = original(name)
        target = bytearray(raw)
        for w in selected:
            assert digest(raw[w['offset']:w['offset'] + w['size']]) == w['expected_sha256']
            target[w['offset']:w['offset'] + w['size']] = w['data']
        cursor = 0
        for w in selected:
            assert target[cursor:w['offset']] == raw[cursor:w['offset']]
            assert digest(target[w['offset']:w['offset'] + w['size']]) == w['final_sha256']
            cursor = w['offset'] + w['size']
        assert target[cursor:] == raw[cursor:] and len(target) == len(raw)
        outputs[name] = bytes(target)
    plan = {'schema_version': 1, 'variant': variant, 'policy': 'development_poc_non_distributable',
            'release_eligible': False, 'source_sha256': inventory['source_sha256'],
            'all_source_files': items, 'font': font_meta,
            'writes': [{k: v for k, v in w.items() if k != 'data'} for w in writes],
            'allowed_changed_files': sorted(outputs), 'iso_created': False}
    return plan, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=['growth', 'glyphs', 'atlas', 'columns', 'columns_growth', 'single_unit','single_unit_sprite','single_unit_mixed','unicode_hangul_mixed','unicode_hangul_single_lane','unicode_hangul_alias_fallback'], required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--diagnostic-config',type=Path)
    parser.add_argument('--font-route-probe',choices=['small','arial10','arial13'])
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in ('.', '..'):
        raise ValueError('Unsafe folder name')
    root = ROOT / 'workspace/runtime' / args.name
    diagnostic=json.loads(args.diagnostic_config.read_text(encoding='utf-8')) if args.diagnostic_config else None
    plan, outputs = derive(args.variant,diagnostic=diagnostic,font_route_probe=args.font_route_probe)
    plan['disc_folder'] = str((root / 'disc').relative_to(ROOT)).replace('\\', '/')
    if args.verify:
        assert json.loads((root / 'expected_writes.json').read_text(encoding='utf-8')) == plan
    else:
        if root.exists():
            raise FileExistsError(root)
        verify_tree(SOURCE)
        root.mkdir()
        # Persist all Expected Writes before creating/applying final game files.
        save_json(root / 'expected_writes.json', plan)
        for name in plan['all_source_files']:
            dest = root / 'disc' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if name in outputs:
                dest.write_bytes(outputs[name])
            else:
                shutil.copy2(SOURCE / name, dest)
    expected = {}
    for name, item in plan['all_source_files'].items():
        data = outputs.get(name)
        expected[name] = {'size': len(data) if data is not None else item['size'],
                          'sha256': digest(data) if data is not None else item['sha256']}
        path = root / 'disc' / name
        assert path.stat().st_size == expected[name]['size'] and sha(path) == expected[name]['sha256']
        assert path.stat().st_ino != (SOURCE / name).stat().st_ino
    assert {p.relative_to(root / 'disc').as_posix() for p in (root / 'disc').rglob('*') if p.is_file()} == set(expected)
    manifest = {'schema_version': 1, 'policy': plan['policy'], 'release_eligible': False,
                'variant': args.variant, 'source_sha256': plan['source_sha256'],
                'disc_folder': plan['disc_folder'], 'files': expected,
                'expected_writes_sha256': sha(root / 'expected_writes.json'),
                'all_differences_owned': True, 'source_files_verified': 80,
                'unchanged_files': 80 - len(outputs), 'iso_created': False}
    if args.font_route_probe is not None:manifest['font_route_probe']=plan['font_route_probe']
    if args.verify:
        assert json.loads((root / 'artifact.json').read_text(encoding='utf-8')) == manifest
    else:
        save_json(root / 'artifact.json', manifest)
    print(json.dumps({'status': 'PASS', 'variant': args.variant, 'folder': plan['disc_folder'],
                      'changed_files': sorted(outputs), 'unchanged_files': manifest['unchanged_files'],
                      'verified_from_immutable_source': True, 'verification_only': args.verify}))


if __name__ == '__main__':
    main()

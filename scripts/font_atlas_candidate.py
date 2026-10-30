"""Unadopted 512-square/font-repertoire diagnostic, used only by primary builder.

Preserves original glyph texels/advances/bearings and halves original normalized
UVs. A same-location fixed LUI change makes the existing quad dimension512.
All five source fonts use512 to avoid changing only one side of a shared rule.
"""
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from survey import ROOT, digest
from psp_folder import sha
from psp_texture import decode_4bpp, encode_4bpp
from morpheus_font import decode as old_decode

REPERTOIRE = [0xac00, 0xac01, 0xad1c, 0xbdc1, 0xd7a3, 0xd55c, 0xae00]

def derive_atlas(columns=False, loader_growth=False, single_unit=False, diagnostic=None, sprites=False,mixed=False,unicode_hangul=False,single_lane=False,alias_fallback=False,font_route_probe=None):
    assert not loader_growth or columns
    assert not single_unit or columns and not loader_growth
    assert diagnostic is None or single_unit
    assert not sprites or single_unit
    assert not mixed or sprites
    assert not unicode_hangul or mixed and single_unit and diagnostic is not None
    assert not single_lane or unicode_hangul
    assert not alias_fallback or single_lane
    assert font_route_probe is None or font_route_probe in ('small','arial10','arial13') and alias_fallback
    if font_route_probe is not None:
        from survey_alias_fallback064 import FALLBACK_CODES
        assert len(diagnostic['cases'])==1 and diagnostic['unmapped_probe_codepoints']==[]
        assert diagnostic['cases'][0]['text'].split(' ',1)[1]==''.join(map(chr,FALLBACK_CODES))
    exact_files=diagnostic is not None and diagnostic.get('file_replacement')=='exact'
    inventory = json.loads((ROOT / 'manifests/iso_inventory.json').read_text(encoding='utf-8'))
    items = {f['path']: f for f in inventory['files']}
    cache = {}
    def original(name):
        if name not in cache:
            data = (ROOT / 'extracted/disc' / name).read_bytes()
            assert digest(data) == items[name]['sha256']
            cache[name] = data
        return cache[name]
    wad_path = 'PSP_GAME/USRDIR/resource.wad'
    wad = original(wad_path)
    catalog = json.loads((ROOT / 'qa/reports/asset_analysis.json').read_text(encoding='utf-8'))
    font_path = ROOT / 'workspace/font/morpheus_stage003/source_galmuri_2.40.4/Galmuri11.ttf'
    assert sha(font_path) == 'e24256f42e43713d2ea086a1e1669d78b968f5b3cc547e5c157f0606ffa5def1'
    cmap = TTFont(font_path).getBestCmap()
    assert all(cmap.get(code) not in (None, '.notdef') for code in REPERTOIRE)
    complete_font_coverage = sum(cmap.get(code) not in (None, '.notdef') for code in range(0xac00, 0xd7a4))
    font = ImageFont.truetype(str(font_path), 16)
    book = None
    if columns:
        from hangul_columns import codebook, atlas, rebuild_locale
        book = codebook(font_path)
        if single_unit:
            from single_unit_renderer import atlas_single as atlas, rebuild_single_locale as rebuild_locale
        if single_lane:
            from single_lane061 import repack,atlas_single_lane
            book=repack(book);atlas=atlas_single_lane
        if alias_fallback:
            from survey_alias_fallback064 import build_book
            from alias_fallback065 import atlas_fallback
            book=build_book()[0];atlas=atlas_fallback
    glyph_masks = []
    for code in REPERTOIRE:
        mask = Image.new('L', (18, 22))
        # Preserve one pixel of outline padding for glyphs with negative left bearing.
        origin_x = 1 - min(0, font.getbbox(chr(code))[0])
        ImageDraw.Draw(mask).text((origin_x, 2), chr(code), font=font, fill=255)
        mask = mask.point(lambda v: 255 if v >= 128 else 0)
        box = mask.getbbox()
        assert box and box[0] >= 1 and box[1] >= 1 and box[2] < 18 and box[3] < 22
        glyph_masks.append((mask, mask.filter(ImageFilter.MaxFilter(3))))
    append = bytearray()
    font_reports, index_finals = [], []
    for asset in catalog['wad']['fonts']:
        source = wad[asset['offset']:asset['offset'] + asset['size_candidate']]
        assert digest(source) == asset['sha256']
        src_pixels = decode_4bpp(source[0x21e0:], 256)
        assert src_pixels == old_decode(source[0x21e0:])
        assert encode_4bpp(src_pixels, 256) == source[0x21e0:]
        pixels, used = bytearray([1]) * (512 * 512), bytearray(512 * 512)
        for y in range(256):
            pixels[y * 512:y * 512 + 256] = src_pixels[y * 256:(y + 1) * 256]
        metrics = bytearray(source[0x17c:0x217c])
        for code in range(256):
            uv = struct.unpack_from('<4f', metrics, code * 32 + 16)
            x0, y0, x1, y1 = [int(v * 256) for v in uv]
            for y in range(y0, y1):
                used[y * 512 + x0:y * 512 + x1] = b'\1' * (x1 - x0)
            new_uv = [v / 2 for v in uv]
            assert all(a * 256 == b * 512 for a, b in zip(uv, new_uv))
            struct.pack_into('<4f', metrics, code * 32 + 16, *new_uv)
            assert metrics[code * 32:code * 32 + 16] == source[0x17c + code * 32:0x17c + code * 32 + 16]
        cells = []
        for y in range(0 if columns else 512 - 22 + 1):
            for x in range(512 - 18 + 1):
                if any(any(used[yy * 512 + x:yy * 512 + x + 18]) for yy in range(y, y + 22)):
                    continue
                cells.append([x, y, 18, 22])
                for yy in range(y, y + 22):
                    used[yy * 512 + x:yy * 512 + x + 18] = b'\1' * 18
        assert columns or len(cells) >= len(REPERTOIRE)
        new_metrics = bytearray()
        for index, (code, cell, masks) in enumerate(zip(REPERTOIRE, cells, glyph_masks)):
            x0, y0, w, h = cell
            mask, outline = masks
            for y in range(h):
                for x in range(w):
                    pixels[(y0 + y) * 512 + x0 + x] = 11 if mask.getpixel((x, y)) else 15 if outline.getpixel((x, y)) else 1
            new_metrics.extend(struct.pack('<Iiii4f', 256 + index, 0, w, 0,
                                           x0 / 512, y0 / 512, (x0 + w) / 512, (y0 + h) / 512))
        palette_mapping = None
        if columns:
            pixels, new_metrics, palette_mapping = atlas(source, src_pixels, book)
            if loader_growth:
                # Capacity-only probe. Retain all014 selected metrics; unused slots
                # are explicit '?' copies and can never appear in diagnostic text.
                template=bytearray(metrics[63*32:64*32])
                for slot in range(7633,14675):
                    struct.pack_into('<I',template,0,slot)
                    new_metrics.extend(template)
                assert len(new_metrics)//32+256==14675
        # Existing source glyph rectangles, not all unused source pixels, are protected.
        for code in range(256):
            uv = struct.unpack_from('<4f', source, 0x17c + code * 32 + 16)
            x0, y0, x1, y1 = [int(v * 256) for v in uv]
            for y in range(y0, y1):
                assert pixels[y * 512 + x0:y * 512 + x1] == src_pixels[y * 256 + x0:y * 256 + x1]
        packed = encode_4bpp(pixels, 512)
        assert decode_4bpp(packed, 512) == pixels
        header = bytearray(source[:0x17c])
        texture_header_offset = 0x2180 + len(new_metrics)
        struct.pack_into('<II', header, 0x150, 256 + len(new_metrics)//32, texture_header_offset)
        tex_header = bytearray(source[0x2180:0x21a0])
        assert struct.unpack_from('<3I', tex_header, 0x10) == (256, 256, 256)
        struct.pack_into('<II', tex_header, 0x10, 512, 512)
        assert tex_header[0x18:] == source[0x2198:0x21a0]  # Format/swizzle byte flags and relative palette pointer.
        payload = bytes(header + metrics + new_metrics) + source[0x217c:0x2180] + tex_header + source[0x21a0:0x21e0] + packed
        assert len(payload) == texture_header_offset + 96 + 131072
        if not columns:assert len(payload) == 139968 and texture_header_offset == 0x2260
        # Original payloads remain intact; only index pointers redirect to appended resources.
        while (len(wad) + len(append)) % 2048:
            append.append(0)
        offset = len(wad) + len(append)
        append.extend(payload + asset['trailing_label_candidate'].encode('ascii') + b'\0')
        while (len(wad) + len(append)) % 2048:
            append.append(0)
        index_finals.append((16 + asset['index'] * 16 + 8, struct.pack('<II', offset, len(payload))))
        font_reports.append({'font': asset['trailing_label_candidate'], 'index': asset['index'],
                             'original_offset': asset['offset'], 'new_offset': offset,
                             'source_payload_sha256': asset['sha256'], 'payload_size': len(payload),
                             'payload_sha256': digest(payload), 'texture_size': [512, 512],
                             'texture_header_relative': texture_header_offset, 'texture_relative': texture_header_offset+96,
                             'original_metrics_semantics_preserved': 256, 'additional_slots': len(new_metrics)//32,
                             'constructive_additional_cell_capacity': len(cells),
                             'new_cells': cells[:len(REPERTOIRE)],
                             **({'logical_to_source_palette':{str(k):v for k,v in palette_mapping.items()},'column_cells':len(book['textures'])} if columns else {})})
    writes = []
    def write(owner, path, offset, final, derivation,whole_file=False):
        raw = original(path)
        expected = raw if whole_file else raw[offset:offset + len(final)]
        assert not whole_file or offset==0
        assert offset <= len(raw)
        writes.append({'owner': owner, 'path': path, 'offset': offset, 'size': len(final),
                       'expected_size': len(expected), 'expected_sha256': digest(expected),
                       'final_sha256': digest(final), 'derivation': derivation, 'data': final,
                       **({'kind':'replace_file'} if whole_file else {})})
    for offset, value in index_finals:
        write('Redirect font resource offset/length', wad_path, offset, value,
              'Original keys/order retained; deterministic append offset and payload size' if columns else 'Original keys/order retained; new append offset and139968-byte payload')
    write('Append five512-square font resources and labels', wad_path, len(wad), bytes(append),
          'Immutable five fonts: preserve code/advance/bearing, halve UVs, preserve source glyph texels, append declared diagnostic metrics/cells, width/height512, unchanged palette/flags, source labels, 2048alignment. Original file body protected except five index offset/length pairs.' if columns else 'Immutable five fonts: preserve code/advance/bearing, halve UVs, preserve source glyph texels, append7 explicit diagnostic metrics/cells, width/height512, unchanged palette/flags, source labels, 2048alignment. Original file body protected except five index offset/length pairs.')
    boot_path, eboot_path = 'PSP_GAME/SYSDIR/BOOT.BIN', 'PSP_GAME/SYSDIR/EBOOT.BIN'
    boot = bytearray(original(boot_path))
    dis = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    instructions = []
    for offset, before, final, before_op, after_op, address in [
            (0xc965c, '0001a628', 'd11da628' if columns else '0701a628', ('slti', '$a2, $a1, 0x100'), ('slti', '$a2, $a1, 0x1dd1' if columns else '$a2, $a1, 0x107'), 0xc95dc),
            (0xc9308, '8043043c', '0044043c', ('lui', '$a0, 0x4380'), ('lui', '$a0, 0x4400'), 0xc9288)]:
        assert boot[offset:offset + 4] == bytes.fromhex(before)
        assert [(i.mnemonic, i.op_str) for i in dis.disasm(bytes.fromhex(before), address)] == [before_op]
        assert [(i.mnemonic, i.op_str) for i in dis.disasm(bytes.fromhex(final), address)] == [after_op]
        boot[offset:offset + 4] = bytes.fromhex(final)
        instructions.append({'boot_offset': offset, 'elf_relative': address, 'before': before, 'after': final})
    hook_info = None
    if single_unit:
        if sprites:from sprite_renderer import build_sprite_prx as build_prx
        else:from single_unit_renderer import build_prx
        eboot,hook_info=build_prx(original(boot_path),mixed=True,unicode_hangul=True,single_lane=single_lane) if unicode_hangul else build_prx(original(boot_path),mixed=True) if mixed else build_prx(original(boot_path))
    else:
        eboot = bytes(boot).ljust(len(original(eboot_path)), b'\0')
        assert len(eboot) == len(original(eboot_path))
    route_report=None
    if font_route_probe is not None:
        from font_route070 import apply_font_route
        eboot,route_report=apply_font_route(original(boot_path),eboot,font_route_probe)
    write('Plain ELF EBOOT with Unicode selector and mixed renderer' if unicode_hangul else 'Plain ELF EBOOT with two fixed constants', eboot_path, 0, eboot,
          'Source BOOT plus preserved-BSS third PT_LOAD,mixed renderer and literal-Unicode public selector; original selector entry replaced by relocated jump/NOP,original unsupported fallback preserved; scoped reference catalog and declared ISA checked.' if unicode_hangul else 'Source BOOT plus third PT_LOAD after preserved BSS, relocated program-header table, new single-unit hook, original JAL relocation retained, selector14675/dimension512. No old instructions moved; original BOOT protected.' if single_unit else 'Source BOOT plus two exact same-address selector/quad constants; no moved instructions/branch/literal targets; zero padding to original EBOOT length; original BOOT protected' if columns else 'Source BOOT plus same-address slti256->263 and LUI float256->512; no moved instructions/branch/literal targets; zero padding to original EBOOT length; original BOOT protected',whole_file=exact_files)
    trans_path = 'PSP_GAME/USRDIR/locale/en_us_trans.dat'
    rows = [json.loads(line) for line in (ROOT / 'extracted/text/en_us_trans_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
    row = next(r for r in rows if r['key'] == 3881)
    raw = bytes.fromhex(row['source_hex'])
    assert original(trans_path)[row['offset']:row['offset'] + len(raw)] == raw
    prefix = ''.join(chr(256 + i) for i in range(len(REPERTOIRE))) + ' A9! '
    locale_changes = None
    if columns:
        dir_path = 'PSP_GAME/USRDIR/locale/en_us_dir.dat'
        if diagnostic is None:
            directory, trans, locale_changes = rebuild_locale(original(dir_path),original(trans_path),book)
        else:
            directory, trans, locale_changes = rebuild_locale(original(dir_path),original(trans_path),book,diagnostic=diagnostic,unicode_hangul=True) if unicode_hangul else rebuild_locale(original(dir_path),original(trans_path),book,diagnostic=diagnostic)
        write('Rebuilt locale directory',dir_path,0,directory,'Source858 entries; only translated offsets/target3881 length updated; English offsets/lengths/flags/reserved preserved',whole_file=exact_files)
        write('Rebuilt locale strings',trans_path,0,trans,'Target3881 diagnostic prefix only; every other raw string preserved byte-identically, control tokens preserved; strict mapped custom encoding, not approved translation',whole_file=exact_files)
        static_changes=None
        if diagnostic is not None and diagnostic.get('static_overrides'):
            from single_unit_renderer import rebuild_static
            static_path='PSP_GAME/USRDIR/locale/en_us_static.dat'
            if unicode_hangul:
                from unicode_codec042 import encode_unicode,decode_unicode
                static,static_changes=rebuild_static(original(static_path),book,diagnostic['static_overrides'],encoder=encode_unicode,decoder=decode_unicode)
            else:static,static_changes=rebuild_static(original(static_path),book,diagnostic['static_overrides'])
            write('Declared static menu diagnostic',static_path,0,static,'Source key/length UTF-8 records in original order; exact source text guards; only declared menu keys changed with single-unit custom encoding; control tokens and every other record preserved. Not approved translation.',whole_file=exact_files)
    else:
        assert len(prefix.encode('utf-8')) == len(b'The streets of Aven') == 19
        write('Seven glyph diagnostic prefix', trans_path, row['offset'] + raw.index(b'The streets of Aven'),
              prefix.encode('utf-8'), 'Record3881 only; same19bytes, tokens and lengths protected; explicit custom codes256..262; diagnostic, not approved translation')
    writes.sort(key=lambda w: (w['path'], w['offset']))
    outputs = {}
    from expected_writes import apply_owned_writes
    for path in {w['path'] for w in writes}:
        selected = [w for w in writes if w['path'] == path]
        outputs[path] = apply_owned_writes(original(path),selected)
    if columns and static_changes is not None and outputs[static_path]!=static:
        raise ValueError('Final static stream retained an old source suffix; exact full-file replacement required')
    if exact_files:
        assert outputs[trans_path]==trans and outputs[dir_path]==directory
    plan = {'schema_version': 2 if exact_files else 1, 'variant': 'columns_growth' if loader_growth else 'columns' if columns else 'atlas', 'policy': 'development_poc_non_distributable',
            'release_eligible': False, 'source_sha256': inventory['source_sha256'], 'all_source_files': items,
            'allowed_changed_files': sorted(outputs), 'iso_created': False,
            'font': {'source': str(font_path.relative_to(ROOT)), 'source_sha256': sha(font_path),
                     'modern_hangul_source_cmap_coverage': complete_font_coverage,
                     'mapping': [{'unicode': c, 'slot': 256 + i} for i, c in enumerate(REPERTOIRE)],
                     'diagnostic_encoded_prefix_hex': prefix.encode('utf-8').hex(),
                     'fonts': font_reports, 'fixed_instruction_constants': instructions,
                     'scope': 'Morpheus body diagnostic; new Korean on other UI fonts and full repertoire/lifetime unverified'},
            'writes': [{k: v for k, v in w.items() if k != 'data'} for w in writes]}
    if columns:
        plan['font'].update({'mapping':{str(k):v for k,v in book['mapping'].items()},'diagnostic_encoded_prefix_hex':locale_changes[0]['diagnostic_encoded_hex'],
                             'locale_changes':locale_changes,'pixel_size':12,'draws_per_syllable':14,
                             'visual_alias_groups':book['aliases'],'full_raster_roundtrips':11172,
                             'mapping_roundtrips':11172,'texture_count':3247,'extra_metric_count':7377,
                             'sampling_profile':'1px column with horizontal extrusion; fractional GPU equivalence unverified',
                             'original_texture_region_and_wrap_ring_preserved':True})
        if single_unit:
            plan['variant']='single_unit'
            if sprites:plan['variant']='single_unit_sprite'
            if mixed:plan['variant']='single_unit_mixed'
            plan['font'].update({'mapping':{'unicode_first':0xac00,'unicode_last':0xd7a3,'slot_first':256,'slot_last':11427},
                                 'code_units_per_syllable':1,'record_count':14675,'extra_metric_count':14419,
                                 'virtual_metric_count':11172,'texture_metric_count':3247,
                                 'selector_upper_bound':14675,'fixed_instruction_constants':None,
                                 'single_unit_hook':hook_info,'scope':'Single-unit prologue diagnostic; full UI/linewrap/font quality/performance remain unverified'})
            if diagnostic is not None:
                plan['diagnostic_input']=diagnostic
                if static_changes:plan['static_diagnostic_changes']=static_changes
                plan['font']['scope']='Declared wrap diagnostic only; original source body retained in immutable extraction, not translated prose'
                if diagnostic.get('trans_overrides'):
                    plan['font']['scope']='Development diagnostics: declared static UI,3881 wrap fixtures and source-guarded2499 tutorial; all other source text preserved; wording/font unapproved and runtime coverage limited to named QA reports'
                next(w for w in plan['writes'] if w['path']==trans_path)['derivation']=('Target3881 body replaced with declared wrap fixtures; original bg/title control header preserved. Additional2499 tutorial uses source-guarded observed literal brackets,CRLF and button preservation; all other856 raw strings preserved. Diagnostic only, not approved translation.' if diagnostic.get('trans_overrides') else 'Target3881 body replaced with declared wrap fixtures; original bg/title control header and every other raw string preserved. Diagnostic only, not approved translation.')
                if diagnostic['schema_version']==6:
                    assert diagnostic['event_resource_probe']['fixture_not_translation'] is True
                    plan['event_resource_probe']=diagnostic['event_resource_probe']
                    plan['font']['scope']='Temporary2499 resource QA fixture copied from source2465 controls,3881 wrap probes and unchanged static35/ability3081 development wording. No tutorial translation selection in this probe; not distributable.'
                    preserved=len(directory)//20-1-len(diagnostic['trans_overrides'])
                    next(w for w in plan['writes'] if w['path']==trans_path)['derivation']=f'Exact source-guarded trans rebuild:3881 wrap fixture,2499 explicit image/page QA fixture,3081 unchanged ability draft; other{preserved} raw strings preserved. Source controls copied literally; all authored text unapproved.'
                    next(w for w in plan['writes'] if w['path']==dir_path)['derivation']='Source858 entries; translated offsets and declared3881/2499/3081 payload lengths updated; original English offsets/lengths,keys,flags,reserved preserved'
        if loader_growth:
            assert all(f['payload_size']==601152 for f in font_reports)
            plan['font'].update({'purpose':'loader capacity only; no single-unit virtual consumer',
                                 'unused_question_mark_records':7042,'record_count':14675,
                                 'selector_upper_bound':7633,'extra_metric_count':14419,
                                 'unused_slots_never_encoded':True})
    if unicode_hangul:
        plan['variant']='unicode_hangul_mixed'
        plan['font'].update({'storage_encoding':'utf8_modern_hangul_v1','selector_upper_bound':None,
                            'public_selector_ranges':[[0,255],[0xac00,0xd7a3]],'public_unmapped_fallback_metric':63,
                            'internal_metric_IDs_are_not_public_character_codes':True})
        plan['declared_unmapped_probes']={'codepoints':diagnostic['unmapped_probe_codepoints'],'scope':'Only declared cases in3881; strict failure remains for authored static/tutorial wording','expected_result':'Original question-mark metric63; not registered glyph coverage'}
        if diagnostic['schema_version']==6:plan['declared_unmapped_probes']['scope']='Only declared cases in3881; strict missing-glyph failure for all other authored/probe override text'
        for w in plan['writes']:
            if w['path'].endswith(('en_us_trans.dat','en_us_static.dat')):w['derivation']+=' Literal Hangul UTF8,not legacy low-code substitution; explicit3881 fallback probes declared separately.'
    if single_lane:
        plan['variant']='unicode_hangul_single_lane'
        plan['font'].update({'sampling_profile':'1-pixel atlas lanes,constant-U at texel center,separate1-pixel geometry; unchanged vertical gutters and G11 glyph raster',
          'scope':'Sampling isolation only: same37 unapproved static/tutorial/ability drafts and3881 fixture; current G11 aliases remain. No font adoption.',
          'column_lane_width':1,'constant_U_texel_centers':True})
        next(w for w in plan['writes'] if w['path']==dir_path)['derivation']='Source858 entries; declared3881/2499/3081 payload lengths and offsets updated; English fields,keys,flags,reserved preserved'
        next(w for w in plan['writes'] if w['path']==trans_path)['derivation']='Source-guarded unchanged37 authored development drafts and3881 fixture; all other855 trans raw records preserved. Literal Hangul Unicode; strict glyph checks outside explicit3881 probes.'
    if alias_fallback:
        from survey_alias_fallback064 import G14_SHA,FALLBACK_CODES
        plan['variant']='unicode_hangul_alias_fallback'
        count=len(book['textures']);assert count==3285 and not book['aliases']
        assert all(f['payload_size']==602368 for f in font_reports)
        plan['font'].update({'texture_count':count,'texture_metric_count':count,'record_count':11428+count,
          'extra_metric_count':11172+count,'visual_alias_groups':[],
          'sampling_profile':'Same061 constant-U1pixel sampling and14column12bit renderer; unchanged vertical gutters;18source-derived glyph fallbacks',
          'source_fallback':{'path':'workspace/font/morpheus_stage003/source_galmuri_2.40.4/Galmuri14.ttf',
             'sha256':G14_SHA,'pixel_size':12,'threshold':128,'codepoints':list(FALLBACK_CODES),
             'unchanged_base_glyphs':11154,'final_font_adoption':False},
          'scope':'Development font PoC:18G11 alias glyphs replaced by G14/12; other11154G11 glyphs and37unapproved wording values preserved. No font/wording approval.'})
    if route_report is not None:
        plan['font_route_probe']=route_report
        plan['font']['scope']='Temporary data-only font route fixture:global Morpheus name requests Small;single-row18-glyph prologue QA,unchanged37draft values. Not original Small map layout or product font adoption.'
        next(w for w in plan['writes'] if w['path']==eboot_path)['derivation']+=' Explicit temporary font-route data write:source file13A1C8 literal fon_Morpheus/NUL becomes fon_Small/NUL with same13bytes;all code/addresses/relocations unchanged.'
        if font_route_probe!='small':
            name=route_report['fixture_name'];display=name.removeprefix('fon_')
            plan['font']['scope']=f'Temporary data-only font route fixture:global Morpheus name requests {display};single-row18-glyph prologue QA,unchanged37draft values. Not all original font consumers or product font adoption.'
            next(w for w in plan['writes'] if w['path']==eboot_path)['derivation']=next(w for w in plan['writes'] if w['path']==eboot_path)['derivation'].replace('fon_Small/NUL',name+'/NUL')
    if alias_fallback and diagnostic is not None:
        authored=len(diagnostic['static_overrides'])+len(diagnostic['trans_overrides'])
        if authored!=37:
            plan['selected_development_draft_count']=authored
            plan['font']['scope']=f'Development font PoC with18G11 alias glyph fallbacks;current{authored} unapproved authored drafts selected from source-guarded static/trans entries. Final font/wording approval remains pending.'
            if route_report is not None:plan['font']['scope']+=' Temporary explicit font-route fixture;not original consumers or layouts.'
            trans_count=len(diagnostic['trans_overrides']);preserved=len(directory)//20-1-trans_count
            next(w for w in plan['writes'] if w['path']==trans_path)['derivation']=f'Source-guarded{trans_count} trans draft values and3881 QA fixture;all other{preserved} trans raw records preserved. Static draft additions are in the separate static file. Literal Hangul Unicode;strict glyph checks outside explicit3881 probes.'
    if alias_fallback and diagnostic is not None and {r['key'] for r in diagnostic.get('trans_overrides',[])}=={2499,3081,2266,2502}:
        next(w for w in plan['writes'] if w['path']==dir_path)['derivation']='Source858 entries;3881 QA fixture and four source-bound trans drafts2499/3081/2266/2502 lengths and translated offsets updated. Original English fields,keys,flags,reserved preserved;literal quest syntax only.'
    if diagnostic is not None and diagnostic.get('schema_version')==7:
        assert alias_fallback and diagnostic['prologue_policy']=='preserve_original_unselected'
        rows=[struct.unpack_from('<IIIHHHH',original(dir_path),p) for p in range(0,len(original(dir_path)),20)]
        source_row=next(r for r in rows if r[0]==3881);source_prologue=original(trans_path)[source_row[2]:source_row[2]+source_row[4]]
        current_row=next(struct.unpack_from('<IIIHHHH',directory,p) for p in range(0,len(directory),20) if struct.unpack_from('<I',directory,p)[0]==3881)
        assert trans[current_row[2]:current_row[2]+current_row[4]]==source_prologue
        count=len(diagnostic['trans_overrides']);total=count+len(diagnostic['static_overrides'])
        plan['source3881']={'policy':'preserve_original_unselected','source_sha256':digest(source_prologue),'source_bytes':len(source_prologue),'byte_exact':True,'fixture_not_present':True,'selected_as_translation':False}
        plan['font']['diagnostic_encoded_prefix_hex']=None
        plan['font']['scope']=f'Development font PoC with{total} unapproved source-bound drafts. Original unselected prologue3881 preserved byte-exact;no wrap/glyph/fallback QA fixture. Final wording/font approval pending.'
        plan['declared_unmapped_probes']={'codepoints':[],'scope':'No intentional fallback probes;strict glyph checks for every authored override. Original unselected prologue retained.','expected_result':None}
        next(w for w in plan['writes'] if w['path']==dir_path)['derivation']=f'Source858 entries;translated offsets and{count} selected draft lengths updated. English fields,keys,flags,reserved protected;3881 original raw payload/length preserved.'
        next(w for w in plan['writes'] if w['path']==trans_path)['derivation']=f'Source-guarded{count} trans draft values;all other{858-count} trans raw records including original3881 prologue preserved exactly. No font/wrap/unmapped QA fixture;strict glyph checks for authored text.'
    if diagnostic is not None and diagnostic.get('schema_version')==8:
        assert alias_fallback and diagnostic['prologue_policy']=='translate_original_contextual'
        source_rows=[struct.unpack_from('<IIIHHHH',original(dir_path),p) for p in range(0,len(original(dir_path)),20)]
        sr=next(r for r in source_rows if r[0]==3881);source_prologue=original(trans_path)[sr[2]:sr[2]+sr[4]]
        current=next(struct.unpack_from('<IIIHHHH',directory,p) for p in range(0,len(directory),20) if struct.unpack_from('<I',directory,p)[0]==3881)
        drafted=next(r for r in diagnostic['trans_overrides'] if r['key']==3881)
        assert trans[current[2]:current[2]+current[4]]==drafted['text'].encode('utf8')
        count=len(diagnostic['trans_overrides']);total=count+len(diagnostic['static_overrides'])
        plan['source3881']={'policy':'translate_original_contextual','source_sha256':digest(source_prologue),'source_bytes':len(source_prologue),'byte_exact':False,'fixture_not_present':True,'selected_as_translation':True,'translated_bytes':current[4],'paragraphs':10,'background_tags':['[bg_SL_intro1]','[bg_SL_intro2]']}
        plan['font']['diagnostic_encoded_prefix_hex']=None
        plan['font']['scope']=f'Development font PoC with{total} unapproved source-bound drafts,including contextual prologue3881. No wrap/glyph/unmapped QA fixture. Final semantic/font approval pending.'
        plan['declared_unmapped_probes']={'codepoints':[],'scope':'No intentional fallback probes;strict glyph checks for every authored override.','expected_result':None}
        next(w for w in plan['writes'] if w['path']==dir_path)['derivation']=f'Source858 entries;translated offsets and{count} selected draft lengths updated. English fields,keys,flags,reserved protected.'
        next(w for w in plan['writes'] if w['path']==trans_path)['derivation']=f'Source-guarded{count} contextual trans drafts including3881 with exact two background tags and ten paragraph boundaries;all other{858-count} raw records preserved. No QA fixture;strict glyph checks.'
    return plan, outputs

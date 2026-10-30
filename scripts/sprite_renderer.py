"""Two-vertex text primitive with exact PRX relocations; development only."""
import re
import struct
from survey import ROOT,digest,save_json
from allegrex_profile import Profile
from single_unit_renderer import build_prx

def build_sprite_prx(source,mixed=False,unicode_hangul=False,single_lane=False):
    assert not unicode_hangul or mixed
    assert not single_lane or unicode_hangul
    baseline,old_info=build_prx(source)
    profile=Profile();folder=ROOT/('workspace/analysis/single_lane061' if single_lane else 'workspace/analysis/unicode042' if unicode_hangul else 'workspace/analysis/mixed023' if mixed else 'workspace/analysis/sprites022')
    origin=old_info['hook_vma'];hookoff=old_info['hook_file_offset'];phoff=old_info['program_header_offset']
    asm=(ROOT/'config'/('mixed_single_unit_draw.asm' if mixed else 'sprite_single_unit_draw.asm')).read_text(encoding='utf-8')
    if single_lane:
        before='    sub.s f22,f12,f13\n    sub.s f20,f14,f15\n    lui t1,0x4400\n    mtc1 t1,f12\n    mul.s f22,f22,f12\n    mul.s f20,f20,f12'
        after='    lui t1,0x3f80\n    mtc1 t1,f22\n    sub.s f20,f14,f15\n    lui t1,0x4400\n    mtc1 t1,f12\n    mul.s f20,f20,f12'
        assert asm.count(before)==1;asm=asm.replace(before,after)
    if unicode_hangul:
        import json
        audit=json.loads((ROOT/'qa/reports/namespace_stage041_references.json').read_text(encoding='utf-8'))
        assert audit['status']=='PASS_BOUNDED_SELECTOR_ENTRY_REFERENCE_CATALOG' and audit['source_BOOT_sha256']==digest(source)
        assert not audit['blocking_interior_references'] and audit['intended_entry_replacement_relative']==[0xc95d8,0xc95e0]
        model=json.loads((ROOT/'qa/reports/unicode_selector_stage042.json').read_text(encoding='utf-8'))
        assert model['status']=='PASS_FULL_U16_SELECTOR_MODEL' and model['source_asm_sha256']==digest((ROOT/'config/unicode_selector042.asm').read_bytes())
        asm+='\n'+(ROOT/'config/unicode_selector042.asm').read_text(encoding='utf-8')
    code=profile.assemble(asm,origin,folder,'sprites',symbols=True)
    symbols={name:int(value,16) for value,name in re.findall(r'^([0-9A-Fa-f]{8}) ([a-z_]+)\s*$',(folder/'sprites.sym').read_text(),re.M)}
    decoded=profile.verify_roundtrip(code,origin,folder,'sprites_roundtrip')
    assert symbols['entry']==origin
    if unicode_hangul:
        assert symbols['unicode_selector']==model['selector_origin']
        assert digest(code[symbols['unicode_selector']-origin:])==model['selector_sha256']
    relocations=[];edges=[];boundaries={i['pc'] for i in decoded}
    for index,ins in enumerate(decoded):
        pc=ins['pc'];name=ins['name'];fields=ins['fields']
        if name in ['j','jal']:relocations.append((pc-origin,0x204))
        if name in ['beq','bne']:
            offset=fields['offset'];offset=offset-65536 if offset&32768 else offset
            target=pc+4+offset*4;assert target in boundaries
            edges.append({'pc':pc,'target':target,'kind':name})
        if name in ['beq','bne','j','jal','jr']:
            delay=decoded[index+1]
            assert delay['name'] in ['nop','or','addiu'] or mixed and delay['name']=='lw' and delay['fields']=={'rt':5,'offset':20,'base':29}
        assert name not in ['eret','mfc0','mtc0']
    relocations.extend([(symbols['sprite_white_hi']-origin,0x205),(symbols['sprite_white_lo']-origin,0x206)])
    relocations.sort()
    assert len({p for p,_ in relocations})==len(relocations)
    entry_relocations=[(0xc95d8,4)] if unicode_hangul else []
    shoff=struct.unpack_from('<I',source,32)[0];relhdr=shoff+2*40
    original_reloc=struct.unpack_from('<10I',source,relhdr)
    assert original_reloc[1]==0x700000a0 and original_reloc[4:6]==(1798408,327736)
    result=bytearray(baseline[:hookoff]);result.extend(code)
    relfile=(len(result)+15)&~15;result.extend(b'\0'*(relfile-len(result)))
    table=source[original_reloc[4]:original_reloc[4]+original_reloc[5]]
    result.extend(table+b''.join(struct.pack('<II',off,info) for off,info in relocations+entry_relocations))
    struct.pack_into('<II',result,relhdr+16,relfile,len(table)+(len(relocations)+len(entry_relocations))*8)
    struct.pack_into('<II',result,phoff+64+16,len(code),len(code))
    # Delay-slot constant and an existing relocated call, no source instruction moves.
    assert source[0xc9db4+128:0xc9db8+128]==bytes.fromhex('03000534')
    if not mixed:result[0xc9db4+128:0xc9db8+128]=profile.assemble('ori a1,zero,6',0xc9db4,folder,'begin_mode')
    assert source[0x1ee840:0x1ee848]==struct.pack('<II',0xca2bc,4)
    result[0xca2bc+128:0xca2c0+128]=profile.assemble(f'jal 0x{symbols["sprite_flush"]:x}',0xca2bc,folder,'flush_call')
    if unicode_hangul:
        assert source[0xc95d8+128:0xc95e0+128]==bytes.fromhex('ffffa5300001a628')
        assert not any(struct.unpack_from('<II',table,p)[0]==0xc95d8 for p in range(0,len(table),8))
        result[0xc95d8+128:0xc95e0+128]=profile.assemble(f'j 0x{symbols["unicode_selector"]:x}\nnop',0xc95d8,folder,'unicode_entry')
    allowed=[(28,4),(44,2),(0xc9560+128,4),(0xc95dc+128,4),(0xc9288+128,4),
             (0xc9db4+128,4),(0xca2bc+128,4),(relhdr+16,8)]
    if unicode_hangul:allowed.append((0xc95d8+128,4))
    owned={p for a,n in allowed for p in range(a,a+n)}
    assert all(a==b or p in owned for p,(a,b) in enumerate(zip(source,result)))
    assert result[relfile:relfile+len(table)]==table
    live_checks=[]
    for base in [0x08804000,0x08904000]:
        live=bytearray(code)
        for offset,info in relocations:
            word=struct.unpack_from('<I',live,offset)[0];kind=info&15
            if kind==4:word=(word&0xfc000000)|(((word&0x3ffffff)+(base>>2))&0x3ffffff)
            elif kind==5:word=(word&0xffff0000)|(((base+0x1611c0+0x8000)>>16)&65535)
            elif kind==6:word=(word&0xffff0000)|((base+0x1611c0)&65535)
            else:raise AssertionError(kind)
            struct.pack_into('<I',live,offset,word)
        loaded=profile.verify_roundtrip(live,base+origin,folder,f'sprites_live_{base:x}')
        for original,actual in zip(decoded,loaded):
            if original['name'] in ['j','jal']:
                assert ((actual['word']&0x3ffffff)<<2)==base+((original['word']&0x3ffffff)<<2)
        white_hi=struct.unpack_from('<I',live,symbols['sprite_white_hi']-origin)[0]&65535
        white_lo=struct.unpack_from('<I',live,symbols['sprite_white_lo']-origin)[0]&65535
        white_lo=white_lo-65536 if white_lo&32768 else white_lo
        assert (white_hi<<16)+white_lo==base+0x1611c0
        live_checks.append({'base':base,'bytes_sha256':digest(live)})
    info={**old_info,'implementation':'Hangul sprite/unchanged original ASCII triangles with explicit batch transition' if mixed else 'two-vertex GU_SPRITES text batches; fallback to original quad/flush for other context modes',
          'hook_bytes':len(code),'hook_sha256':digest(code),'symbols':symbols,
          'relocations':[list(r) for r in relocations],'relocation_table_file_offset':relfile,
          'original_relocation_bytes_preserved':len(table),'relocation_section_header_offset':relhdr,
          'source_instructions_moved':False,'relative_branch_edges':edges,
          'new_geometry_vertices_per_quad':2,'old_geometry_vertices_per_quad':6,
          **({'ASCII_geometry':'original quad,original triangle batch','font_begin_mode_original':3,'transitions_preserve_FPR0_to19':True} if mixed else {}),
          'allocator_limit_unchanged':491520,'vertex_format_unchanged':0x1ff,
          'all_generated_words_profile_roundtrip':True,'live_relocation_checks':live_checks,
          'runtime_verified':False,'scope':'New renderer only. Orthographic UI sprites require runtime equivalence; no arbitrary 3D-font claim.'}
    if unicode_hangul:
        placement=[]
        entry_word=struct.unpack_from('<I',result,0xc95d8+128)[0]
        for base in [0x08804000,0x08904000]:
            live=(entry_word&0xfc000000)|(((entry_word&0x3ffffff)+(base>>2))&0x3ffffff)
            check=profile.verify_roundtrip(struct.pack('<I',live)+b'\0'*4,base+0xc95d8,folder,f'unicode_entry_live_{base:x}')
            target=((live&0x3ffffff)<<2)|((base+0xc95dc)&0xf0000000)
            assert target==base+symbols['unicode_selector'] and check[1]['name']=='nop'
            placement.append({'module_base':base,'entry_pc':base+0xc95d8,'selector_pc':target})
        info.update({'encoding':'utf8_modern_hangul_v1','selector_source_entry':0xc95d8,'selector_new_vma':symbols['unicode_selector'],
                     'selector_bytes':len(code)-(symbols['unicode_selector']-origin),'source_entry_relocations':[list(r) for r in entry_relocations],
                     'selector_entry_before':source[0xc95d8+128:0xc95e0+128].hex(),'selector_entry_after':result[0xc95d8+128:0xc95e0+128].hex(),
                     'selector_placement_checks':placement,'selector_reference_audit':'qa/reports/namespace_stage041_references.json',
                     'selector_interface':'Same modified a0,a1,a2,v0 as original; no stack/FPR/RA changes; full u16 domain requires audit',
                     'public_unmapped_fallback_metric':63,'internal_texture_metrics':'Direct pointer arithmetic in existing mixed dispatcher; never routed through public Unicode selector'})
    if single_lane:info.update({'constant_U_sampling':True,'geometry_width_per_column':1,'glyph_raster_and_14_column_mapping_unchanged':True})
    save_json(folder/'prx_layout.json',info)
    return bytes(result),info

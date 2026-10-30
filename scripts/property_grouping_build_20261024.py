"""Source-derived schema20: property-local grouping, unchanged common renderer."""
import argparse,copy,json,re,struct
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from allegrex_profile import Profile
from title_geography_20261024 import CONFIG as PARENT,derive_title,WAD

NAME='property_grouping_20261024';CONFIG='development_'+NAME+'.json'
ASM=ROOT/'config/property_grouping_20261024.asm'
WORK=ROOT/'workspace/analysis/property_grouping_build_20261024'
EBOOT='PSP_GAME/SYSDIR/EBOOT.BIN'

def configuration():
    proof=ROOT/'qa/reports/property_wrap_20261024_runtime.json'
    p=json.loads(proof.read_text(encoding='utf8'))
    assert p['status']=='PASS_REVERSIBLE_CAUSAL_GROUPING_EXPERIMENT_PRODUCT_FIX_PENDING'
    return dict(schema_version=20,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        property_grouping=dict(assembly=ASM.relative_to(ROOT).as_posix(),assembly_sha256=digest(ASM.read_bytes()),
            evidence=proof.relative_to(ROOT).as_posix(),evidence_sha256=digest(proof.read_bytes()),
            scope='Three original25A94 formatter calls only;preserve leading separators,bind internal word spaces as NBSP;five zero-ink metric160 advances equal source spaces.',
            UTF16_scan_bound=2048,common_renderer_unchanged=True,main_text_SSOT_changed=False),release_eligible=False)

def select():
    protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),indent=2)+'\n')
    print('Prepared schema20 property grouping candidate configuration;not yet adopted.')

def patch_elf(parent):
    p=Profile();WORK.mkdir(parents=True,exist_ok=True)
    phoff=struct.unpack_from('<I',parent,28)[0];assert struct.unpack_from('<H',parent,44)[0]==3
    ph=[struct.unpack_from('<8I',parent,phoff+i*32) for i in range(3)]
    third=ph[2];assert third[0]==1 and third[4]==third[5] and third[6:]==(5,64)
    shoff=struct.unpack_from('<I',parent,32)[0];relhdr=shoff+2*40
    rel=struct.unpack_from('<10I',parent,relhdr);assert rel[1]==0x700000a0
    relfile,relsize=rel[4:6];assert relfile+relsize==len(parent)
    original_table=parent[relfile:relfile+relsize]
    pad=(-third[4])%16;origin=third[2]+third[4]+pad;codeoff=third[1]+third[4]+pad
    assert codeoff>=third[1]+third[4] and codeoff<=relfile
    hook=p.assemble(ASM.read_text(encoding='utf8'),origin,WORK,'property_group',symbols=True)
    decoded=p.verify_roundtrip(hook,origin,WORK,'property_group_roundtrip')
    symbols={name:int(value,16) for value,name in re.findall(r'^([0-9a-fA-F]{8}) ([a-z_]+)\s*$',(WORK/'property_group.sym').read_text(),re.M)}
    assert symbols['property_integer_group']==origin
    boundaries={x['pc'] for x in decoded};relocs=[]
    for i,x in enumerate(decoded):
        if x['name']=='jal':
            assert ((x['word']&0x3ffffff)<<2) in [0x6fcf4,0x6fe20]
            relocs.append((x['pc']-third[2],0x204))
        if x['name'] in ['beq','bne']:
            v=x['fields']['offset'];v=v-65536 if v&32768 else v
            assert x['pc']+4+4*v in boundaries
        if x['name'] in ['beq','bne','jal','jr']:
            delay=decoded[i+1]
            assert delay['name'] in ['nop','or','addiu'] or delay['word']==0x340b00a0
        assert x['name'] not in ['j','jalr','eret','mfc0','mtc0']
    assert len(relocs)==2
    out=bytearray(parent[:third[1]+third[4]]);out.extend(b'\0'*pad);assert len(out)==codeoff
    out.extend(hook);newrel=(len(out)+15)&~15;out.extend(b'\0'*(newrel-len(out)))
    out.extend(original_table+b''.join(struct.pack('<II',*x) for x in relocs))
    newsize=codeoff+len(hook)-third[1]
    struct.pack_into('<II',out,phoff+64+16,newsize,newsize)
    struct.pack_into('<II',out,relhdr+16,newrel,relsize+16)
    source=parent[128:128+1271960];sites=[]
    for pc in range(0x25a94,0x25bdc,4):
        word=struct.unpack_from('<I',source,pc)[0]
        if word>>26!=3:continue
        target=(word&0x3ffffff)<<2
        if target not in [0x6fcf4,0x6fe20]:continue
        assert sum(struct.unpack_from('<II',original_table,j)==(pc,4) for j in range(0,relsize,8))==1
        newtarget=symbols['property_integer_group' if target==0x6fcf4 else 'property_percent_group']
        after=p.assemble(f'jal 0x{newtarget:x}',pc,WORK,'site_'+hex(pc)[2:])
        out[128+pc:132+pc]=after
        sites.append(dict(pc=pc,old_target=target,new_target=newtarget,before=parent[128+pc:132+pc].hex(),after=after.hex()))
    assert len(sites)==3 and [x['old_target'] for x in sites].count(0x6fcf4)==1
    protected_spans=[(phoff+64+16,8),(relhdr+16,8)]+[(128+x['pc'],4) for x in sites]
    allowed={j for a,n in protected_spans for j in range(a,a+n)}
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(parent[:third[1]+third[4]],out)))
    assert out[newrel:newrel+relsize]==original_table
    checks=[]
    for base in [0x08804000,0x08904000]:
        live=bytearray(hook)
        for offset,info in relocs:
            at=offset-(origin-third[2]);v=struct.unpack_from('<I',live,at)[0]
            v=(v&0xfc000000)|(((v&0x3ffffff)+(base>>2))&0x3ffffff);struct.pack_into('<I',live,at,v)
        rows=p.verify_roundtrip(live,base+origin,WORK,'hook_live_'+hex(base)[2:])
        assert [((x['word']&0x3ffffff)<<2) for x in rows if x['name']=='jal']==[base+0x6fcf4,base+0x6fe20]
        for site in sites:
            v=int.from_bytes(bytes.fromhex(site['after']),'little');v=(v&0xfc000000)|(((v&0x3ffffff)+(base>>2))&0x3ffffff)
            assert ((v&0x3ffffff)<<2)==base+site['new_target']
        checks.append(dict(base=base,relocated_hook_sha256=digest(live)))
    meta=dict(hook_origin=origin,hook_file_offset=codeoff,hook_size=len(hook),hook_sha256=digest(hook),symbols=symbols,
        sites=sites,new_relocations=[list(x) for x in relocs],parent_first_two_PT_LOAD_unchanged=True,old_third_code_preserved=True,
        old_BSS_preserved=True,old_relocation_table_preserved_bytes=relsize,third_segment_growth=newsize-third[4],
        placement_checks=checks,relative_call_relocation_policy='Reuse segment0 base-add original sites;new calls write in segment2/read segment0 (0x204).')
    save_json(WORK/'elf_patch.json',meta)
    return bytes(out),meta

def derive_grouping(cfg):
    assert cfg==configuration()
    parentcfg=json.loads((ROOT/'config'/PARENT).read_text(encoding='utf8'))
    plan,outputs=derive_title(parentcfg);plan=copy.deepcopy(plan);outputs=dict(outputs)
    parent_artifact=json.loads((ROOT/'workspace/runtime/title_geography_20261024/artifact.json').read_text(encoding='utf8'))
    for path in [EBOOT,WAD]:assert digest(outputs[path])==parent_artifact['files'][path]['sha256']
    outputs[EBOOT],elfmeta=patch_elf(outputs[EBOOT])
    before=outputs[WAD];wad=bytearray(before);metrics=[];ranges=[]
    for font in plan['font']['fonts']:
        off,size=struct.unpack_from('<II',wad,16+font['index']*16+8)
        assert off==font['new_offset'] and size==font['payload_size']
        s=struct.unpack_from('<Iiii4f',wad,off+0x17c+32*32);n=struct.unpack_from('<Iiii4f',wad,off+0x17c+160*32)
        assert s[0:4]==(32,0,5,0) and n[0:4]==(160,0,0,0) and n[4]==n[6] and n[5]==n[7]
        at=off+0x17c+160*32+8;struct.pack_into('<i',wad,at,s[2]);ranges.append((at,at+4))
        metrics.append(dict(index=font['index'],font=font['font'],offset=at,before=0,after=s[2],zero_ink_and_other31metrics_bytes_preserved=True))
        font.update(payload_sha256=digest(wad[off:off+size]),original_metrics_semantics_preserved=255,
            NBSP160=dict(code=160,advance=s[2],zero_ink_preserved=True))
    assert len(metrics)==5
    cursor=0
    for a,z in sorted(ranges):assert wad[cursor:a]==before[cursor:a];cursor=z
    assert wad[cursor:]==before[cursor:] and len(wad)==len(before)
    outputs[WAD]=bytes(wad)
    ew=[x for x in plan['writes'] if x['path']==EBOOT];assert len(ew)==1 and ew[0]['offset']==0 and ew[0]['kind']=='replace_file'
    ew[0].update(size=len(outputs[EBOOT]),final_sha256=digest(outputs[EBOOT]),
        derivation=ew[0]['derivation']+' Extend owned third PT_LOAD with two property-only formatter wrappers;preserve existing load/BSS/code/relocations;three original JAL sites and2 new R_MIPS_26 relocations only.')
    for a,z in ranges:
        writers=[x for x in plan['writes'] if x['path']==WAD and x['offset']<=a and z<=x['offset']+x['size']];assert len(writers)==1
    writers={id(x):x for x in plan['writes'] if x['path']==WAD and any(x['offset']<=a and z<=x['offset']+x['size'] for a,z in ranges)}
    assert len(writers)==1
    for x in writers.values():
        x.update(final_sha256=digest(outputs[WAD][x['offset']:x['offset']+x['size']]),
            derivation=x['derivation']+' Exception:existing zero-ink glyph160 advance0->source-space advance5 in all five appended fonts;code,bearing,UVs,raster and all other metrics preserved.')
    plan['diagnostic_input']=cfg;plan['property_grouping']=dict(elf=elfmeta,font_metrics=metrics,
        common_renderer_and_locale_SSOT_unchanged=True,native_verification_pending=True,release_eligible=False)
    save_json(WORK/'font_metrics.json',metrics)
    return plan,outputs

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);a=p.parse_args();globals()[a.action]()

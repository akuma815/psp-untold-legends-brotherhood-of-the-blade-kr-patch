"""804 UI source-record inventory and exact paletted-index roundtrips; no asset edits."""
import json,re,struct
from collections import Counter
from PIL import Image
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from psp_texture import decode_4bpp,encode_4bpp
from ui_texture_candidates_20261024 import swizzle8


def decode(packed,w,h,depth):
    stride=w*depth//8;assert stride%16==0 and h%8==0 and len(packed)==stride*h
    linear=bytearray(len(packed))
    for y in range(h):
        for x in range(stride):
            p=(y//8)*(stride*8)+(x//16)*128+(y%8)*16+x%16
            linear[y*stride+x]=packed[p]
    if depth==8:return bytes(linear)
    out=bytearray(w*h)
    for i,b in enumerate(linear):out[2*i]=b&15;out[2*i+1]=b>>4
    return bytes(out)


def encode(pixels,w,h,depth):
    assert len(pixels)==w*h
    if depth==4:
        assert all(v<16 for v in pixels)
        linear=bytes(pixels[i]|pixels[i+1]<<4 for i in range(0,len(pixels),2))
    else:linear=pixels
    stride=w*depth//8;out=bytearray(len(linear))
    for y in range(h):
        for x in range(stride):
            p=(y//8)*(stride*8)+(x//16)*128+(y%8)*16+x%16
            out[p]=linear[y*stride+x]
    return bytes(out)


def main():
    idxpath=ROOT/'workspace/analysis/wad_index_candidates.json';idx=json.loads(idxpath.read_text(encoding='utf-8'))
    assert idx['count']==7543 and idx['source_sha256']=='696b7618de5fc7c2610666b7b9f543ec2be5e91bcd0bcdd86c20d0d5db47870d'
    ui=[e for e in idx['entries'] if e['trailing_label_candidate'].startswith('Textures\\Ui\\')];assert len(ui)==804
    prior=json.loads((ROOT/'qa/reports/ui_texture_candidates_20261024.json').read_text(encoding='utf-8'))
    already={e['index'] for e in prior['records']}
    records=[];previews=[];out=ROOT/'workspace/graphics/ui_additional_candidates_20261024'
    with (ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').open('rb') as f:
        for e in ui:
            f.seek(e['offset']);raw=f.read(e['size_candidate']);assert digest(raw)==e['sha256']
            head=struct.unpack_from('<8I',raw);w,h=head[4:6];depth=4 if head[6]&255==0 else 8
            assert head[1]==0x106 and head[6]&255 in [0,1] and (head[6]>>8)&255==1 and head[7]==32
            assert w in [32,64,128,256,512] and h in [32,64,128,256,512]
            colors=1<<depth;palette=raw[32:32+colors*4];packed=raw[32+colors*4:]
            assert len(packed)==w*h*depth//8
            pixels=decode(packed,w,h,depth);reverse=encode(pixels,w,h,depth)
            assert raw[:32]+palette+reverse==raw
            if w==h and w in [256,512] and depth==4:
                assert pixels==decode_4bpp(packed,w) and reverse==encode_4bpp(pixels,w)
            if w==h==512 and depth==8:assert pixels==swizzle8(packed) and reverse==swizzle8(pixels,decode=False)
            name=e['trailing_label_candidate'].split('\\')[-1]
            interesting=bool(re.search(r'(?i)text|button|logo|splash|title|loading|font|select|menu|start|legal|credits|caption|label|psp|arrow|tutorial|controlscheme|ui_actv|ui__|dialog|hud|SL_end',name))
            record=dict(index=e['index'],label=e['trailing_label_candidate'],WAD_offset=e['offset'],source_bytes=len(raw),source_sha256=digest(raw),
                width=w,height=h,bpp=depth,header_u32=list(head),header_opaque_words=[2,3],header_word6_opaque_upper16=head[6]>>16,
                palette_bytes=len(palette),packed_bytes=len(packed),indexed_roundtrip_byte_equal=True,name_priority_candidate=interesting,
                pixel_text_status='unresolved',runtime_consumer_confirmed=e['index']==5419)
            if interesting and e['index'] not in already:
                path=out/f'{e["index"]:04}_{name}.png';assert not path.exists(),'Protected preview exists'
                path.parent.mkdir(parents=True,exist_ok=True)
                im=Image.frombytes('P',(w,h),pixels);im.putpalette(palette,'RGBA');im.convert('RGBA').save(path)
                preview=dict(index=e['index'],path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()),width=w,height=h)
                record['preview']=preview['path'];previews.append(preview)
            records.append(record)
    target=ROOT/'workspace/analysis/ui_texture_inventory_20261024/records.jsonl'
    protected_write(target,''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    report=dict(status='PASS804_SOURCE_RECORD_HASHES_DIMENSIONS_AND_EXACT_INDEXED_ROUNDTRIPS_NOT_RUNTIME_COVERAGE',
        source_WAD_sha256=idx['source_sha256'],source_index_sha256=digest(idxpath.read_bytes()),records_path=target.relative_to(ROOT).as_posix(),
        records_sha256=digest(target.read_bytes()),UI_named_records=804,total_source_bytes=sum(e['source_bytes'] for e in records),
        bpp_counts=dict(Counter(e['bpp'] for e in records)),dimensions=dict(Counter('%dx%d'%(e['width'],e['height']) for e in records)),
        priority_name_candidates=sum(e['name_priority_candidate'] for e in records),additional_source_previews=previews,
        opaque_header_policy='Preserve words2/3 and upper16 of word6;nonzero values are not semantic flags inferred here.',
        palette_interpretation='Candidate RGBA8888;not all runtime consumers confirmed. Source reconstruction preserves raw palette and whole record.',
        native_runtime_checks_added=0,new_graphics_translation=0,new_game_SSOT_or_config_bytes=0,release_eligible=False)
    save_json(ROOT/'qa/reports/ui_texture_inventory_20261024.json',report)
    print(json.dumps({k:report[k] for k in ['status','UI_named_records','total_source_bytes','bpp_counts','dimensions','priority_name_candidates']}))
    print('Additional previews:',len(previews))


if __name__=='__main__':main()

"""Source-only 512-square paletted UI previews with exact indexed-byte roundtrip."""
import json,struct
from PIL import Image
from survey import ROOT,digest,save_json
from psp_texture import decode_4bpp,encode_4bpp

INDICES=[4850,5092,5419,5420,5421,5422,5423,5509,5510,5511]


def swizzle8(data,width=512,decode=True):
    assert len(data)==width*width
    out=bytearray(len(data))
    for y in range(width):
        for x in range(width):
            packed=(y//8)*(width*8)+(x//16)*128+(y%8)*16+x%16
            linear=y*width+x
            if decode:out[linear]=data[packed]
            else:out[packed]=data[linear]
    return bytes(out)


def main():
    ip=ROOT/'workspace/analysis/wad_index_candidates.json';idx=json.loads(ip.read_text(encoding='utf-8'))
    assert idx['count']==7543 and idx['source_sha256']=='696b7618de5fc7c2610666b7b9f543ec2be5e91bcd0bcdd86c20d0d5db47870d'
    out=ROOT/'workspace/graphics/ui_source_candidates_20261024';out.mkdir(parents=True,exist_ok=True);records=[]
    with (ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').open('rb') as f:
        for i in INDICES:
            e=idx['entries'][i];assert e['index']==i
            f.seek(e['offset']);raw=f.read(e['size_candidate']);assert digest(raw)==e['sha256']
            header=struct.unpack_from('<8I',raw);assert header[1]==0x106 and header[4:6]==(512,512) and header[7]==32
            depth=4 if header[6]&255==0 else 8;assert header[6]&255 in [0,1] and (header[6]>>8)&255==1
            colors=1<<depth;palette=raw[32:32+colors*4];packed=raw[32+colors*4:]
            assert len(packed)==512*512*depth//8
            pixels=bytes(decode_4bpp(packed,512)) if depth==4 else swizzle8(packed)
            reverse=encode_4bpp(pixels,512) if depth==4 else swizzle8(pixels,decode=False)
            assert raw[:32]+palette+reverse==raw
            name=e['trailing_label_candidate'].split('\\')[-1];path=out/f'{i:04}_{name}.png'
            assert not path.exists(),'Protected source preview already exists'
            im=Image.frombytes('P',(512,512),pixels);im.putpalette(palette,'RGBA');im.convert('RGBA').save(path)
            records.append(dict(index=i,label=e['trailing_label_candidate'],WAD_offset=e['offset'],source_record_bytes=len(raw),source_record_sha256=digest(raw),
                header_u32=list(header),candidate_width=512,candidate_height=512,candidate_bpp=depth,palette_bytes=len(palette),pixel_data_bytes=len(packed),
                palette_interpretation_candidate='RGBA8888 bytes;visual/source-consumer confirmation still required',swizzled_indexed_roundtrip_byte_equal=True,
                preview=path.relative_to(ROOT).as_posix(),preview_sha256=digest(path.read_bytes()),actual_runtime_consumer_identified=False,
                is_translation_target_not_yet_decided=True))
    report=dict(status='TEN_SOURCE_UI_IMAGE_CANDIDATES_DECODED_INDEXED_BYTES_EXACT_ROUNDTRIP_NOT_RUNTIME_OR_TRANSLATION_PROOF',
        WAD_index_sha256=digest(ip.read_bytes()),source_WAD_sha256=idx['source_sha256'],records=records,
        scope='These10 named UI candidates only;not complete graphics-text population. Source previews,not native screenshots.',
        new_native=0,new_game_or_SSOT_or_config_bytes=0,new_graphics_translation=0,release_eligible=False)
    save_json(ROOT/'qa/reports/ui_texture_candidates_20261024.json',report)
    print('PASS10 source previews;exact indexed-byte roundtrip;no runtime or translation claim.')


if __name__=='__main__':main()

"""Read-only exact map PNG/record codec; no resampling, quantization or game writer."""
import json,struct
from PIL import Image
from survey import ROOT,digest,save_json
from ui_texture_inventory_20261024 import decode,encode


def source():
    idx=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf-8'))
    assert idx['source_sha256']=='696b7618de5fc7c2610666b7b9f543ec2be5e91bcd0bcdd86c20d0d5db47870d'
    rows=[]
    with (ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').open('rb') as f:
        for n in range(1,65):
            e=idx['entries'][5095+n]
            assert e['trailing_label_candidate']==f'Textures\\Ui\\tex_ui_map_0_{n:02}'
            f.seek(e['offset']);raw=f.read(e['size_candidate']);assert digest(raw)==e['sha256']
            h=struct.unpack_from('<8I',raw)
            assert h[1]==0x106 and h[4:6]==(128,128) and h[6]&0xffff==0x100 and h[7]==32
            assert len(raw)==8288
            palette=[tuple(raw[i:i+4]) for i in range(32,96,4)]
            pixels=decode(raw[96:],128,128,4)
            assert raw[:96]+encode(pixels,128,128,4)==raw
            rows.append(dict(number=n,entry=e,raw=raw,palette=palette,pixels=pixels))
    return rows


def encode_candidate(size,rgba,rows,rectangles):
    """Encode a candidate in memory for review only, preserving all other pixels.

    Rectangles bound a candidate change; they do not establish a clean background,
    an adopted erase mask, final layout, or authorization for a product build.
    """
    if tuple(size)!=(1024,1024):raise ValueError('INPUT_DIMENSIONS_MUST_BE1024X1024')
    if len(rgba)!=1024*1024:raise ValueError('INPUT_PIXEL_COUNT')
    records=[];changed=[]
    for row in rows:
        n=row['number']-1;ox=n%8*128;oy=n//8*128
        palette=row['palette'];lookup={}
        for i,color in enumerate(palette):lookup.setdefault(color,i)
        pixels=bytearray(row['pixels']);count=0
        for y in range(128):
            for x in range(128):
                local=y*128+x;gx,gy=ox+x,oy+y;color=rgba[gy*1024+gx]
                if color not in lookup:raise ValueError('COLOR_NOT_IN_THIS_TILE_ORIGINAL_PALETTE')
                if color==palette[pixels[local]]:continue
                if not any(a<=gx<c and b<=gy<d for a,b,c,d in rectangles):
                    raise ValueError('PROTECTED_PIXEL_CHANGE')
                pixels[local]=lookup[color];count+=1
        final=row['raw'][:96]+encode(bytes(pixels),128,128,4)
        assert len(final)==len(row['raw']) and final[:96]==row['raw'][:96]
        assert decode(final[96:],128,128,4)==bytes(pixels)
        records.append(final)
        if count:changed.append(dict(number=row['number'],index=row['entry']['index'],changed_pixels=count))
    return records,changed


def load_png(path,rows,rectangles):
    im=Image.open(path)
    if im.format!='PNG':raise ValueError('INPUT_MUST_BE_PNG')
    if im.size!=(1024,1024):raise ValueError('INPUT_DIMENSIONS_MUST_BE1024X1024')
    return encode_candidate(im.size,list(im.convert('RGBA').get_flattened_data()),rows,rectangles)


def main():
    rows=source();regions=json.loads((ROOT/'workspace/graphics/translation/map_regions_analysis_20261024.json').read_text(encoding='utf-8'))
    rectangles=[r['conservative_source_rectangle'] for r in regions['regions']]
    original=ROOT/regions['source_mosaic']
    encoded,changed=load_png(original,rows,rectangles)
    assert not changed and encoded==[r['raw'] for r in rows]
    negatives=[]
    def reject(label,fn,expected):
        try:fn()
        except ValueError as e:
            assert str(e)==expected;negatives.append(dict(case=label,rejected=str(e)))
        else:raise AssertionError('Invalid input accepted:'+label)
    wrong=ROOT/'workspace/graphics/map_kr_drafts_20261024/imagegen_01.png'
    reject('actual_generated1254_square',lambda:load_png(wrong,rows,rectangles),'INPUT_DIMENSIONS_MUST_BE1024X1024')
    rgba=list(Image.open(original).convert('RGBA').get_flattened_data())
    bad=list(rgba);bad[60*1024+60]=(255,0,255,255)
    reject('unmapped_color_in_caption_region',lambda:encode_candidate((1024,1024),bad,rows,rectangles),'COLOR_NOT_IN_THIS_TILE_ORIGINAL_PALETTE')
    bad=list(rgba);bad[0]=next(c for c in rows[0]['palette'] if c!=rgba[0])
    reject('protected_corner',lambda:encode_candidate((1024,1024),bad,rows,rectangles),'PROTECTED_PIXEL_CHANGE')
    reject('truncated_pixels',lambda:encode_candidate((1024,1024),rgba[:-1],rows,rectangles),'INPUT_PIXEL_COUNT')
    report=dict(status='PASS64_EXACT_SOURCE_RECORD_ROUNDTRIPS_AND4_REJECTIONS_NO_KOREAN_MAP_INPUT',
        source_record_count=64,source_total_bytes=sum(len(r['raw']) for r in rows),
        header_palette_bytes_per_record=96,original_record_bytes_per_tile=8288,
        original_mosaic_sha256=digest(original.read_bytes()),original_all64_encoded_records_byte_equal=True,
        preserve_duplicate_palette_index_for_equal_colors=True,
        generated_image_sha256=digest(wrong.read_bytes()),generated_size=[1254,1254],negative_cases=negatives,
        resampling_or_palette_approximation=False,edited_image_files_emitted=False,
        in_memory_candidate_encoder_not_product_build_writer=True,
        allowed_rectangles_are_provisional_not_erase_masks=True,
        adopted_clean_background_and_final_edit_mask_available=False,
        valid_Korean_map_input_available=False,new_game_or_config_or_SSOT_bytes=0,release_eligible=False)
    save_json(ROOT/'qa/reports/map_texture_import_20261024.json',report)
    print('PASS64 full8288-byte source roundtrips/4 invalid inputs rejected;no edited image or game output.')


if __name__=='__main__':main()

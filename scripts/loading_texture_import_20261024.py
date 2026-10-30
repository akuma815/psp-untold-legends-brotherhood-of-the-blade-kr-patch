"""Strict PNG->original PSP texture encoding; never resize or invent palette colors."""
import json,struct
from PIL import Image
from survey import ROOT,digest,save_json
from ui_texture_inventory_20261024 import decode,encode

W,H=128,32
RECT=(16,4,112,28)
EXPECTED='22c6dd4b801ed5cf0be7ca9b0d430ae144954b8f8aeb72549ac0897040968284'


def source():
    idx=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf-8'));e=idx['entries'][5080]
    assert e['trailing_label_candidate']=='Textures\\Ui\\tex_ui_loading_0' and e['size_candidate']==5152 and e['sha256']==EXPECTED
    with (ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').open('rb') as f:f.seek(e['offset']);raw=f.read(5152)
    assert digest(raw)==EXPECTED
    header=struct.unpack_from('<8I',raw);assert header[4:6]==(W,H) and header[6]&0xffff==0x101 and header[7]==32
    palette=[tuple(raw[i:i+4]) for i in range(32,1056,4)];pixels=decode(raw[1056:],W,H,8)
    assert all(p[3]==255 for p in palette) and len(pixels)==W*H
    return e,raw,palette,pixels


def pack_pixels(size,rgba,raw,palette,original):
    if tuple(size)!=(W,H):raise ValueError('INPUT_DIMENSIONS_MUST_BE128X32')
    if len(rgba)!=W*H:raise ValueError('INPUT_PIXEL_COUNT')
    lookup={}
    for i,color in enumerate(palette):lookup.setdefault(color,i)
    result=bytearray(len(original))
    for pos,color in enumerate(rgba):
        if color not in lookup:raise ValueError('COLOR_NOT_IN_ORIGINAL_PALETTE')
        x,y=pos%W,pos//W
        # Identical colors retain their original index, including duplicate palette entries.
        result[pos]=original[pos] if color==palette[original[pos]] else lookup[color]
        if not(RECT[0]<=x<RECT[2] and RECT[1]<=y<RECT[3]) and result[pos]!=original[pos]:
            raise ValueError('PROTECTED_PIXEL_CHANGE')
    packed=encode(bytes(result),W,H,8);output=raw[:1056]+packed
    assert len(output)==len(raw)==5152 and output[:1056]==raw[:1056]
    assert decode(output[1056:],W,H,8)==bytes(result)
    return output


def load_png(path,raw,palette,original):
    im=Image.open(path)
    if im.format!='PNG':raise ValueError('INPUT_MUST_BE_PNG')
    # Read only. No scaling,cropping,palette approximation or image rewriting.
    if im.size!=(W,H):raise ValueError('INPUT_DIMENSIONS_MUST_BE128X32')
    rgba=list(im.convert('RGBA').get_flattened_data())
    return pack_pixels(im.size,rgba,raw,palette,original)


def main():
    entry,raw,palette,original=source()
    preview=ROOT/'workspace/graphics/ui_additional_candidates_20261024/5080_tex_ui_loading_0.png'
    assert load_png(preview,raw,palette,original)==raw
    nonblack=[(p%W,p//W) for p,i in enumerate(original) if palette[i][:3]!=(0,0,0)]
    bbox=(min(x for x,y in nonblack),min(y for x,y in nonblack),max(x for x,y in nonblack)+1,max(y for x,y in nonblack)+1)
    assert RECT[0]<=bbox[0]<bbox[2]<=RECT[2] and RECT[1]<=bbox[1]<bbox[3]<=RECT[3]
    rgba=[palette[i] for i in original];negatives=[]
    def reject(label,fn,expected):
        try:fn()
        except ValueError as e:assert str(e)==expected;negatives.append(dict(case=label,rejected=str(e)))
        else:raise AssertionError('Negative case accepted:'+label)
    draft=ROOT/'workspace/graphics/loading_kr_drafts_20261024/imagegen_01.png'
    reject('actual_imagegen_wrong_dimensions',lambda:load_png(draft,raw,palette,original),'INPUT_DIMENSIONS_MUST_BE128X32')
    invalid=list(rgba);invalid[4*W+16]=(255,0,255,255);assert invalid[4*W+16] not in palette
    reject('synthetic_unmapped_color',lambda:pack_pixels((W,H),invalid,raw,palette,original),'COLOR_NOT_IN_ORIGINAL_PALETTE')
    outside=list(rgba);outside[0]=next(c for c in palette if c[:3]!=(0,0,0))
    reject('synthetic_protected_corner',lambda:pack_pixels((W,H),outside,raw,palette,original),'PROTECTED_PIXEL_CHANGE')
    reject('synthetic_truncated_input',lambda:pack_pixels((W,H),rgba[:-1],raw,palette,original),'INPUT_PIXEL_COUNT')
    report=dict(status='PASS_STRICT_SOURCE_ROUNDTRIP_AND4_NEGATIVE_INPUTS_NO_KOREAN_ASSET_SELECTED',
        source_WAD_index=5080,source_WAD_offset=entry['offset'],source_record_sha256=EXPECTED,source_record_bytes=5152,
        original_preview_roundtrip_all5152_equal=True,protected_header_and_palette_bytes=1056,palette_entries=256,
        palette_unique_RGBA=len(set(palette)),permitted_palette='Original256 raw entries only;duplicate-color index preserved for unchanged pixels.',
        source_nonblack_bbox=list(bbox),proposed_edit_rectangle=list(RECT),outside_rectangle_equal_required=True,
        background_reference='Opaque black;all source pixels outside original glyph bbox are black;uniform color identity is reproducible. No text-free image file fabricated.',
        background_reference_not_final_human_layout=True,negative_cases=negatives,
        no_scaling_or_palette_approximation=True,no_edited_image_file_created=True,
        valid_Korean_input_not_yet_available=True,source_canvas_and_text_identity_need_review=True,
        new_game_SSOT_or_config_bytes=0,release_eligible=False)
    save_json(ROOT/'qa/reports/loading_texture_import_20261024.json',report)
    print('PASS original full5152 roundtrip;actual wrong-size draft+3 synthetic invalid inputs rejected;no scaling/game writes.')


if __name__=='__main__':main()

"""Approved exact-size Korean loading raster and source-derived schema15 layer."""
import argparse,copy,io,json
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from loading_texture_import_20261024 import source,pack_pixels,load_png,RECT
from marker_footer_20261024 import CONFIG as PARENT,derive_markers

NAME='loading_korean_20261024';CONFIG=f'development_{NAME}.json'
WORK=ROOT/'workspace/graphics/loading_kr_20261024'
FONT='workspace/font/morpheus_stage003/source_galmuri_2.40.4/Galmuri11.ttf'
FONT_SHA='e24256f42e43713d2ea086a1e1669d78b968f5b3cc547e5c157f0606ffa5def1'
TEXT='불러오는 중'
WAD='PSP_GAME/USRDIR/resource.wad'


def render():
    entry,original,palette,indices=source();fontpath=ROOT/FONT
    assert digest(fontpath.read_bytes())==FONT_SHA
    cmap=TTFont(fontpath).getBestCmap();assert all(ord(c) in cmap for c in TEXT)
    font=ImageFont.truetype(str(fontpath),16);bbox=font.getbbox(TEXT)
    width,height=bbox[2]-bbox[0],bbox[3]-bbox[1]
    x=(128-width)//2-bbox[0];y=(32-height)//2-bbox[1]
    black=(0,0,0,255);white=max(palette,key=lambda c:sum(c[:3]))
    assert black in palette and white==(230,220,222,255)
    im=Image.new('RGBA',(128,32),black);d=ImageDraw.Draw(im);d.fontmode='1';d.text((x,y),TEXT,font=font,fill=white)
    pixels=list(im.get_flattened_data());assert set(pixels)=={black,white}
    record=pack_pixels(im.size,pixels,original,palette,indices)
    assert record[:1056]==original[:1056] and len(record)==5152
    foreground=[(p%128,p//128) for p,c in enumerate(pixels) if c!=black]
    ink=[min(a for a,b in foreground),min(b for a,b in foreground),max(a for a,b in foreground)+1,max(b for a,b in foreground)+1]
    assert RECT[0]<=ink[0]<ink[2]<=RECT[2] and RECT[1]<=ink[1]<ink[3]<=RECT[3]
    meta=dict(text=TEXT,font=FONT,font_sha256=FONT_SHA,font_size=16,fontmode='1',text_origin=[x,y],ink_bbox=ink,
        editable_rectangle=list(RECT),source_record_sha256=digest(original),record_sha256=digest(record),
        source_record_bytes=5152,protected_header_palette_bytes=1056,packed_pixel_bytes=4096,
        RGBA_pixels_sha256=digest(im.tobytes()),ink_RGBA=list(white),new_palette_colors=0,palette_bytes_equal=True,
        outside_edit_rectangle_equal=True,all_canvas_alpha255=True,code_rasterization_explicitly_user_requested=True)
    return im,record,meta,entry


def configuration():
    approval=WORK/'approval.json';a=json.loads(approval.read_text(encoding='utf-8'))
    assert a['status']=='approved_exact_wording_and_python_existing_font_method' and a['text']==TEXT
    im,raw,meta,entry=render();png=WORK/'loading_kr_128x32.png'
    assert load_png(png,*source()[1:])==raw
    assert (WORK/'loading_kr_128x32.bin').read_bytes()==raw
    return dict(schema_version=15,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        graphic=dict(WAD_index=5080,WAD_offset=entry['offset'],source_record_sha256=meta['source_record_sha256'],
            original_record_bytes=5152,header_palette_preserved_bytes=1056,pixel_payload_bytes=4096,
            png=png.relative_to(ROOT).as_posix(),png_sha256=digest(png.read_bytes()),
            texture=(WORK/'loading_kr_128x32.bin').relative_to(ROOT).as_posix(),texture_sha256=digest(raw),
            render=meta,approval=approval.relative_to(ROOT).as_posix(),approval_sha256=digest(approval.read_bytes())),
        text_SSOT_changed=False,full_translation_or_release_approval=False)


def derive_loading(cfg):
    assert cfg==configuration();parent=json.loads((ROOT/'config'/PARENT).read_text(encoding='utf-8'))
    plan,outputs=derive_markers(parent);plan=copy.deepcopy(plan);outputs=dict(outputs)
    _,record,meta,entry=render();_,source_record,_,_=source()
    off=entry['offset']+1056;end=off+4096;before=outputs[WAD]
    assert before[entry['offset']:entry['offset']+5152]==source_record
    for w in plan['writes']:
        if w['path']==WAD:assert end<=w['offset'] or off>=w['offset']+w['size'],'Overlapping WAD writer'
    final=before[:off]+record[1056:]+before[end:]
    assert len(final)==len(before) and final[:off]==before[:off] and final[end:]==before[end:]
    outputs[WAD]=final
    plan['writes'].append(dict(owner='User-requested exact Korean loading raster;Galmuri11 16px',path=WAD,offset=off,size=4096,
        expected_sha256=digest(source_record[1056:]),final_sha256=digest(record[1056:]),
        derivation='Only index5080 swizzled8bpp pixels;original1056 header/palette bytes and other WAD bytes unchanged.'))
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['korean_loading_raster']=dict(meta,WAD_offset=entry['offset'],wording_method_user_approved=True,
        full_layout_human_approval=False,new_native_validation_pending=True,release_eligible=False)
    return plan,outputs


def prepare(recover=False):
    approval=dict(status='approved_exact_wording_and_python_existing_font_method',date='2026-10-24',text=TEXT,
        question='로딩 문구 ‘불러오는 중’은 작은 UI 이미지이므로, Python과 기존 한글 글꼴로 정확한 128×32 픽셀 이미지로 제작할까요? 이미지 생성 초안은 규격을 지키지 못했습니다. 문구와 원래 팔레트·배경은 유지하는 제안입니다.',
        answer='Python·기존 한글 글꼴로 정확한 규격 제작 (권장)',scope='Only loading_0/index5080 Korean wording and exact-size existing-font method;preserve palette/background/container.',
        full_layout_or_translation_or_release_approval=False)
    if WORK.exists():
        assert recover and sorted(p.name for p in WORK.iterdir())==['approval.json'],'Protected prepare cannot be replayed'
        assert json.loads((WORK/'approval.json').read_text(encoding='utf-8'))==approval
    else:
        assert not recover
        WORK.mkdir(parents=True)
        protected_write(WORK/'approval.json',json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
    im,record,meta,entry=render();im.save(WORK/'loading_kr_128x32.png')
    (WORK/'loading_kr_128x32.bin').write_bytes(record)
    protected_write(WORK/'render.json',json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    background=Image.new('RGBA',(128,32),(0,0,0,255));background.save(WORK/'adopted_black_background_128x32.png')
    im.resize((512,128),Image.Resampling.NEAREST).save(WORK/'analysis_only_4x.png')
    cfg=configuration();protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    save_json(ROOT/'qa/reports/loading_korean_20261024_raster.json',dict(status='PASS128X32_USER_REQUESTED_FONT_RASTER_MECHANICAL_CHECKS_NATIVE_PENDING',
        **meta,PNG_sha256=digest((WORK/'loading_kr_128x32.png').read_bytes()),config_sha256=digest((ROOT/'config'/CONFIG).read_bytes()),
        adopted_background_sha256=digest((WORK/'adopted_black_background_128x32.png').read_bytes()),new_game_build=0,release_eligible=False))
    print('PASS128x32 Galmuri11 Korean raster;original palette/header and protected pixels preserved;schema15 prepared;native pending.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','resume_prepare']);a=p.parse_args();prepare(a.action=='resume_prepare')

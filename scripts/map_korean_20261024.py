"""User-requested exact map raster; frozen inpaint background, source palettes/containers."""
import argparse,copy,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from fontTools.ttLib import TTFont
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from loading_korean_20261024 import FONT,FONT_SHA,CONFIG as PARENT,WAD
from map_texture_import_20261024 import source,encode_candidate

NAME='map_korean_20261024';CONFIG=f'development_{NAME}.json'
WORK=ROOT/'workspace/graphics/map_kr_20261024'
REGIONS=ROOT/'workspace/graphics/translation/map_regions_analysis_20261024.json'


def regions():return json.loads(REGIONS.read_text(encoding='utf-8'))['regions']


def original():
    path=ROOT/'workspace/graphics/map_source_review_20261024/analysis_english_map1024.png'
    im=Image.open(path).convert('RGBA');assert im.size==(1024,1024)
    rows=source();records,changes=encode_candidate(im.size,list(im.get_flattened_data()),rows,[])
    assert not changes and records==[r['raw'] for r in rows]
    return im,rows


def quantize_masked(a,mask,rows):
    """Choose existing per-tile colors only, preserving every unmasked source pixel."""
    result=a.copy()
    for row in rows:
        n=row['number']-1;x=n%8*128;y=n//8*128;m=mask[y:y+128,x:x+128]
        if not m.any():continue
        colors=np.array(row['palette'],dtype=np.int32);patch=result[y:y+128,x:x+128]
        values=patch[m].astype(np.int32)
        distance=((values[:,None,:]-colors[None,:,:])**2).sum(axis=2)
        patch[m]=colors[distance.argmin(axis=1)].astype(np.uint8)
    return result


def prepare_background():
    assert not WORK.exists(),'Protected preparation already exists'
    im,rows=original();a=np.asarray(im).copy();mask=np.zeros((1024,1024),dtype=bool)
    metadata=[]
    for r in regions():
        x0,y0,x1,y1=r['conservative_source_rectangle'];patch=a[y0:y1,x0:x1]
        lum=(patch[:,:,:3].astype(np.int32)*np.array([299,587,114])).sum(axis=2)//1000
        seed=Image.fromarray(((lum<110)*255).astype(np.uint8))
        m=np.asarray(seed.filter(ImageFilter.MaxFilter(5)))!=0
        assert m.any();mask[y0:y1,x0:x1]=m
        # Deterministic local harmonic fill. Original non-mask pixels are fixed
        # boundary conditions. Save/adopt the result; product builds never inpaint.
        value=patch[:,:,:3].astype(np.float64).copy()
        value[m]=np.median(value[~m],axis=0)
        for _ in range(800):
            pad=np.pad(value,((1,1),(1,1),(0,0)),mode='edge')
            average=(pad[:-2,1:-1]+pad[2:,1:-1]+pad[1:-1,:-2]+pad[1:-1,2:])/4
            value[m]=average[m]
        patch[m,:3]=np.clip(np.rint(value[m]),0,255).astype(np.uint8)
        metadata.append(dict(id=r['id'],seed_threshold_luma110=True,dilation_radius=2,mask_pixels=int(m.sum()),iterations=800))
    original_pixels=np.asarray(im);a=quantize_masked(a,mask,rows)
    assert np.all(a[~mask]==original_pixels[~mask])
    WORK.mkdir(parents=True)
    approval=dict(date='2026-10-24',status='approved_python_existing_font_exact_size_map_method',
        answer='Python·기존 글꼴로 정확한 규격 제작 (권장)',
        scope='Six map labels/eleven occurrences;freeze recovered original ink background;preserve terrain,paths,nodes,logo and original palettes.',
        full_graphic_layout_or_translation_or_release_approval=False)
    protected_write(WORK/'approval.json',json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
    Image.fromarray(a).save(WORK/'background_candidate1024.png')
    Image.fromarray((mask*255).astype(np.uint8)).save(WORK/'source_ink_mask1024.png')
    overlay=original_pixels.copy();overlay[mask]=[255,40,40,255]
    Image.fromarray(overlay).save(WORK/'analysis_only_ink_mask_overlay.png')
    review=dict(status='BACKGROUND_AND_SOURCE_INK_MASK_CANDIDATE_VISUAL_REVIEW_PENDING',
        source_map_sha256=digest(im.tobytes()),mask_pixels=int(mask.sum()),regions=metadata,
        background_sha256=digest((WORK/'background_candidate1024.png').read_bytes()),
        mask_sha256=digest((WORK/'source_ink_mask1024.png').read_bytes()),
        outside_mask_RGBA_equal=True,all_colors_from_original_per_tile_palettes=True,
        source_region_rectangles_not_used_as_whole_erase_masks=True,background_human_approved=False,release_eligible=False)
    protected_write(WORK/'background_candidate.json',json.dumps(review,indent=2)+'\n')
    render(save=True)
    print('Prepared1024 source-ink mask/frozen background candidate/exact Galmuri Korean preview;visual review pending.')


def render(save=False):
    im,rows=original();src=np.asarray(im);bg=Image.open(WORK/'background_candidate1024.png').convert('RGBA')
    background=np.asarray(bg).copy();oldmask=np.asarray(Image.open(WORK/'source_ink_mask1024.png'))!=0
    assert np.all(background[~oldmask]==src[~oldmask])
    assert digest((ROOT/FONT).read_bytes())==FONT_SHA
    cmap=TTFont(ROOT/FONT).getBestCmap();ink=Image.new('L',(1024,1024));draw=ImageDraw.Draw(ink);draw.fontmode='1'
    notes=[]
    for r in regions():
        text=r['working_korean'];text=text.replace(' ','\n') if r['id']=='map-caption-07' else text
        assert all(ord(c) in cmap for c in text if c!='\n')
        font=ImageFont.truetype(str(ROOT/FONT),r['candidate_font_size']);rect=r['conservative_source_rectangle']
        box=draw.multiline_textbbox((0,0),text,font=font,spacing=2,align='center')
        w,h=box[2]-box[0],box[3]-box[1];x=(rect[0]+rect[2]-w)//2-box[0];y=(rect[1]+rect[3]-h)//2-box[1]
        assert w+2<=rect[2]-rect[0] and h+2<=rect[3]-rect[1]
        draw.multiline_text((x,y),text,font=font,spacing=2,align='center',fill=255)
        notes.append(dict(id=r['id'],text=text,font_size=r['candidate_font_size'],origin=[x,y],ink_size=[w,h]))
    core=np.asarray(ink)!=0;outline=np.asarray(ink.filter(ImageFilter.MaxFilter(3)))!=0
    out=background.copy()
    for row in rows:
        n=row['number']-1;x=n%8*128;y=n//8*128;palette=row['palette']
        dark=min(palette,key=lambda c:sum(c[:3]));light=max(palette,key=lambda c:sum(c[:3]))
        patch=out[y:y+128,x:x+128];patch[outline[y:y+128,x:x+128]]=light;patch[core[y:y+128,x:x+128]]=dark
    allowed=oldmask|outline
    assert np.all(out[~allowed]==src[~allowed])
    rectangles=[r['conservative_source_rectangle'] for r in regions()]
    allowed_rect=np.zeros((1024,1024),dtype=bool)
    for a,b,c,d in rectangles:allowed_rect[b:d,a:c]=True
    assert not np.any(allowed&~allowed_rect)
    records,changed=encode_candidate((1024,1024),list(Image.fromarray(out).get_flattened_data()),rows,rectangles)
    meta=dict(size=[1024,1024],font=FONT,font_sha256=FONT_SHA,labels=notes,changed_tiles=changed,
        changed_RGBA_pixels=int(np.any(out!=src,axis=2).sum()),allowed_mask_pixels=int(allowed.sum()),
        outside_exact_ink_and_cleanup_mask_equal=True,source_header_palette_all64_equal=True,
        original_per_tile_palette_only=True,logo_region_unchanged=bool(np.all(out[829:1004,781:1024]==src[829:1004,781:1024])),
        final_layout_human_approval=False,release_eligible=False)
    assert meta['logo_region_unchanged']
    if save:
        Image.fromarray(out).save(WORK/'map_korean_candidate1024.png')
        Image.fromarray((allowed*255).astype(np.uint8)).save(WORK/'allowed_changes_mask1024.png')
        protected_write(WORK/'render_candidate.json',json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
        # Full-sized local triptych is analysis only, not an input texture.
        sheet=Image.new('RGBA',(3072,1024));sheet.paste(im,(0,0));sheet.paste(bg,(1024,0));sheet.paste(Image.fromarray(out),(2048,0))
        sheet.save(WORK/'analysis_only_before_background_korean.png')
    return Image.fromarray(out),records,meta,rows


def configuration():
    a=json.loads((WORK/'approval.json').read_text(encoding='utf-8'))
    assert a['status']=='approved_python_existing_font_exact_size_map_method'
    adoption=json.loads((WORK/'background_adoption.json').read_text(encoding='utf-8'))
    assert adoption['status']=='agent_visually_adopted_development_background_not_human_final_layout'
    for name,key in [('background_candidate1024.png','background_sha256'),('source_ink_mask1024.png','source_ink_mask_sha256')]:
        assert digest((WORK/name).read_bytes())==adoption[key]
    im,records,meta,rows=render()
    assert list(im.get_flattened_data())==list(Image.open(WORK/'map_korean_candidate1024.png').convert('RGBA').get_flattened_data())
    return dict(schema_version=16,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        map=dict(approval=(WORK/'approval.json').relative_to(ROOT).as_posix(),approval_sha256=digest((WORK/'approval.json').read_bytes()),
            background_adoption=(WORK/'background_adoption.json').relative_to(ROOT).as_posix(),background_adoption_sha256=digest((WORK/'background_adoption.json').read_bytes()),
            source_regions_sha256=digest(REGIONS.read_bytes()),PNG_sha256=digest((WORK/'map_korean_candidate1024.png').read_bytes()),
            render=meta,record_sha256=[digest(r) for r in records]),
        text_SSOT_changed=False,full_translation_or_release_approval=False)


def derive_map(cfg):
    assert cfg==configuration()
    from loading_korean_20261024 import derive_loading
    parent=json.loads((ROOT/'config'/PARENT).read_text(encoding='utf-8'));plan,outputs=derive_loading(parent)
    plan=copy.deepcopy(plan);outputs=dict(outputs);before=outputs[WAD];wad=bytearray(before)
    _,records,meta,rows=render();changed=[]
    for row,record in zip(rows,records):
        e=row['entry'];off=e['offset'];assert before[off:off+8288]==row['raw']
        if record==row['raw']:continue
        start,end=off+96,off+8288
        for w in plan['writes']:
            if w['path']==WAD:assert end<=w['offset'] or start>=w['offset']+w['size'],'Overlapping map WAD writer'
        wad[start:end]=record[96:]
        plan['writes'].append(dict(owner=f'User-requested exact Korean map tile{row["number"]:02}',path=WAD,offset=start,size=8192,
            expected_sha256=digest(row['raw'][96:]),final_sha256=digest(record[96:]),
            derivation='Only source4bpp pixels;original96-byte header/palette and all pixels outside frozen cleanup/new-ink mask preserved.'))
        changed.append(dict(index=e['index'],offset=start,size=8192))
    outputs[WAD]=bytes(wad);assert len(wad)==len(before)
    allowed=sorted((e['offset'],e['offset']+e['size']) for e in changed);cursor=0
    for a,z in allowed:assert wad[cursor:a]==before[cursor:a];cursor=z
    assert wad[cursor:]==before[cursor:]
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['korean_map_raster']=dict(meta,changed_record_extents=changed,native_verification_pending=True,release_eligible=False)
    return plan,outputs


def select():
    assert not (WORK/'background_adoption.json').exists()
    adoption=dict(status='agent_visually_adopted_development_background_not_human_final_layout',
        background_sha256=digest((WORK/'background_candidate1024.png').read_bytes()),
        source_ink_mask_sha256=digest((WORK/'source_ink_mask1024.png').read_bytes()),
        visual_review='Inspected source mask overlay,clean background and exact Korean raster at1024. Eleven old captions removed;mask does not cover location nodes,roads,terrain or logo. Local paper fill remains a development candidate;human final layout approval false.',
        frozen_background_is_build_input=True,build_never_repeats_inpainting=True,
        palette_policy='Harmonic fill values quantized only inside source ink mask to each original tile palette;header/palette bytes unchanged. New Hangul uses existing darkest/lightest palette entries.',
        final_human_layout_or_release_approval=False)
    protected_write(WORK/'background_adoption.json',json.dumps(adoption,indent=2)+'\n')
    cfg=configuration();protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    audit_raster()
    print('Selected development-only frozen background/exact Korean raster;schema16 ready;native pending.')


def audit_raster():
    cfg=configuration();assert json.loads((ROOT/'config'/CONFIG).read_text(encoding='utf-8'))==cfg
    save_json(ROOT/'qa/reports/map_korean_20261024_raster.json',dict(status='PASS_EXACT1024_SOURCE_PALETTES_AND_FROZEN_MASKS_NATIVE_PENDING',
        config_sha256=digest((ROOT/'config'/CONFIG).read_bytes()),**cfg['map']['render']))
    print('PASS frozen map inputs/schema16/exact record derivation;native pending.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','select','audit_raster']);a=p.parse_args()
    globals()[a.action]() if a.action!='prepare' else prepare_background()

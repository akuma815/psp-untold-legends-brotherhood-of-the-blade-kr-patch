"""Original PNG -> built-in generated lettering -> exact source-paletted map candidate."""
import argparse,copy,json
from collections import deque
import numpy as np
from PIL import Image,ImageFilter
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from map_korean_20261024 import original,regions,WORK as PREVIOUS
from map_texture_import_20261024 import encode_candidate
from loading_korean_20261024 import CONFIG as PARENT,WAD,derive_loading

NAME='map_generated_korean_20261024';CONFIG=f'development_{NAME}.json'
WORK=ROOT/'workspace/graphics/map_generated_kr_20261024_v4'
GENERATED=ROOT/'workspace/graphics/map_kr_drafts_20261024/imagegen_01.png'
GEN_SHA='041cdf45739285c9122ce1c3198b9b1b16e4ad5a8a308f862e2780656cc7253a'
LETTER_WINDOWS=[[[50,58,224,109]],[[600,101,655,128]],[[411,165,490,192]],
    [[304,383,378,411]],[[608,383,686,407]],[[902,422,959,450]],
    [[151,554,255,580],[188,582,214,610]],[[594,665,667,697]],
    [[791,679,865,706]],[[219,761,235,777],[230,757,243,784],[244,759,267,784]],[[188,906,324,940]]]


def components(mask):
    seen=np.zeros_like(mask,dtype=bool);out=np.zeros_like(mask,dtype=bool);h,w=mask.shape
    for y,x in zip(*np.nonzero(mask)):
        if seen[y,x]:continue
        q=deque([(int(x),int(y))]);seen[y,x]=True;points=[]
        while q:
            a,b=q.popleft();points.append((a,b))
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                c,d=a+dx,b+dy
                if 0<=c<w and 0<=d<h and mask[d,c] and not seen[d,c]:seen[d,c]=True;q.append((c,d))
        if len(points)>=5:
            for a,b in points:out[b,a]=True
    return out


def prepare():
    assert not WORK.exists();assert digest(GENERATED.read_bytes())==GEN_SHA
    im,rows=original();source=np.asarray(im);bg=Image.open(PREVIOUS/'background_candidate1024.png').convert('RGBA')
    oldmask=np.asarray(Image.open(PREVIOUS/'source_ink_mask1024.png'))!=0
    assert np.all(np.asarray(bg)[~oldmask]==source[~oldmask])
    gen=Image.open(GENERATED).convert('RGBA');assert gen.size==(1254,1254)
    normalized=gen.resize((1024,1024),Image.Resampling.LANCZOS)
    pixels=np.asarray(normalized);ink=Image.new('L',(1024,1024));notes=[]
    for region_number,r in enumerate(regions()):
        x0,y0,x1,y1=r['conservative_source_rectangle']
        # Recover the whole generated inscription even if it drifted a few pixels
        # from the requested slot, then fit its silhouette inside the original slot.
        margin=12;a,b,c,d=max(0,x0-margin),max(0,y0-margin),min(1024,x1+margin),min(1024,y1+margin)
        patch=pixels[b:d,a:c,:3].astype(np.int32)
        lum=(patch*np.array([299,587,114])).sum(axis=2)//1000
        permitted=np.zeros(lum.shape,dtype=bool)
        for u,v,w,z in LETTER_WINDOWS[region_number]:
            permitted[max(0,v-b):min(d-b,z-b),max(0,u-a):min(c-a,w-a)]=True
        mask=components((lum<105)&permitted);ys,xs=np.nonzero(mask);assert len(xs)>0
        bounds=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
        glyph=Image.fromarray((mask*255).astype(np.uint8)).crop(bounds)
        original_size=glyph.size;maxw,maxh=x1-x0-4,y1-y0-4
        scale=min(1,maxw/glyph.width,maxh/glyph.height)
        if scale<1:glyph=glyph.resize((max(1,round(glyph.width*scale)),max(1,round(glyph.height*scale))),Image.Resampling.NEAREST)
        x=(x0+x1-glyph.width)//2;y=(y0+y1-glyph.height)//2;ink.paste(glyph,(x,y))
        notes.append(dict(id=r['id'],expected_text=r['working_korean'],generated_crop=[a,b,c,d],
            visually_bounded_letter_windows=LETTER_WINDOWS[region_number],
            recovered_ink_bbox=[a+bounds[0],b+bounds[1],a+bounds[2],b+bounds[3]],
            recovered_ink_size=list(original_size),adopted_ink_size=list(glyph.size),adopted_origin=[x,y],
            size_fitted_inside_original_slot=True,text_accuracy_visual_review_pending=True))
    core=np.asarray(ink)!=0;outline=np.asarray(ink.filter(ImageFilter.MaxFilter(3)))!=0
    out=np.asarray(bg).copy()
    for row in rows:
        n=row['number']-1;x=n%8*128;y=n//8*128;p=row['palette'];tile=out[y:y+128,x:x+128]
        tile[outline[y:y+128,x:x+128]]=max(p,key=lambda c:sum(c[:3]))
        tile[core[y:y+128,x:x+128]]=min(p,key=lambda c:sum(c[:3]))
    allowed=oldmask|outline;assert np.all(out[~allowed]==source[~allowed])
    rects=[r['conservative_source_rectangle'] for r in regions()]
    records,changed=encode_candidate((1024,1024),list(Image.fromarray(out).get_flattened_data()),rows,rects)
    assert np.all(out[829:1004,781:1024]==source[829:1004,781:1024])
    WORK.mkdir(parents=True)
    Image.fromarray(out).save(WORK/'map_korean_candidate1024.png');ink.save(WORK/'generated_ink_mask1024.png')
    Image.fromarray((allowed*255).astype(np.uint8)).save(WORK/'allowed_changes_mask1024.png')
    normalized.save(WORK/'analysis_only_normalized_generated1024.png')
    sheet=Image.new('RGBA',(1024,11*96));from PIL import ImageDraw
    draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(regions()):
        x0,y0,x1,y1=r['conservative_source_rectangle'];crop=Image.fromarray(out).crop((x0,y0,x1,y1))
        crop=crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST)
        sheet.paste(crop,(0,i*96));draw.text((400,i*96+8),r['id'],fill=(255,0,0))
    sheet.save(WORK/'analysis_only_label_strip2x.png')
    protected_write(WORK/'derivation.json',json.dumps(dict(
        status='GENERATED_LETTERING_TRANSFER_CANDIDATE_VISUAL_REVIEW_PENDING',
        user_direction='Original PNG -> generative translation -> reinsertion;Python used for exact size/palette/container preparation.',
        generator='built-in image_gen',generated_source=GENERATED.relative_to(ROOT).as_posix(),generated_sha256=GEN_SHA,
        full_prompt_receipt='workspace/graphics/map_kr_drafts_20261024/imagegen_01_receipt.json',
        generated_full_map_rejected_as_direct_input=True,normalized_generated_map_is_analysis_only=True,
        background=(PREVIOUS/'background_candidate1024.png').relative_to(ROOT).as_posix(),
        background_sha256=digest((PREVIOUS/'background_candidate1024.png').read_bytes()),
        transfer='Generated dark lettering silhouette only;source-normalized LANCZOS then native-slot fit of binary mask;existing darkest/lightest palette entries.',
        labels=notes,changed_tiles=changed,changed_pixels=int(np.any(out!=source,axis=2).sum()),
        protected_source_pixels_outside_exact_mask_equal=True,all_original_headers_palettes_retained=True,
        logo_unchanged=True,full_layout_or_release_human_approved=False,release_eligible=False),ensure_ascii=False,indent=2)+'\n')
    print('Prepared exact1024 candidate from generated Korean lettering;original terrain outside source cleanup/ink masks preserved;visual review pending.')


def frozen():
    im,rows=original();source=np.asarray(im)
    candidate=Image.open(WORK/'map_korean_candidate1024.png').convert('RGBA');assert candidate.size==(1024,1024)
    out=np.asarray(candidate);allowed=np.asarray(Image.open(WORK/'allowed_changes_mask1024.png'))!=0
    assert allowed.shape==(1024,1024) and np.all(out[~allowed]==source[~allowed])
    assert np.all(out[829:1004,781:1024]==source[829:1004,781:1024])
    records,changed=encode_candidate((1024,1024),list(candidate.get_flattened_data()),rows,[r['conservative_source_rectangle'] for r in regions()])
    return candidate,rows,records,changed


def configuration():
    adopted=json.loads((WORK/'adoption.json').read_text(encoding='utf-8'))
    assert adopted['status']=='agent_visually_adopted_generated_lettering_development_candidate'
    for name,sha in adopted['pinned_inputs'].items():assert digest((ROOT/name).read_bytes())==sha
    _,rows,records,changed=frozen()
    return dict(schema_version=17,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        generated_map=dict(adoption=(WORK/'adoption.json').relative_to(ROOT).as_posix(),
            adoption_sha256=digest((WORK/'adoption.json').read_bytes()),
            records=[dict(number=r['number'],index=r['entry']['index'],record_sha256=digest(data)) for r,data in zip(rows,records)],
            changed_tiles=changed,final_human_layout_approval=False),text_SSOT_changed=False,release_eligible=False)


def derive_generated(cfg):
    assert cfg==configuration();parent=json.loads((ROOT/'config'/PARENT).read_text(encoding='utf-8'))
    plan,outputs=derive_loading(parent);plan=copy.deepcopy(plan);outputs=dict(outputs)
    before=outputs[WAD];wad=bytearray(before);_,rows,records,changed=frozen();extents=[]
    for row,record in zip(rows,records):
        off=row['entry']['offset'];assert before[off:off+8288]==row['raw']
        if record==row['raw']:continue
        start,end=off+96,off+8288
        for w in plan['writes']:
            if w['path']==WAD:assert end<=w['offset'] or start>=w['offset']+w['size']
        wad[start:end]=record[96:];extents.append((start,end))
        plan['writes'].append(dict(owner=f'Generated Korean map lettering,tile{row["number"]:02}',path=WAD,offset=start,size=8192,
            expected_sha256=digest(row['raw'][96:]),final_sha256=digest(record[96:]),
            derivation='Frozen exact source-paletted PNG,generated lettering only;original header/palette/protected mask pixels unchanged.'))
    cursor=0
    for a,z in sorted(extents):assert wad[cursor:a]==before[cursor:a];cursor=z
    assert wad[cursor:]==before[cursor:] and len(wad)==len(before)
    outputs[WAD]=bytes(wad);plan['writes'].sort(key=lambda w:(w['path'],w['offset']))
    plan['diagnostic_input']=cfg;plan['generated_korean_map']=dict(changed_tiles=changed,full_layout_human_approved=False,native_verification_pending=True,release_eligible=False)
    return plan,outputs


def select():
    assert not (WORK/'adoption.json').exists();_,rows,records,changed=frozen()
    inputs=[WORK/'map_korean_candidate1024.png',WORK/'generated_ink_mask1024.png',WORK/'allowed_changes_mask1024.png',WORK/'derivation.json',
        GENERATED,PREVIOUS/'background_candidate1024.png',PREVIOUS/'source_ink_mask1024.png',PREVIOUS/'approval.json']
    adoption=dict(status='agent_visually_adopted_generated_lettering_development_candidate',
        user_direction='이미지를 png로 받은 후에 해당 이미지를 생성형으로 번역한 다음에 다시 삽입하는 방법은 안되는가?',
        pipeline='Source PNG -> built-in generated Korean map -> normalize for lettering extraction only ->11 bounded silhouettes ->frozen source-color map PNG ->4bpp containers. Original whole-map redraw never imported.',
        pinned_inputs={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in inputs},
        visual_review='Inspected all11 labels at2x native pixels;v1/v2 noisy masks andv3 clipped final syllable refinements retained;v4 removes nearby map geometry and restores complete Aven/Woodland Ring strokes. Dark generated ink is heavier than rejected Galmuri preview.',
        final_layout_human_approved=False,release_eligible=False)
    protected_write(WORK/'adoption.json',json.dumps(adoption,ensure_ascii=False,indent=2)+'\n')
    cfg=configuration();protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    save_json(ROOT/'qa/reports/map_generated_korean_20261024_raster.json',dict(status='PASS_FROZEN_GENERATED_LETTERING_EXACT1024_NATIVE_PENDING',
        changed_tiles=len(changed),label_occurrences=11,distinct_labels=6,header_palette_original=True,protected_pixels_equal=True,release_eligible=False))
    print('Selected development generated-lettering candidate;schema17 from schema15;exact1024/source palettes;native pending.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','select']);a=p.parse_args();globals()[a.action]()

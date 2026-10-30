"""Generated title-map captions; immutable source and frozen palette-constrained inputs."""
import argparse,copy,json,struct
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from ui_texture_inventory_20261024 import decode,encode
from loading_korean_20261024 import WAD
from map_generated_korean_20261024 import CONFIG as PARENT,derive_generated

NAME='title_geography_20261024';CONFIG='development_'+NAME+'.json'
WORK=ROOT/'workspace/graphics/title_geography_kr_20261024_v3'
RECTS=[(28,246,80,272),(374,221,473,256)]

def source():
    idx=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf-8'))['entries']
    entry=idx[5419]
    with (ROOT/'extracted/disc'/WAD).open('rb') as f:f.seek(entry['offset']);raw=f.read(entry['size_candidate'])
    assert digest(raw)==entry['sha256']=='4f2bd149ebf75bca7816fbf33936290475a769e82a2c3013181dfb0ce93d7475'
    assert len(raw)==263200 and struct.unpack_from('<4I',raw,16)==(512,512,257,32)
    palette=np.frombuffer(raw[32:1056],dtype=np.uint8).reshape(256,4)
    pixels=decode(raw[1056:],512,512,8);assert raw[:1056]+encode(pixels,512,512,8)==raw
    rgba=palette[np.frombuffer(pixels,dtype=np.uint8)].reshape(512,512,4)
    return entry,raw,palette,pixels,rgba

def inspect():
    _,_,_,_,rgba=source()
    gen=Image.open(WORK/'imagegen_01.png').convert('RGBA')
    print('generated size',gen.size)
    gen=gen.resize((512,512),Image.Resampling.LANCZOS);sheet=Image.new('RGBA',(620,240))
    for i,rect in enumerate(RECTS):
        patch=rgba[rect[1]:rect[3],rect[0]:rect[2]]
        l=(patch[:,:,:3].astype(int)*[299,587,114]).sum(axis=2)//1000
        print(i,'source_luma',np.percentile(l,[0,10,25,50,75,100]).tolist())
        crop=Image.fromarray(patch).resize((patch.shape[1]*3,patch.shape[0]*3),Image.Resampling.NEAREST)
        sheet.paste(crop,(0,i*120));crop=gen.crop(rect);sheet.paste(crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST),(310,i*120))
    sheet.save(WORK/'analysis_source_generated_3x.png')

def record_from_png(path):
    entry,raw,palette,pixels,original=source()
    im=Image.open(path).convert('RGBA');assert im.size==(512,512)
    rgba=np.asarray(im);allowed=np.asarray(Image.open(WORK/'allowed_mask512.png'))!=0
    assert np.array_equal(rgba[~allowed],original[~allowed])
    lookup={tuple(c):i for i,c in reversed(list(enumerate(palette.tolist())))}
    out=bytearray(pixels)
    for y,x in zip(*np.nonzero(np.any(rgba!=original,axis=2))):
        color=tuple(rgba[y,x]);assert color in lookup,'Unmapped palette color'
        out[y*512+x]=lookup[color]
    record=raw[:1056]+encode(bytes(out),512,512,8)
    assert len(record)==len(raw) and record[:1056]==raw[:1056]
    assert np.array_equal(palette[np.frombuffer(decode(record[1056:],512,512,8),dtype=np.uint8)].reshape(512,512,4),rgba)
    return entry,record

def prepare():
    assert not (WORK/'title_korean512.png').exists()
    entry,raw,palette,pixels,original=source()
    generated=Image.open(WORK/'imagegen_01.png').convert('RGBA');assert generated.size==(1254,1254)
    gen=np.asarray(generated.resize((512,512),Image.Resampling.LANCZOS))
    lum=lambda a:(a[:,:,:3].astype(np.int32)*[299,587,114]).sum(axis=2)//1000
    old=np.zeros((512,512),dtype=np.uint8);ink=old.copy()
    for x0,y0,x1,y1 in RECTS:
        old[y0:y1,x0:x1]=(lum(original[y0:y1,x0:x1])<27)*255
    from map_generated_korean_20261024 import components
    for x0,y0,x1,y1 in [(29,250,69,270),(386,229,456,256)]:
        ink[y0:y1,x0:x1]=components(lum(gen[y0:y1,x0:x1])<33)*255
    old=np.asarray(Image.fromarray(old).filter(ImageFilter.MaxFilter(3)))!=0
    clip=np.zeros((512,512),dtype=bool)
    for x0,y0,x1,y1 in RECTS:clip[y0:y1,x0:x1]=True
    old &= clip
    core=ink!=0;outline=(np.asarray(Image.fromarray(ink).filter(ImageFilter.MaxFilter(3)))!=0)&clip
    background=original.copy();rgb=original[:,:,:3].astype(np.float64)
    for _ in range(800):
        average=(np.roll(rgb,1,0)+np.roll(rgb,-1,0)+np.roll(rgb,1,1)+np.roll(rgb,-1,1))/4
        rgb[old]=average[old]
    colors=palette[:,:3].astype(np.int32)
    def quantize(values):
        values=np.rint(values).astype(np.int32)
        return palette[((values[:,None,:]-colors[None,:,:])**2).sum(axis=2).argmin(axis=1)]
    background[old]=quantize(rgb[old])
    candidate=background.copy()
    dark=palette[((colors-[11,3,5])**2).sum(axis=1).argmin()]
    light=palette[((colors-[180,163,120])**2).sum(axis=1).argmin()]
    candidate[outline]=light;candidate[core]=dark
    allowed=old|outline
    assert np.array_equal(candidate[~allowed],original[~allowed])
    Image.fromarray(background).save(WORK/'adopted_local_background512.png')
    Image.fromarray(old.astype(np.uint8)*255).save(WORK/'old_ink_cleanup_mask512.png')
    Image.fromarray(ink).save(WORK/'generated_letter_mask512.png')
    Image.fromarray(allowed.astype(np.uint8)*255).save(WORK/'allowed_mask512.png')
    Image.fromarray(candidate).save(WORK/'title_korean512.png')
    _,record=record_from_png(WORK/'title_korean512.png')
    (WORK/'title_korean512.bin').write_bytes(record)
    sheet=Image.new('RGBA',(620,240))
    for i,(x0,y0,x1,y1) in enumerate(RECTS):
        patch=Image.fromarray(candidate).crop((x0,y0,x1,y1));sheet.paste(patch.resize((patch.width*3,patch.height*3),Image.Resampling.NEAREST),(0,i*120))
        mask=Image.fromarray(old.astype(np.uint8)*255).crop((x0,y0,x1,y1));sheet.paste(mask.resize((mask.width*3,mask.height*3),Image.Resampling.NEAREST),(310,i*120))
    sheet.save(WORK/'analysis_candidate_cleanup_3x.png')
    receipt=dict(generator='built-in image_gen',source='workspace/graphics/ui_source_candidates_20261024/5419_tex_ui_menu_splash_0.png',
        generated_source='C:/Users/akuma/.codex/generated_images/01a144f9-078e-7992-9d6a-e42ffa5d54f9/exec-ea33ce6b-3843-408d-a448-ba6f515e55e5.png',
        prompt=(WORK/'prompt.txt').read_text(encoding='utf-8'),requested_size=[512,512],actual_size=[1254,1254],
        generated_sha256=digest((WORK/'imagegen_01.png').read_bytes()),direct_whole_generated_import=False,
        normalization='Analysis512 coordinate space only;extract dark generated Korean silhouettes in two original caption slots. Final game texture comes from immutable original,local frozen cleanup and transferred generated ink.',release_eligible=False)
    save_json(WORK/'imagegen_receipt.json',receipt)
    save_json(WORK/'preparation.json',dict(status='FROZEN_TITLE_MAP_CAPTIONS_VISUAL_REVIEW_PENDING',
        captions=['아벤','황무지'],rectangles=RECTS,old_ink_luma_threshold=27,cleanup_dilation=3,
        background='adopted_local_background512.png',background_method='800 fixed-boundary Jacobi iterations only inside old English ink mask,then original256-color palette quantization',
        changed_pixels=int(np.any(candidate!=original,axis=2).sum()),new_palette_colors=0,protected_outside_mask_equal=True,
        logo_and_other_clipped_English_unchanged=True,header_palette1056bytes_equal=True,full_human_layout_accepted=False,release_eligible=False))
    print('Prepared2 generated title-map captions,exact512/8bpp/source palette;visual review pending.')

def configuration():
    adoption=json.loads((WORK/'adoption.json').read_text(encoding='utf-8'))
    for p,sha in adoption['pinned_inputs'].items():assert digest((ROOT/p).read_bytes())==sha
    entry,record=record_from_png(WORK/'title_korean512.png')
    assert record==(WORK/'title_korean512.bin').read_bytes()
    return dict(schema_version=18,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        title_map=dict(index=5419,record_sha256=digest(record),adoption=(WORK/'adoption.json').relative_to(ROOT).as_posix(),
            adoption_sha256=digest((WORK/'adoption.json').read_bytes()),captions=['아벤','황무지'],final_human_layout_accepted=False),
        main_text_SSOT_changed=False,release_eligible=False)

def select():
    assert not (WORK/'adoption.json').exists()
    files=['imagegen_01.png','prompt.txt','imagegen_receipt.json','title_korean512.png','title_korean512.bin',
        'adopted_local_background512.png','old_ink_cleanup_mask512.png','generated_letter_mask512.png','allowed_mask512.png','preparation.json']
    save_json(WORK/'adoption.json',dict(status='AGENT_VISUALLY_ADOPTED_TWO_TITLE_MAP_CAPTIONS_DEVELOPMENT',
        visual_review='Aven and Badlands generated silhouettes readable;old English masks and final512 image reviewed;logo,far-left clipped inscription,padding and nonmask pixels preserved.',
        pinned_inputs={(WORK/f).relative_to(ROOT).as_posix():digest((WORK/f).read_bytes()) for f in files},
        human_final_layout_accepted=False,release_eligible=False))
    protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    print('Selected schema18 title-map2 captions;development only.')

def derive_title(cfg):
    assert cfg==configuration()
    parent=json.loads((ROOT/'config'/PARENT).read_text(encoding='utf-8'))
    plan,outputs=derive_generated(parent);plan=copy.deepcopy(plan);outputs=dict(outputs)
    entry,raw,_,_,_=source();_,record=record_from_png(WORK/'title_korean512.png')
    start=entry['offset']+1056;end=start+262144;before=outputs[WAD]
    assert before[entry['offset']:end]==raw
    for w in plan['writes']:
        if w['path']==WAD:assert end<=w['offset'] or start>=w['offset']+w['size']
    final=before[:start]+record[1056:]+before[end:]
    assert len(final)==len(before) and final[:start]==before[:start] and final[end:]==before[end:]
    outputs[WAD]=final
    plan['writes'].append(dict(owner='Generated Korean2 title-map captions',path=WAD,offset=start,size=262144,
        expected_sha256=digest(raw[1056:]),final_sha256=digest(record[1056:]),derivation='Frozen source-palette512 PNG;only old ink cleanup/generated lettering masks changed;original1056 header/palette and protected pixels preserved.'))
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['title_map_captions']=dict(captions=['아벤','황무지'],original_logo_preserved=True,native_pending=True,release_eligible=False)
    return plan,outputs

def mechanical():
    import io
    entry,raw,palette,pixels,original=source()
    candidate=Image.open(WORK/'title_korean512.png').convert('RGBA')
    _,record=record_from_png(WORK/'title_korean512.png')
    assert record==(WORK/'title_korean512.bin').read_bytes()
    rejected=[]
    bad_dimension=Image.open(WORK/'imagegen_01.png')
    bad_protected=candidate.copy();bad_protected.putpixel((0,0),tuple(palette[100]))
    allowed=np.asarray(Image.open(WORK/'allowed_mask512.png'))!=0;y,x=next(zip(*np.nonzero(allowed)))
    bad_palette=candidate.copy();assert (255,0,255,255) not in map(tuple,palette.tolist());bad_palette.putpixel((int(x),int(y)),(255,0,255,255))
    for name,im in [('raw_generated_wrong_dimensions',bad_dimension),('protected_pixel_change',bad_protected),('unmapped_palette_color',bad_palette)]:
        stream=io.BytesIO();im.save(stream,format='PNG');stream.seek(0)
        try:record_from_png(stream)
        except AssertionError:rejected.append(name)
        else:raise AssertionError('Invalid input accepted:'+name)
    assert len(rejected)==3
    save_json(ROOT/'qa/reports/title_geography_20261024_mechanical.json',dict(status='PASS_EXACT512_SOURCE_PALETTE_PROTECTED_MASK_AND_THREE_NEGATIVE_IMPORTS',
        original263200record_roundtrip=True,header_palette1056bytes_equal=record[:1056]==raw[:1056],
        record_sha256=digest(record),rejected=rejected,release_eligible=False))
    print('PASS exact source indexed roundtrip/frozen PNG record;3 invalid imports rejected.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','prepare','select','mechanical']);a=p.parse_args();globals()[a.action]()

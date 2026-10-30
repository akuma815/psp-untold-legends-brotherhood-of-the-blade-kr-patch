"""Native grid map labels, complete glyph bounds, original palettes and terrain."""
import argparse,copy,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from fontTools.ttLib import TTFont
from survey import ROOT,digest,save_json
from map_korean_20261024 import original,regions,WORK as BACKGROUND
from map_texture_import_20261024 import encode_candidate

NAME='map_crisp27_20261030';CONFIG='development_'+NAME+'.json'
WORK=ROOT/'workspace/graphics/map_crisp27_20261030_v2'
PARENT='development_second_review_apply_20261030.json'
FONT=ROOT/'workspace/font/morpheus_stage003/source_galmuri_2.40.4/Galmuri11.ttf'
WAD='PSP_GAME/USRDIR/resource.wad'
read=lambda p:json.loads(p.read_text(encoding='utf8'))

def prepare():
    assert not WORK.exists()
    source,rows=original();src=np.asarray(source)
    background=Image.open(BACKGROUND/'background_candidate1024.png').convert('RGBA')
    oldmask=np.asarray(Image.open(BACKGROUND/'source_ink_mask1024.png'))!=0
    assert np.all(np.asarray(background)[~oldmask]==src[~oldmask])
    font=ImageFont.truetype(str(FONT),12);cmap=TTFont(FONT).getBestCmap()
    ink=Image.new('1',(1024,1024));notes=[]
    for r in regions():
        text=r['working_korean'];text=text.replace(' ','\n') if r['id']=='map-caption-07' else text
        assert all(ord(c) in cmap for c in text if c!='\n')
        probe=ImageDraw.Draw(Image.new('1',(256,96)));box=probe.multiline_textbbox((0,0),text,font=font,spacing=2,align='center')
        box=(math.floor(box[0]),math.floor(box[1]),math.ceil(box[2]),math.ceil(box[3]))
        # Keep the complete glyph image and ample padding. No AI silhouettes,
        # region-window clipping, antialiasing, or fractional-size resampling.
        glyph=Image.new('1',(box[2]-box[0]+8,box[3]-box[1]+8))
        draw=ImageDraw.Draw(glyph);draw.fontmode='1';draw.multiline_text((4-box[0],4-box[1]),text,font=font,fill=1,spacing=2,align='center')
        assert glyph.getbbox() and glyph.getbbox()[0]>=3 and glyph.getbbox()[1]>=3
        assert glyph.getbbox()[2]<=glyph.width-3 and glyph.getbbox()[3]<=glyph.height-3
        glyph=glyph.crop(glyph.getbbox());scale=3 if r['id']=='map-caption-01' else 2
        glyph=glyph.resize((glyph.width*scale,glyph.height*scale),Image.Resampling.NEAREST)
        x0,y0,x1,y1=r['conservative_source_rectangle'];x=(x0+x1-glyph.width)//2;y=(y0+y1-glyph.height)//2
        assert x>=x0+1 and y>=y0+1 and x+glyph.width<=x1-1 and y+glyph.height<=y1-1,(r['id'],glyph.size)
        ink.paste(glyph,(x,y))
        notes.append(dict(id=r['id'],text=text,font_size_native=12,integer_scale=scale,origin=[x,y],
            complete_ink_extent=list(glyph.size),bbox_margin_verified=True,mask_sha256=digest(glyph.tobytes())))
    ink=ink.convert('L');core=np.asarray(ink)!=0;outline=np.asarray(ink.filter(ImageFilter.MaxFilter(3)))!=0
    out=np.asarray(background).copy()
    for row in rows:
        n=row['number']-1;x=n%8*128;y=n//8*128;p=row['palette'];tile=out[y:y+128,x:x+128]
        tile[outline[y:y+128,x:x+128]]=max(p,key=lambda c:sum(c[:3]))
        tile[core[y:y+128,x:x+128]]=min(p,key=lambda c:sum(c[:3]))
    allowed=oldmask|outline
    assert np.all(out[~allowed]==src[~allowed]) and np.all(out[829:1004,781:1024]==src[829:1004,781:1024])
    records,changed=encode_candidate((1024,1024),list(Image.fromarray(out).get_flattened_data()),rows,[r['conservative_source_rectangle'] for r in regions()])
    WORK.mkdir(parents=True)
    Image.fromarray(out).save(WORK/'map_crisp1024.png');ink.save(WORK/'ink1024.png')
    Image.fromarray((allowed*255).astype(np.uint8)).save(WORK/'allowed1024.png')
    before=Image.open(ROOT/'workspace/graphics/map_generated_kr_20261024_v4/map_korean_candidate1024.png').convert('RGBA')
    sheet=Image.new('RGB',(800,11*128),'#ddd');draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(regions()):
        x0,y0,x1,y1=r['conservative_source_rectangle'];b=(x0-4,y0-4,x1+4,y1+10)
        for j,im in enumerate([before,Image.fromarray(out)]):
            crop=im.crop(b);crop=crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST);sheet.paste(crop,(j*400,i*128+10))
        draw.text((4,i*128),r['id'],fill='red')
    sheet.save(WORK/'analysis_before_after2x.png')
    save_json(WORK/'raster.json',dict(status='CRISP_NATIVE_GRID_CANDIDATE_NOT_YET_RUNTIME_VERIFIED',
        font=FONT.relative_to(ROOT).as_posix(),font_sha256=digest(FONT.read_bytes()),labels=notes,changed_tiles=changed,
        source_header_palette_original=True,outside_ink_and_source_cleanup_mask_equal=True,logo_equal=True,
        binary_ink_values=sorted(map(int,np.unique(np.asarray(ink)))),anti_aliasing=False,
        generated_lettering_or_fractional_resampling=False,complete_font_glyphs_not_window_extracted=True,
        background_reused_source_terrain_below_Unataca_not_blindly_erased=True,
        user_report='Dirty outlines, bottom clipping and unknown trace below Unataca na. Graphics26 final appearance rejected.',
        final_human_quality_approved=False,release_eligible=False))
    print('Prepared native grid candidate,complete11 labels;no AA,source palette/terrain;visual check required')

def frozen():
    source,rows=original();im=Image.open(WORK/'map_crisp1024.png').convert('RGBA')
    mask=np.asarray(Image.open(WORK/'allowed1024.png'))!=0
    assert im.size==(1024,1024) and np.all(np.asarray(im)[~mask]==np.asarray(source)[~mask])
    assert im.crop((781,829,1024,1004)).tobytes()==source.crop((781,829,1024,1004)).tobytes()
    records,changed=encode_candidate(im.size,list(im.get_flattened_data()),rows,[r['conservative_source_rectangle'] for r in regions()])
    return im,rows,records,changed

def configuration():
    return dict(schema_version=27,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        frozen_inputs={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in [WORK/'map_crisp1024.png',WORK/'ink1024.png',WORK/'allowed1024.png',WORK/'raster.json']},
        preserved_wording_approval='workspace/translation/approvals/20261030_current3571_wording.json',
        preserved_original13_scope='workspace/translation/approvals/20261030_graphics13_original_scope.json',
        human_graphics_quality_approved=False,release_eligible=False)

def select():
    frozen();assert not (ROOT/'config'/CONFIG).exists();save_json(ROOT/'config'/CONFIG,configuration());print('Crisp candidate frozen;not final appearance approval')

def derive_crisp(cfg):
    assert cfg==configuration()
    for n,s in cfg['frozen_inputs'].items():assert digest((ROOT/n).read_bytes())==s
    from second_review_apply_20261030 import derive_second_review
    plan,outputs=derive_second_review(read(ROOT/'config'/PARENT));plan=copy.deepcopy(plan);outputs=dict(outputs)
    before=outputs[WAD];wad=bytearray(before);im,rows,records,changed=frozen();ranges=[]
    # Replace the prior25 map writers with the new source-derived map writers,
    # preserving loading, font pointers/appends and all other patches exactly.
    starts={r['entry']['offset']+96 for r in rows}
    plan['writes']=[w for w in plan['writes'] if not (w['path']==WAD and w['offset'] in starts)]
    for row,record in zip(rows,records):
        off=row['entry']['offset'];assert before[off:off+96]==row['raw'][:96]
        wad[off:off+8288]=record
        if record!=row['raw']:
            plan['writes'].append(dict(owner='Complete native-grid Korean map label',path=WAD,offset=off+96,size=8192,
                expected_sha256=digest(row['raw'][96:]),final_sha256=digest(record[96:]),
                derivation='Frozen source-paletted1024PNG;exact complete Korean font glyphs,noAA;original headers/palettes and pixels outside frozen masks.'))
        ranges.append((off,off+8288))
    cursor=0
    for a,z in ranges:assert wad[cursor:a]==before[cursor:a];cursor=z
    assert wad[cursor:]==before[cursor:] and len(wad)==len(before)
    outputs[WAD]=bytes(wad);plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['map_quality_correction']=dict(source_user_defects=True,changed_map_tiles=len(changed),
        wordings3571_and_other79_files_unchanged=True,loading_original13_title_unchanged=True,native_pending=True,human_approved=False)
    return plan,outputs

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','select']);a=p.parse_args();globals()[a.action]()

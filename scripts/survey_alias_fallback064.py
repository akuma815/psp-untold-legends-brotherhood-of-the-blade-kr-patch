"""Source-derived eighteen-glyph fallback survey; no game asset writes or adoption."""
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont
from hangul_columns import codebook
from survey_galmuri14_060 import pack
from survey import ROOT, digest, save_json
from psp_folder import sha

G11_SHA='e24256f42e43713d2ea086a1e1669d78b968f5b3cc547e5c157f0606ffa5def1'
G14_SHA='6fe6c3fe4369e3837ac348431e8670733d67aa4bd550982baa72cc93c81a1c68'
FALLBACK_CODES=(0xb6b7,0xb743,0xc7d2,0xc7e1,0xc922,0xc931,0xcb63,0xcbef,
                0xcb86,0xcb87,0xcd49,0xcd4a,0xcd4b,0xcd4c,0xcd4d,0xcd4e,0xce28,0xce3a)

def raster(font,code):
    # Draw into a larger canvas first: neither the fill nor outline may be cropped.
    large=Image.new('L',(48,48));x=1-min(0,font.getbbox(chr(code))[0])
    ImageDraw.Draw(large).text((10+x,12),chr(code),font=font,fill=255)
    mask=large.crop((10,10,24,28));outside=large.copy();outside.paste(0,(10,10,24,28))
    assert outside.getbbox() is None
    levels=sorted(set(mask.tobytes()));mask=mask.point(lambda v:255 if v>=128 else 0)
    box=mask.getbbox();assert box and box[0]>=1 and box[1]>=1 and box[2]<14 and box[3]<18
    im=Image.new('L',(14,18),1)
    im.paste(15,(0,0,14,18),mask.filter(ImageFilter.MaxFilter(3)));im.paste(11,(0,0,14,18),mask)
    return im.tobytes(),list(box),levels

def build_book():
    base=ROOT/'workspace/font/morpheus_stage003/source_galmuri_2.40.4'
    assert sha(base/'Galmuri11.ttf')==G11_SHA and sha(base/'Galmuri14.ttf')==G14_SHA
    book=codebook(base/'Galmuri11.ttf')
    assert set(sum(book['aliases'],[]))==set(FALLBACK_CODES)
    # Preserve every original texture/metric ID; only eighteen mapping rows change.
    book=dict(book,textures=list(book['textures']),metrics=list(book['metrics']),mapping=dict(book['mapping']))
    index={v:i for i,v in enumerate(book['textures'])};metrics={v:i+256 for i,v in enumerate(book['metrics'])}
    fonts={False:ImageFont.truetype(str(base/'Galmuri11.ttf'),12),True:ImageFont.truetype(str(base/'Galmuri14.ttf'),12)}
    cmap=TTFont(base/'Galmuri14.ttf').getBestCmap();rasters=defaultdict(list);fallback=[];levels=set()
    for code in range(0xac00,0xd7a4):
        replaced=code in FALLBACK_CODES
        if replaced:assert cmap.get(code) not in (None,'.notdef')
        raw,box,rawlevels=raster(fonts[replaced],code);rasters[raw].append(code)
        if not replaced:continue
        levels.update(rawlevels);seq=[]
        for x in range(14):
            col=bytes(raw[y*14+x] for y in range(18))
            bottom=max((y+1 for y,v in enumerate(col) if v!=1),default=1);col=col[:bottom]
            if col not in index:index[col]=len(book['textures']);book['textures'].append(col)
            metric=(index[col],14 if x==0 else 0,0 if x==0 else x-14)
            if metric not in metrics:metrics[metric]=len(book['metrics'])+256;book['metrics'].append(metric)
            seq.append(metrics[metric])
        book['mapping'][code]=seq
        fallback.append({'codepoint':code,'bbox':box,'source_advance':fonts[True].getlength(chr(code)),
                         'raster_sha256':digest(raw),'threshold':128})
    book['aliases']=[v for v in rasters.values() if len(v)>1]
    assert len(rasters)==11172 and not book['aliases']
    assert len(book['textures'])<=4096
    book['cells'],overflow=pack(book['textures'],1);assert not overflow
    book['reverse']={tuple(seq):code for code,seq in book['mapping'].items()};assert len(book['reverse'])==11172
    for code,seq in book['mapping'].items():
        rebuilt=bytearray([1])*252
        for x,slot in enumerate(seq):
            for y,v in enumerate(book['textures'][book['metrics'][slot-256][0]]):rebuilt[y*14+x]=v
        assert rasters[bytes(rebuilt)]==[code]
    return book,rasters,fallback,sorted(levels)

def main():
    book,rasters,fallback,levels=build_book()
    base=ROOT/'workspace/font/morpheus_stage003/source_galmuri_2.40.4'
    oldfont=ImageFont.truetype(str(base/'Galmuri11.ttf'),12)
    preview=Image.new('RGB',(1120,7*184),(245,245,245));draw=ImageDraw.Draw(preview)
    groups=[[0xb6b7,0xb743],[0xc7d2,0xc7e1],[0xc922,0xc931],[0xcb63,0xcbef],
            [0xcb86,0xcb87],list(range(0xcd49,0xcd4f)),[0xce28,0xce3a]]
    for n,group in enumerate(groups):
        draw.text((8,n*184+8),f'G11 / G14 size12; group {n+1}',fill='black')
        for j,code in enumerate(group):
            x=225+j*145;y=n*184;draw.text((x,y+3),f'U+{code:04X}',fill='black')
            new=next(raw for raw,codes in rasters.items() if codes==[code])
            old=raster(oldfont,code)[0]
            for raw,yy in [(old,y+22),(new,y+100)]:
                im=Image.frombytes('L',(14,18),bytes({1:0,11:255,15:60}[v] for v in raw))
                preview.paste(im.convert('RGB').resize((56,72),Image.Resampling.NEAREST),(x,yy))
    out=ROOT/'workspace/analysis/font064';out.mkdir(parents=True,exist_ok=True)
    manifest={'policy':'development_poc_non_distributable','release_eligible':False,'runtime_adopted':False,
      'base_font_sha256':G11_SHA,'fallback_font_sha256':G14_SHA,'fallback_size':12,'cell':[14,18],
      'fallback':fallback,'columns':[v.hex() for v in book['textures']],
      'mapping':[[book['metrics'][slot-256][0] for slot in book['mapping'][code]] for code in range(0xac00,0xd7a4)]}
    save_json(out/'fallback_codebook.json',manifest)
    qa=ROOT/'qa/graphics/20261017_064_alias_fallback';qa.mkdir(parents=True,exist_ok=True);preview.save(qa/'alias_fallback_comparison.png')
    report={'status':'PASS_SCOPED_SOURCE_FONT_FALLBACK_SURVEY','release_eligible':False,'game_assets_changed':False,
      'glyphs_checked':11172,'unique_rasters':len(rasters),'unchanged_G11_rasters':11154,'G14_size12_fallback_glyphs':18,
      'visual_aliases':book['aliases'],'cell':[14,18],'outside_crop_ink_loss':False,'fallback_raw_mask_levels':levels,
      'unique_columns':len(book['textures']),'new_columns':len(book['textures'])-3247,'column_id_bits':12,
      'single_pixel_atlas_reconstructions':11172,'metric_records_per_font':11428+len(book['textures']),
      'font_payload_bytes_each':0x2180+(11172+len(book['textures']))*32+96+131072,
      'same14column12bit_renderer_compatible_static':True,'native_G14_size15_adopted':False,
      'font_style_or_runtime_approved':False,'codebook_sha256':sha(out/'fallback_codebook.json'),
      'preview_sha256':sha(qa/'alias_fallback_comparison.png'),'fallback':fallback}
    save_json(ROOT/'qa/reports/font_stage064_alias_fallback.json',report);print({k:v for k,v in report.items() if k!='fallback'})

if __name__=='__main__':main()

"""Full native15 G14 raster uniqueness and atlas/metric packing costs; no game edits."""
import json,math,struct
from collections import defaultdict,Counter
from PIL import Image,ImageDraw,ImageFilter,ImageFont
from fontTools.ttLib import TTFont
from survey import ROOT,save_json,digest
from psp_folder import sha

def pack(columns,width):
    lanes=[{'x':x,'y':258 if x<258 else 0} for x in range(0,512-width,width)]
    cells={};overflow=[]
    for tid in sorted(range(len(columns)),key=lambda n:(-len(columns[n]),n)):
        height=len(columns[tid])+2
        lane=next((p for p in lanes if p['y']+height<=511),None)
        if lane is None:overflow.append(tid);continue
        cells[tid]=(lane['x'],lane['y'],width,height);lane['y']+=height
    return cells,overflow

def main():
    path=ROOT/'workspace/font/morpheus_stage003/source_galmuri_2.40.4/Galmuri14.ttf'
    assert sha(path)=='6fe6c3fe4369e3837ac348431e8670733d67aa4bd550982baa72cc93c81a1c68'
    font=ImageFont.truetype(str(path),15);tt=TTFont(path);cmap=tt.getBestCmap()
    columns=[];index={};mapping=[];rasters=defaultdict(list);advances=set();bounds=Counter();levels=set()
    for code in range(0xac00,0xd7a4):
        char=chr(code);assert cmap.get(code) not in [None,'.notdef'];advances.add(font.getlength(char))
        large=Image.new('L',(48,48));x=1-min(0,font.getbbox(char)[0]);ImageDraw.Draw(large).text((10+x,12),char,font=font,fill=255)
        mask=large.crop((10,10,27,28));outside=large.copy();outside.paste(0,(10,10,27,28));assert outside.getbbox() is None
        levels.update(mask.tobytes());mask=mask.point(lambda v:255 if v>=128 else 0);box=mask.getbbox();bounds[tuple(box)]+=1
        assert box and box[0]>=1 and box[1]>=1 and box[2]<17 and box[3]<18
        outline=mask.filter(ImageFilter.MaxFilter(3));image=Image.new('L',(17,18),1)
        image.paste(15,(0,0,17,18),outline);image.paste(11,(0,0,17,18),mask)
        raw=image.tobytes();rasters[raw].append(code);row=[];rebuilt=bytearray([1])*(17*18)
        for xx in range(17):
            col=bytes(raw[y*17+xx] for y in range(18));bottom=max((y+1 for y,v in enumerate(col) if v!=1),default=1);col=col[:bottom]
            if col not in index:index[col]=len(columns);columns.append(col)
            tid=index[col];row.append(tid)
            for y,v in enumerate(col):rebuilt[y*17+xx]=v
        assert rebuilt==raw;mapping.append(row)
    assert len(mapping)==11172 and len(rasters)==11172 and len(columns)==6626 and advances=={15.0}
    cells3,overflow3=pack(columns,3);cells1,overflow1=pack(columns,1)
    assert overflow3 and not overflow1
    # Verify both byte addressing and every reconstructed glyph in a hypothetical
    # one-pixel atlas. Constant-U sampling is a design candidate, not runtime proof.
    pixels=bytearray([1])*(512*512)
    for tid,col in enumerate(columns):
        x,y,w,h=cells1[tid]
        for dy,v in enumerate(col):pixels[(y+1+dy)*512+x]=v
        # Preserve the current vertical transparent gutter/filter profile.
    for ordinal,row in enumerate(mapping):
        raw=bytearray([1])*306
        for xx,tid in enumerate(row):
            x,y,w,h=cells1[tid]
            for dy in range(len(columns[tid])):raw[dy*17+xx]=pixels[(y+1+dy)*512+x]
        assert rasters[bytes(raw)]==[0xac00+ordinal]
    bits=(len(columns)-1).bit_length();assert bits==13
    packed=[sum(tid<<(bits*n) for n,tid in enumerate(row)).to_bytes(28,'little') for row in mapping]
    assert all(int.from_bytes(raw,'little')>>(17*13)==0 for raw in packed)
    out=ROOT/'workspace/analysis/font060';out.mkdir(parents=True,exist_ok=True)
    # Six extra bytes per glyph can complete22 bytes already available in metric.
    extra=b''.join(raw[22:] for raw in packed);assert len(extra)==67032
    (out/'glyph_tail6.bin').write_bytes(extra)
    records=256+11172+len(columns);payload=((0x17c+records*32+15)//16)*16+96+131072
    manifest={'font_sha256':sha(path),'native_size':15,'cell':[17,18],'tid_bits':13,'columns':[col.hex() for col in columns],
      'mapping':mapping,'cells_single_pixel':cells1,'glyph_tail6_sha256':digest(extra),'runtime_adopted':False}
    save_json(out/'g14_static_codebook.json',manifest)
    previous=json.loads((ROOT/'qa/reports/font_alias_stage033.json').read_text(encoding='utf-8'))['groups']
    preview=Image.new('RGB',(1160,7*190),(245,245,245));draw=ImageDraw.Draw(preview)
    oldpath=path.with_name('Galmuri11.ttf');oldfont=ImageFont.truetype(str(oldpath),12)
    for n,group in enumerate(previous):
        draw.text((8,n*190+8),f'Alias group {n+1}: G11 upper / G14 lower',fill='black')
        for j,member in enumerate(group['members']):
            code=member['codepoint'];x=220+j*150;y=n*190
            draw.text((x,y+3),f'U+{code:04X}',fill='black')
            for f,sz,yy in [(oldfont,(14,18),y+18),(font,(17,18),y+100)]:
                m=Image.new('L',sz);ImageDraw.Draw(m).text((1,2),chr(code),font=f,fill=255)
                rgb=Image.merge('RGB',(m,m,m));preview.paste(rgb.resize((sz[0]*4,72),Image.Resampling.NEAREST),(x,yy))
    qa=ROOT/'qa/graphics/20261017_060_g14_survey';qa.mkdir(parents=True,exist_ok=True);preview.save(qa/'alias_native_comparison.png')
    report={'status':'PASS_FULL_G14_STATIC_COST_SURVEY','release_eligible':False,'font_sha256':sha(path),'source_native_advance':15,
      'native_size':15,'required_cell_with_outline':[17,18],'glyphs_checked':11172,'unique_full_rasters':len(rasters),'visual_aliases':0,
      'outside_crop_ink_loss':False,'raw_mask_levels':sorted(levels),'unique_columns':len(columns),'column_id_bits':bits,
      'three_pixel_lanes_packed':len(cells3),'three_pixel_lanes_overflow':len(overflow3),'single_pixel_lanes_packed':len(cells1),'single_pixel_lanes_overflow':len(overflow1),
      'single_pixel_atlas_all_glyph_grid_reconstructions':11172,'virtual_metric_inline_bytes':22,'packed17_by13_bytes':28,'extra_table_bytes':len(extra),
      'extra_table_sha256':digest(extra),'metric_records_per_font':records,'font_payload_bytes_each':payload,'font_payload_delta_vs048_each':payload-601152,
      'quads_per_Hangul':17,'GE_vertices_per_Hangul_per_layer':34,
      'design_conditions':['Constant-U sampling for1-pixel atlas columns requires new live raster checks','13bit17-column unpacking and6byte auxiliary table require source-bound Allegrex hook/relocations','Advance17 and source font line heights require all observed UI/wrap QA','No font final adoption or approval'],
      'game_assets_or_primary048_changed':False,'runtime_font_changed':False,'codebook_sha256':sha(out/'g14_static_codebook.json'),'preview_sha256':sha(qa/'alias_native_comparison.png')}
    save_json(ROOT/'qa/reports/font_stage060_g14_cost.json',report);print(report)

if __name__=='__main__':main()

"""Scoped Morpheus font codec and a non-distribution one-glyph RAM trial asset."""
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont
from survey import ROOT, digest, save_json

WORK=ROOT/'workspace/font/morpheus_stage003'
WAD_OFFSET=0x022a5800
SIZE=0xa1e0

def decode(data):
    assert len(data)==32768
    pixels=bytearray(65536)
    for y in range(256):
        for x in range(256):
            byte_x=x//2
            address=(y//8)*1024+(byte_x//16)*128+(y%8)*16+byte_x%16
            pixels[y*256+x]=(data[address]>>(4*(x%2)))&15
    return pixels

def encode(pixels):
    # Independent block-ordered writer: 16-byte x 8-row blocks, low nibble first.
    assert len(pixels)==65536 and max(pixels)<16
    out=bytearray()
    for block_y in range(32):
        for block_x in range(8):
            for line in range(8):
                row=(block_y*8+line)*256+block_x*32
                for pair in range(16):
                    out.append(pixels[row+pair*2]|pixels[row+pair*2+1]<<4)
    return bytes(out)

def rgba(pixels,palette):
    im=Image.new('RGBA',(256,256))
    im.putdata([tuple(palette[v*4:v*4+4]) for v in pixels])
    return im

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    data=(ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').read_bytes()[WAD_OFFSET:WAD_OFFSET+SIZE]
    catalog=json.loads((ROOT/'qa/reports/asset_analysis.json').read_text(encoding='utf-8'))
    registered=next(f for f in catalog['wad']['fonts'] if f['trailing_label_candidate']=='Fonts\\fon_Morpheus')
    assert digest(data)==registered['sha256']
    palette=data[0x21a0:0x21e0]
    pixels=decode(data[0x21e0:])
    assert encode(pixels)==data[0x21e0:]
    glyphs=[]
    used=bytearray(65536)
    for code in range(256):
        rec=struct.unpack_from('<Iiii4f',data,0x17c+code*32)
        assert rec[0]==code
        bounds=[round(v*256) for v in rec[4:]]
        x0,y0,x1,y1=bounds
        assert 0<=x0<=x1<=256 and 0<=y0<=y1<=256
        for y in range(y0,y1):
            for x in range(x0,x1):used[y*256+x]=1
        glyphs.append({'code':code,'unknown_u32':rec[1],'advance':rec[2],
                       'bearing':rec[3],'uv':list(rec[4:]),'bounds':bounds})
    width,height=18,22
    candidates=[(x,y) for y in range(256-height+1) for x in range(256-width+1)
                if all(not any(used[yy*256+x:yy*256+x+width]) for yy in range(y,y+height))]
    assert candidates,'No nonoverlapping trial cell'
    x0,y0=candidates[-1]
    font_path=WORK/'source_galmuri_2.40.4/Galmuri11.ttf'
    assert digest(font_path.read_bytes())=='e24256f42e43713d2ea086a1e1669d78b968f5b3cc547e5c157f0606ffa5def1'
    tt=TTFont(font_path)
    cmap=tt.getBestCmap()
    assert cmap[0xd55c] not in (cmap.get(0x3f),'.notdef')
    font=ImageFont.truetype(str(font_path),16)
    mask=Image.new('L',(width,height))
    ImageDraw.Draw(mask).text((1,2),'한',font=font,fill=255,stroke_width=0)
    mask=mask.point(lambda value:255 if value>=128 else 0)
    assert mask.getbbox() and mask.getbbox()[0]>=1 and mask.getbbox()[2]<width
    expanded=mask.filter(ImageFilter.MaxFilter(3))
    colors=[tuple(palette[i*4:i*4+4]) for i in range(16)]
    transparent=min(range(16),key=lambda i:colors[i][3])
    fill=max(range(16),key=lambda i:sum(colors[i][:3])*colors[i][3])
    dark=[i for i in range(16) if max(colors[i][:3])<80]
    outline=max(dark,key=lambda i:colors[i][3])
    modified=bytearray(pixels)
    for y in range(height):
        for x in range(width):
            v=fill if mask.getpixel((x,y)) else outline if expanded.getpixel((x,y)) else transparent
            modified[(y0+y)*256+x0+x]=v
    assert all(a==b or (x0<=i%256<x0+width and y0<=i//256<y0+height)
               for i,(a,b) in enumerate(zip(pixels,modified)))
    packed=encode(modified)
    assert decode(packed)==modified
    new_record=struct.pack('<Iiii4f',0xd55c,0,width,0,x0/256,y0/256,(x0+width)/256,(y0+height)/256)
    (WORK/'trial_texture.bin').write_bytes(packed)
    (WORK/'trial_record.bin').write_bytes(new_record)
    atlas=rgba(pixels,palette)
    bg=Image.new('RGBA',(256,256),(45,55,65,255));bg.alpha_composite(atlas)
    bg.resize((768,768),Image.Resampling.NEAREST).save(WORK/'original_atlas_verified.png')
    trial=rgba(modified,palette).crop((x0,y0,x0+width,y0+height))
    preview=Image.new('RGBA',(width,height),(65,70,80,255));preview.alpha_composite(trial)
    preview.resize((width*12,height*12),Image.Resampling.NEAREST).save(WORK/'trial_han.png')
    report={'schema_version':1,'scope':'font codec and one-glyph RAM diagnostic; not a distribution mapping',
        'source_wad_offset':WAD_OFFSET,'source_payload_size':SIZE,'source_payload_sha256':digest(data),
        'format':{'width':256,'height':256,'palette_offset':0x21a0,'palette_entries':16,
                  'palette_encoding':'RGBA8','texture_offset':0x21e0,'texture_size':32768,
                  'bit_depth':4,'nibble_order':'low first','swizzle_block_bytes':[16,8],
                  'record_start':0x17c,'record_stride':32,'record_count':256,
                  'record_format_candidate':'u32 code, u32 unknown, i32 advance, i32 bearing, f32 u0,v0,u1,v1'},
        'roundtrip_texture_exact':True,'glyphs':glyphs,'protected_source_records':256,
        'trial':{'unicode':0xd55c,'glyph_source':font_path.relative_to(ROOT).as_posix(),
                 'glyph_source_sha256':digest(font_path.read_bytes()),'pixel_font_size':16,
                 'cell':[x0,y0,width,height],'overlaps_any_source_uv':False,
                 'rgba_palette':colors,'transparent_index':transparent,'fill_index':fill,'outline_index':outline,
                 'texture_sha256':digest(packed),'record_hex':new_record.hex(),
                 'ram_slot':'borrowed loader-initialized sentinel at font+0x15c; restored after test',
                 'temporary_selector_rule':'all >=256 map to borrowed sentinel; only U+D55C is eligible in this diagnostic',
                 'not_proved':['Unicode lookup expansion','glyph capacity','storage loader path','normal-input E2E','final font adoption']}}
    save_json(ROOT/'qa/reports/morpheus_format_stage003.json',report)
    print(json.dumps({'roundtrip_exact':True,'cell':[x0,y0,width,height],
                      'palette_indices':[transparent,fill,outline],'font_sha256':digest(font_path.read_bytes())}))

if __name__=='__main__':main()

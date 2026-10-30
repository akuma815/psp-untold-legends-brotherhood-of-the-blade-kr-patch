"""Unadopted native12 full-Hangul column diagnostic, not translation SSOT.

Logical palette: transparent1, fill11, outline15. Each font maps these to its
own unchanged palette. Code sequences are reversible even for source raster
aliases. Fourteen draw calls per syllable require separate runtime QA.
"""
import struct
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont

DIAGNOSTIC = '한글을 봅니다. 가각괜뷁힣 A9! '

def codebook(font_path):
    font = ImageFont.truetype(str(font_path), 12)
    cmap = TTFont(font_path).getBestCmap()
    textures, texture_ids, metrics, metric_ids, mapping = [], {}, [], {}, {}
    rasters = defaultdict(list)
    reverse = {}
    for code in range(0xac00, 0xd7a4):
        assert cmap.get(code) not in (None, '.notdef')
        mask = Image.new('L', (14, 18))
        ImageDraw.Draw(mask).text((1-min(0,font.getbbox(chr(code))[0]),2), chr(code), font=font, fill=255)
        mask = mask.point(lambda v: 255 if v >= 128 else 0)
        box = mask.getbbox()
        assert box and box[0]>=1 and box[1]>=1 and box[2]<14 and box[3]<18
        outline = mask.filter(ImageFilter.MaxFilter(3))
        image = Image.new('L',(14,18),1)
        image.paste(15,(0,0,14,18),outline); image.paste(11,(0,0,14,18),mask)
        raw = image.tobytes(); rasters[raw].append(code)
        seq = []
        reconstructed = bytearray([1]) * 252
        for x in range(14):
            col = bytes(raw[y*14+x] for y in range(18))
            bottom = max((y+1 for y,v in enumerate(col) if v!=1),default=1)
            col = col[:bottom]
            if col not in texture_ids:
                texture_ids[col] = len(textures); textures.append(col)
            tid = texture_ids[col]
            metric = (tid,14 if x==0 else 0,0 if x==0 else x-14)
            if metric not in metric_ids:
                metric_ids[metric] = len(metrics)+256; metrics.append(metric)
            seq.append(metric_ids[metric])
            for y,v in enumerate(col):reconstructed[y*14+x]=v
        assert reconstructed==raw
        # Distinct code sequences preserve semantic round trips for source visual aliases.
        if tuple(seq) in reverse:
            metrics.append(metrics[seq[-1]-256]); seq[-1]=len(metrics)+255
        assert tuple(seq) not in reverse
        reverse[tuple(seq)]=code; mapping[code]=seq
    assert len(textures)==3247 and len(metrics)==7377 and 256+len(metrics)==7633
    assert sum(len(v)-1 for v in rasters.values())==11
    for code,seq in mapping.items():assert reverse[tuple(seq)]==code
    # Variable-height, 3px-wide lanes avoid the complete original image and wrap ring.
    lanes=[{'x':x,'y':258 if x<258 else 0} for x in range(0,510,3)]
    cells={}
    for tid in sorted(range(len(textures)),key=lambda i:(-len(textures[i]),i)):
        h=len(textures[tid])+2
        lane=next((lane for lane in lanes if lane['y']+h<=511),None)
        if lane is None:raise ValueError('Column texture packing overflow')
        cells[tid]=(lane['x'],lane['y'],3,h);lane['y']+=h
    aliases=[v for v in rasters.values() if len(v)>1]
    return {'textures':textures,'metrics':metrics,'mapping':mapping,'reverse':reverse,'cells':cells,
            'aliases':aliases,'exact_raster_roundtrips':11172}

def encode(text, book):
    out=[]
    for c in text:
        code=ord(c)
        if code<=255:out.append(c)
        elif code in book['mapping']:out.extend(chr(v) for v in book['mapping'][code])
        else:raise ValueError(f'Unmapped diagnostic character U+{code:04X}')
    return ''.join(out)

def decode(text,book):
    out=[];i=0
    while i<len(text):
        code=ord(text[i])
        if code<=255:out.append(text[i]);i+=1
        else:
            seq=tuple(ord(v) for v in text[i:i+14])
            if seq not in book['reverse']:raise ValueError('Invalid column sequence')
            out.append(chr(book['reverse'][seq]));i+=14
    return ''.join(out)

def palette_indices(source):
    palette=list(struct.iter_unpack('<4B',source[0x21a0:0x21e0]))
    transparent=min(range(16),key=lambda i:palette[i][3])
    assert palette[transparent][3]==0
    fill=max(range(16),key=lambda i:sum(palette[i][:3])*palette[i][3])
    dark=[i for i,p in enumerate(palette) if max(p[:3])<80]
    outline=max(dark,key=lambda i:palette[i][3])
    assert len({transparent,fill,outline})==3
    return {1:transparent,11:fill,15:outline}

def atlas(source,src_pixels,book):
    indices=palette_indices(source)
    pixels=bytearray([indices[1]])*(512*512)
    for y in range(256):
        pixels[y*512:y*512+256]=src_pixels[y*256:(y+1)*256]
        pixels[y*512+256]=src_pixels[y*256]
        pixels[y*512+511]=src_pixels[y*256+255]
    for x in range(256):
        pixels[256*512+x]=src_pixels[x]
        pixels[511*512+x]=src_pixels[255*256+x]
    for x,oldx in [(256,0),(511,255)]:
        for y,oldy in [(256,0),(511,255)]:pixels[y*512+x]=src_pixels[oldy*256+oldx]
    used=bytearray(512*512)
    for tid,col in enumerate(book['textures']):
        x,y,w,h=book['cells'][tid]
        assert x>=258 or y>=258
        for yy in range(h):
            for xx in range(w):
                pos=(y+yy)*512+x+xx
                assert not used[pos];used[pos]=1
                pixels[pos]=indices[col[yy-1]] if 1<=yy<h-1 else indices[1]
        assert bytes(pixels[(y+1+yy)*512+x+1] for yy in range(len(col)))==bytes(indices[v] for v in col)
    for y in range(256):assert pixels[y*512:y*512+256]==src_pixels[y*256:(y+1)*256]
    new_metrics=bytearray()
    for i,(tid,advance,bearing) in enumerate(book['metrics']):
        x,y,w,h=book['cells'][tid];height=len(book['textures'][tid])
        new_metrics.extend(struct.pack('<Iiii4f',256+i,0,advance,bearing,
                                       (x+1)/512,(y+1)/512,(x+2)/512,(y+1+height)/512))
    return pixels,new_metrics,indices

def rebuild_locale(directory,trans,book,encoder=encode,decoder=decode,diagnostic_text=None,replace_body=False):
    newdir,newtrans=bytearray(),bytearray();found=0;changes=[]
    for pos in range(0,len(directory),20):
        key,eo,to,el,tl,flags,reserved=struct.unpack_from('<IIIHHHH',directory,pos)
        raw=trans[to:to+tl];assert len(raw)==tl
        if key==3881:
            assert raw.count(b'The streets of Aven')==1
            diagnostic=DIAGNOSTIC if diagnostic_text is None else diagnostic_text
            encoded=encoder(diagnostic,book)
            assert decoder(encoded,book)==diagnostic
            if replace_body:
                header,body=raw.split(b'\r\n\r\n',1)
                assert header==b'[bg_SL_intro1]Prologue' and body.startswith(b'The streets of Aven')
                final=header+b'\r\n\r\n'+encoded.encode('utf-8')
            else:final=raw.replace(b'The streets of Aven',encoded.encode('utf-8'))
            # Formatted route has both a5000-byte UTF8 stage and2048-unit UTF16 stage.
            from text_limits import check_template
            check_template(final.decode('utf-8'),'Prologue3881')
            # Route3881 observed original decoder receives capacity2048, reserves NUL.
            if len(final.decode('utf-8').encode('utf-16le'))//2>2047:
                raise ValueError('Prologue3881 exceeds observed2047-unit decoder output limit')
            found+=1;changes.append({'key':key,'old_offset':to,'old_bytes':tl,'new_bytes':len(final),
                                    'diagnostic_text':diagnostic,'diagnostic_encoded_hex':encoded.encode('utf-8').hex()})
        else:final=raw
        assert len(final)<=65535
        newdir.extend(struct.pack('<IIIHHHH',key,eo,len(newtrans),el,len(final),flags,reserved))
        newtrans.extend(final)
    assert found==1
    # Independent parsing of every output entry, including later shifted strings.
    for pos in range(0,len(directory),20):
        a=struct.unpack_from('<IIIHHHH',directory,pos);b=struct.unpack_from('<IIIHHHH',newdir,pos)
        assert a[0:2]==b[0:2] and a[3]==b[3] and a[5:]==b[5:]
        if a[0]!=3881:assert trans[a[2]:a[2]+a[4]]==newtrans[b[2]:b[2]+b[4]]
    return bytes(newdir),bytes(newtrans),changes

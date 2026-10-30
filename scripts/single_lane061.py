"""Isolated G11 sampling PoC: same glyphs/metrics/encoding,1-pixel atlas lanes."""
import struct
from hangul_columns import atlas
from single_unit_renderer import virtual_metrics,TEXTURE_FIRST
from survey_galmuri14_060 import pack

def repack(book):
    cells,overflow=pack(book['textures'],1);assert not overflow
    return dict(book,cells=cells)

def atlas_single_lane(source,src_pixels,book,metric_builder=virtual_metrics):
    pixels,_,indices=atlas(source,src_pixels,{'textures':[],'metrics':[],'cells':{}})
    used=bytearray(512*512);metrics=metric_builder(book)
    for tid,col in enumerate(book['textures']):
        x,y,w,h=book['cells'][tid];assert w==1 and h==len(col)+2 and (x>=258 or y>=258)
        for dy in range(h):
            pos=(y+dy)*512+x;assert not used[pos];used[pos]=1
            pixels[pos]=indices[col[dy-1]] if 1<=dy<h-1 else indices[1]
        assert bytes(pixels[(y+1+dy)*512+x] for dy in range(len(col)))==bytes(indices[v] for v in col)
        u=(x+.5)/512
        metrics.extend(struct.pack('<Iiii4f',TEXTURE_FIRST+tid,0,0,0,u,(y+1)/512,u,(y+1+len(col))/512))
    return pixels,metrics,indices

"""Explicit eighteen-glyph font PoC, using unchanged061 renderer/character ABI."""
import struct
from single_unit_renderer import PACK_OFFSETS
from single_lane061 import atlas_single_lane
from survey import digest

VIRTUAL_SHA='f31d5aceb49239a1a7a0d53bacce85ca0e8421ae70822d9f88f5d24badd76826'

def virtual_fallback(book):
    records=bytearray()
    for ordinal,(code,seq) in enumerate(book['mapping'].items()):
        assert code==0xac00+ordinal and len(seq)==14
        tids=[book['metrics'][slot-256][0] for slot in seq]
        assert all(0<=tid<3285 for tid in tids)
        packed=sum(tid<<(12*x) for x,tid in enumerate(tids)).to_bytes(22,'little')
        record=bytearray(32);struct.pack_into('<H',record,0,256+ordinal);struct.pack_into('<ii',record,8,14,0)
        for offset,value in zip(PACK_OFFSETS,packed):record[offset]=value
        records.extend(record)
    assert digest(records)==VIRTUAL_SHA
    return records

def atlas_fallback(source,src_pixels,book):
    return atlas_single_lane(source,src_pixels,book,metric_builder=virtual_fallback)

"""Closed subset: original item field72 to705DC,2048wide scratch and document widget."""
import struct,re,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

KEYS={2251,3663,3664,3666,3667,3668,3669,3670,3671,3672,3673,3674,3675,3676,3677}
POLICY='item_document_field72_single_portrait_plain_CRLF_2048_v1'
@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2' and digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    off,n=struct.unpack_from('<II',db,40);fields={};rows=[]
    for row in range(n):
        raw=db[off+row*84:off+(row+1)*84];key=struct.unpack_from('<I',raw,72)[0]
        if key in KEYS:
            assert raw[59]==13 and key not in fields;fields[key]=[(5,row,72)];rows.append(dict(table=5,row=row,stride=84,offset=off+row*84,complete_row_hex=raw.hex()))
    assert set(fields)==KEYS
    from allegrex_profile import Profile
    out=ROOT/'workspace/analysis/document_body_20261020';windows=[]
    for name,a,z in [('selected_item_body_gate',0x25160,0x251d8),('document_body_widget',0x26038,0x26160),('synchronous_body_decoder',0x705dc,0x70678)]:
        raw=boot[a+128:z+128];decoded=Profile().verify_roundtrip(raw,a,out,name);(out/(name+'.listing.txt')).write_text(''.join(f'{r["pc"]:08X} {r["assembly"]}\n' for r in decoded),encoding='utf8')
        windows.append(dict(name=name,start=a,end=z,sha256=digest(raw),roundtrip_instructions=len(decoded)))
    return dict(fields=fields,complete_rows=rows,consumer_windows=windows,
        path='25170 installs selected item+118;25194..251B4 gates row+48>=0;251CC same selected item to item title274D0.2607C/26084/2608C row+48->705DC;70644/70648 DA634 cap2048;26094 BDCB0 owned wide copy;260F8 BE088->26104 C3024 document text;26130 C52DC open.',
        interpretation='Static full consumer chain. Same single-portrait plain grammar and2048wide scratch; natural item acquisition, glyph/layout/paging/reopen QA remains pending.')
FIELDS=context()['fields']
@lru_cache(maxsize=1)
def sources():
    src={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in KEYS:
        s=src[k];b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    return {k:src[k] for k in KEYS}
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    s=sources()[r['key']];text=r['text'];assert r['source_text']==s['source_text'] and text and text==unicodedata.normalize('NFC',text)
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);assert len(tags)==1 and re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tags[0]) and text.startswith(tags[0]) and s['source_text'].startswith(tags[0])
    body=text[len(tags[0]):];assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text']) and '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text and len(encoded)+1<=5000
    check_template(text,'705DC original2048-unit source document decoder, no explicit paging adoption')
    return encoded

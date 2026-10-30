"""All 113 original table16 Map names; source, numbering and plain-text grammar."""
import re, struct, unicodedata
from functools import lru_cache
from survey import ROOT, digest
from catalog_survey034 import lines
from unicode_codec042 import encode_unicode, decode_unicode
from text_limits import check_template

@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,128);assert (off,n)==(350184,113)
    src=lines(ROOT/'workspace/translation/baseline/source_entries.jsonl')
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_static.dat').read_bytes()
    result={}
    for row in range(n):
        key=struct.unpack_from('<H',db,off+row*2)[0]
        found=[s for s in src if s['bank']=='static' and s['key']==key];assert len(found)==1 and key not in result
        s=found[0];value=raw[s['offset']:s['offset']+s['byte_length']]
        assert value.hex()==s['source_hex'] and digest(value)==s['source_sha256'] and value==s['source_text'].encode('utf8')
        assert not any(c in s['source_text'] for c in '\0\r\n\t[]{}$')
        result[key]=dict(source=s,row=row,offset=off+row*2,expected_hex=db[off+row*2:off+row*2+2].hex())
    assert set(result)==set(range(34,147))
    return result

def validate(r,book,encoder=encode_unicode,decoder=decode_unicode):
    assert set(r)=={'key','source_text','text'} and type(r['key']) is int
    s=population()[r['key']]['source'];assert r['source_text']==s['source_text']
    text=r['text'];assert isinstance(text,str) and text.strip() and text==unicodedata.normalize('NFC',text)
    assert not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\d+',text)==re.findall(r'\d+',s['source_text'])
    encoded=encoder(text,book).encode('utf8');assert len(encoded)<=65535
    assert decoder(encoded.decode('utf8'),book)==text
    check_template(text,'table16 Map plain name; geometry requires representative runtime evidence')
    return encoded

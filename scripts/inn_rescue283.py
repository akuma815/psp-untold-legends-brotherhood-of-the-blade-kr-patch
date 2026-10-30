"""Exact source-backed class1 ordinal3 reactions; no story progression claim."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
FIELDS={2293:(0,0x5d469b1b,[37],'PI_WillBartenderConcerned'),
        2295:(2,0x44f6b898,[37],'PI_NathanTondrel'),
        2297:(9,0xe2f77b6e,[37],'PI_LaylaGoodmorrowConcerned')}
POLICY='inn_rescue_table13_ordinal3_portrait_v1'

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,104);row,h,words,portrait=FIELDS[r['key']]
    w=struct.unpack_from('<65I',db,off+row*260)
    assert (off,n)==(336020,18) and w[0]==h and [i for i,x in enumerate(w) if x==r['key']]==words
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    assert r['source_text']==s['source_text']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert raw.hex()==s['source_hex'] and raw==r['source_text'].encode('utf8') and digest(raw)==s['source_sha256']
    tag='[i_'+portrait+']';text=r['text']
    assert r['source_text'].startswith(tag) and text.startswith(tag) and text==unicodedata.normalize('NFC',text)
    body=text[len(tag):]
    assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',r['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8')
    assert decoder(encoded.decode('utf8'),book)==text and len(encoded)<=65535
    check_template(text,'Inn rescue source word37;2047 decoder bound;native layout separately verified')
    return encoded

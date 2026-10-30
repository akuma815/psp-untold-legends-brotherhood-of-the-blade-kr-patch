"""Twelve exact known consumers;unresolved and bad source portrait remain excluded."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
DIALOGUE_KEYS=[2311,2316,2288,2305,2310,2319,2321,2323,2324,2308]
BOOK_KEYS=[2313,2314,2315]
FIELDS={2288:[(15,46,32)],2305:[(13,14,148)],2308:[(13,2,32)],2310:[(13,9,32)],2311:[(14,43,0)],
        2313:[(15,71,40),(15,79,40),(15,80,40)],2314:[(15,79,24)],2315:[(15,80,24)],
        2316:[(15,80,32)],2319:[(13,2,152)],2321:[(13,9,152)],2323:[(13,12,156)],2324:[(13,11,156)]}
POLICY='pending_twelve_known_consumers303_v1'
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    for table,row,field in FIELDS[r['key']]:
        off,n=struct.unpack_from('<II',db,table*8);stride={13:260,14:44,15:56}[table]
        assert row<n and struct.unpack_from('<I',db,off+row*stride+field)[0]==r['key']
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw==s['source_text'].encode('utf8') and digest(raw)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text)
    if r['key'] in DIALOGUE_KEYS:
        tags=re.findall(r'\[i_[^\]\r\n]+\]',s['source_text']);assert len(tags)==1
        tag=tags[0]
        if r['key']==2308:
            assert tag=='[i_PR_NathanTondrelConcened]'
            tag='[i_PI_NathanTondrelConcerned]'
        assert text.startswith(tag)
        body=text[len(tag):]
    else:
        body=text;assert not any(c in text for c in '\r\n')
    assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text and len(encoded)<=65535
    check_template(text,'Known303 consumers;exact portraits/paragraphs;2047 common formatter bound;per-screen layout separately verified')
    return encoded

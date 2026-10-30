"""Seven exact row0 plain-portrait units; no late-story or unknown-control acceptance."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

FIELDS={2326:1,2327:2,2340:3,2341:4,2275:7,2282:36,2306:39}
POLICY='will_table13_row0_early_portrait_v1'
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,count=struct.unpack_from('<II',db,104);row=struct.unpack_from('<65I',db,off);assert count==18 and row[0]==0x5d469b1b and row[FIELDS[r['key']]]==r['key']
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    assert r['source_text']==s['source_text'];raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert raw==r['source_text'].encode('utf8') and digest(raw)==s['source_sha256']
    tag='[i_PI_WillBartender'+('Concerned' if r['key'] in [2282,2306] else '')+']'
    text=r['text'];assert r['source_text'].startswith(tag) and text.startswith(tag) and text==unicodedata.normalize('NFC',text)
    body=text[len(tag):];assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',r['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text
    check_template(text,'Will row0 early subset;necessary common-wrapper guard;layout separately verified')
    if r['key']==2326:assert '울부짖는 소나무 여관' in text and '하울링 파인' not in text
    return encoded

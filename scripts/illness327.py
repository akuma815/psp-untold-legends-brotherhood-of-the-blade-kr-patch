"""Sixteen exact NPC generic slots;no BUG or late conditional block expansion."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from context_illness325 import FIELDS
from text_limits import check_template
POLICY='illness_followups325_exact9_v1'
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    row,word=FIELDS[r['key']];assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==r['key']
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    tags=re.findall(r'\[i_[^\]]+\]',s['source_text']);text=r['text'];assert len(tags)==1 and text.startswith(tags[0]) and 'BUG' not in s['source_text'].upper()
    assert text==unicodedata.normalize('NFC',text);body=text[len(tags[0]):]
    assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    enc=encoder(text,book).encode('utf8');assert decoder(enc.decode('utf8'),book)==text and len(enc)<=65535
    check_template(text,'Illness followups;source325 exact9 controls;shared2047 formatter bound;native layouts separately required')
    return enc

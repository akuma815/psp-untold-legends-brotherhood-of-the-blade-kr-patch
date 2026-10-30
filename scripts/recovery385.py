"""Exact source383 controls, including one preserved Maia[p], never broad literals."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from context_recovery383 import FIELDS
from text_limits import check_template
POLICY='recovery383_exact17_dialogue_v1'

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    row,word=FIELDS[r['key']];assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==r['key']
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);text=r['text']
    assert len(re.findall(r'\[i_[^\]]+\]',s['source_text']))==1 and text.startswith(tags[0]) and 'BUG' not in s['source_text'].upper()
    assert tags==re.findall(r'\[[^\]]+\]',text)
    assert tags[1:]==(['[p]'] if r['key']==3060 else [])
    assert text==unicodedata.normalize('NFC',text);body=text[len(tags[0]):].replace('[p]','')
    assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    if r['key']==3060:assert text.count('\r\n[p]\r\n')==1
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    enc=encoder(text,book).encode('utf8');assert decoder(enc.decode('utf8'),book)==text and len(enc)<=65535
    check_template(text,'Recovery383 exact17 controls;shared2047 formatter bound;[p] preserved without forced-page claim;native layouts required')
    return enc

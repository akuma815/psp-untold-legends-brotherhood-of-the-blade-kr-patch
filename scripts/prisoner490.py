"""Exact8 prisoner quest fields;portrait dialogue and Book title/body only."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from context_prisoner488 import FIELDS,DIALOGUE_KEYS,BOOK_KEYS,TITLES
from text_limits import check_template
POLICY='prisoner488_exact8_quest_text_v1'

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    for table,row,field in FIELDS[r['key']]:
        off,count=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table]
        assert row<count and struct.unpack_from('<I',db,off+row*stride+field)[0]==r['key']
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    assert not re.search(r'\*BUG(?: THIS| ME)?\*',s['source_text'].upper())
    text=r['text'];tags=re.findall(r'\[[^\]]+\]',s['source_text']);assert tags==re.findall(r'\[[^\]]+\]',text)
    images=re.findall(r'\[i_[^\]]+\]',s['source_text']);assert len(images)==(1 if r['key'] in DIALOGUE_KEYS else 0)
    if images:assert text.startswith(images[0])
    count=5 if r['key']==2528 else 0
    assert tags[len(images):]==['[p]']*count and text.count('\r\n[p]\r\n')==count
    assert text==unicodedata.normalize('NFC',text)
    body=text[len(images[0]) if images else 0:].replace('[p]','');assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    if r['key'] in BOOK_KEYS:assert not tags and not any(c in text for c in '\r\n')
    enc=encoder(text,book).encode('utf8');assert decoder(enc.decode('utf8'),book)==text and len(enc)<=65535
    check_template(text,'Prisoner488 exact8 typed fields;2047 formatter bound;Book/dialogue native QA distinct;no added page control')
    return enc

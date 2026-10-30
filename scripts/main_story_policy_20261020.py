"""Exact late-quest population; unsupported multi-image consumers withheld from builds."""
import re,struct,unicodedata
from functools import lru_cache
from collections import defaultdict
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from main_story_drafts_20261020 import HELD_KEYS

QUEST_ROWS=[25,26,27,28,29,30,31,37]
SUB_ROWS={25:[43,44,45,51,52],26:[53,54,55,56,57,58],27:[72,59,60,62],28:[63,64],29:[65,66],30:[67,82,83,85,84],31:[87,88,89,90,92,93],37:[94,95]}
POLICY='main_story_20261020_single_portrait_plain_CRLF_v1'

@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    a,na=struct.unpack_from('<II',db,112);b,nb=struct.unpack_from('<II',db,120);fields=defaultdict(list);rows=[];thoughts=[]
    for q in QUEST_ROWS:
        raw=db[a+q*44:a+(q+1)*44];assert q<na and [j for j in struct.unpack_from('<6h',raw,18) if j>=0]==SUB_ROWS[q]
        rows.append(dict(table=14,row=q,stride=44,hex=raw.hex()));k=struct.unpack_from('<I',raw)[0]
        if k!=0xffffffff:fields[k].append((14,q,0))
        k=struct.unpack_from('<I',raw,4)[0]
        if k!=0xffffffff:fields[k].append((14,q,4))
        k=struct.unpack_from('<I',raw,8)[0]
        if k!=0xffffffff:thoughts.append(dict(table=14,row=q,field=8,mode=3,key=k))
        for j in SUB_ROWS[q]:
            r=db[b+j*56:b+(j+1)*56];assert j<nb and len(r)==56;assert struct.unpack_from('<I',r,28)[0]==0xffffffff
            rows.append(dict(table=15,row=j,stride=56,hex=r.hex()))
            for f in [24,32,36,40]:
                k=struct.unpack_from('<I',r,f)[0]
                if k!=0xffffffff:fields[k].append((15,j,f))
    assert len(fields)==71 and set(HELD_KEYS)<set(fields)
    return dict(fields=dict(fields),rows=rows,separate_mode3=thoughts)

ALL_FIELDS=context()['fields']
FIELDS={k:v for k,v in ALL_FIELDS.items() if k not in HELD_KEYS}

@lru_cache(maxsize=1)
def sources():
    s={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'}
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in ALL_FIELDS:
        r=s[k];data=raw[r['offset']:r['offset']+r['byte_length']]
        assert data.hex()==r['source_hex'] and digest(data)==r['source_sha256'] and data==r['source_text'].encode('utf8')
    return {k:s[k] for k in ALL_FIELDS}

def validate_draft(key,text,book,encoder,decoder):
    assert key in ALL_FIELDS
    s=sources()[key];assert isinstance(text,str) and text==unicodedata.normalize('NFC',text)
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);assert tags==re.findall(r'\[[^\]]+\]',text)
    assert all(re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tag) for tag in tags)
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    body=re.sub(r'\[i_[A-Za-z0-9_]+\]','',text);assert body.strip() and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    enc=encoder(text,book).encode('utf8');assert len(enc)<=65535 and decoder(enc.decode('utf8'),book)==text
    check_template(text,'Late main-quest source control preflight; multi-image held entries are not runtime eligible')
    return enc

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    s=sources()[r['key']];assert r['source_text']==s['source_text']
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);dialogue=any((t==14 and f==0) or (t==15 and f==32) for t,row,f in FIELDS[r['key']])
    assert len(tags)==int(dialogue)
    if tags:assert s['source_text'].startswith(tags[0]) and r['text'].startswith(tags[0])
    return validate_draft(r['key'],r['text'],book,encoder,decoder)

"""Seventeen complete side-quest record scopes, exact 107 source identities."""
import re,struct,unicodedata
from functools import lru_cache
from collections import defaultdict
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

QUEST_ROWS=[38,39,0,1,2,3,4,5,6,7,8,9,10,11,12,14,13]
SUB_ROWS={0:[100,101,102,103],1:[104,105],2:[106,107],3:[108,109],4:[110,111],5:[114,115],6:[112,113],
          7:[116,117],8:[118,119],9:[120,121],10:[122,123],11:[124,125],12:[126,127],13:[128,129,130,131,132,133],14:[69,70],38:[96,97],39:[98,99]}
POLICY='sidequests_20261020_source_single_portrait_plain_CRLF_v1'

@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    a,na=struct.unpack_from('<II',db,112);b,nb=struct.unpack_from('<II',db,120);fields=defaultdict(list);rows=[]
    for q in QUEST_ROWS:
        r=db[a+q*44:a+(q+1)*44];assert q<na and len(r)==44 and [i for i in struct.unpack_from('<6h',r,18) if i>=0]==SUB_ROWS[q]
        rows.append(dict(table=14,row=q,stride=44,offset=a+q*44,hex=r.hex()))
        assert struct.unpack_from('<II',r,4)==(0xffffffff,0xffffffff)
        fields[struct.unpack_from('<I',r)[0]].append((14,q,0))
        for j in SUB_ROWS[q]:
            raw=db[b+j*56:b+(j+1)*56];assert j<nb and len(raw)==56 and struct.unpack_from('<I',raw,28)[0]==0xffffffff
            rows.append(dict(table=15,row=j,stride=56,offset=b+j*56,hex=raw.hex()))
            for f in [24,32,36,40]:
                k=struct.unpack_from('<I',raw,f)[0]
                if k!=0xffffffff:fields[k].append((15,j,f))
    assert len(fields)==107 and 0xffffffff not in fields
    return dict(fields=dict(fields),complete_rows=rows,quest_rows=QUEST_ROWS,logical_order_is_not_physical_reorder=True)

FIELDS=context()['fields']

@lru_cache(maxsize=1)
def sources():
    s={r['key']:r for r in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if r['bank']=='trans'}
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in FIELDS:
        r=s[k];data=raw[r['offset']:r['offset']+r['byte_length']]
        assert data.hex()==r['source_hex'] and digest(data)==r['source_sha256'] and data==r['source_text'].encode('utf8')
    return {k:s[k] for k in FIELDS}

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    s=sources()[r['key']];assert r['source_text']==s['source_text']
    text=r['text'];assert isinstance(text,str) and text.strip() and text==unicodedata.normalize('NFC',text)
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);assert tags==re.findall(r'\[[^\]]+\]',text)
    dialogue=any((t==14 and f==0) or (t==15 and f==32) for t,row,f in FIELDS[r['key']]);assert len(tags)==int(dialogue)
    if tags:assert re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tags[0]) and s['source_text'].startswith(tags[0]) and text.startswith(tags[0])
    body=text[len(tags[0]) if tags else 0:];assert body.strip() and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    enc=encoder(text,book).encode('utf8');assert len(enc)<=65535 and decoder(enc.decode('utf8'),book)==text
    check_template(text,'Side-quest plain/portrait/CRLF 2047 formatter bound; runtime layout separate')
    return enc

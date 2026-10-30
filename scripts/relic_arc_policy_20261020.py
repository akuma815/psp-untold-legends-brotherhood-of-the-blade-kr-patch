"""Four complete quest units, modes1/4/6/7/8; mode3 thoughts remain separate."""
import re, struct, unicodedata
from functools import lru_cache
from collections import defaultdict
from survey import ROOT, digest
from catalog_survey034 import lines
from text_limits import check_template

POLICY='relic_arc_20261020_typed_plain_portrait_CRLF_v1'
QUEST_ROWS=[21,22,23,24]
SUB_ROWS={21:[22,16,17],22:[18,19,20,21],23:[39,40,50],24:[41,42]}

@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    a,na=struct.unpack_from('<II',db,112);b,nb=struct.unpack_from('<II',db,120)
    fields=defaultdict(list);separate=[];rows=[]
    for q in QUEST_ROWS:
        raw=db[a+q*44:a+(q+1)*44];assert len(raw)==44 and q<na
        assert [x for x in struct.unpack_from('<6h',raw,18) if x>=0]==SUB_ROWS[q]
        rows.append(dict(table=14,row=q,stride=44,hex=raw.hex()))
        k=struct.unpack_from('<I',raw)[0];fields[k].append((14,q,0))
        assert struct.unpack_from('<I',raw,4)[0]==0xffffffff
        thought=struct.unpack_from('<I',raw,8)[0];separate.append(dict(key=thought,table=14,row=q,field=8,mode=3))
        for j in SUB_ROWS[q]:
            r=db[b+j*56:b+(j+1)*56];assert len(r)==56 and j<nb
            rows.append(dict(table=15,row=j,stride=56,hex=r.hex()))
            assert struct.unpack_from('<I',r,28)[0]==0xffffffff
            for f in [24,32,36,40]:
                k=struct.unpack_from('<I',r,f)[0]
                if k!=0xffffffff:fields[k].append((15,j,f))
    assert len(fields)==30 and {r['key'] for r in separate}=={3581,3582,3583,3584}
    return dict(fields=dict(fields),rows=rows,separate=separate)

FIELDS=context()['fields']

@lru_cache(maxsize=1)
def sources():
    src={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'}
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in FIELDS:
        s=src[k];data=raw[s['offset']:s['offset']+s['byte_length']]
        assert data.hex()==s['source_hex'] and digest(data)==s['source_sha256'] and data==s['source_text'].encode('utf8')
    return {k:src[k] for k in FIELDS}

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    s=sources()[r['key']];assert r['source_text']==s['source_text']
    tags=re.findall(r'\[[^\]]+\]',s['source_text'])
    assert tags==re.findall(r'\[[^\]]+\]',r['text']) and all(re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',t) for t in tags)
    dialogue=any(t==14 or f==32 for t,row,f in FIELDS[r['key']]);assert len(tags)==int(dialogue)
    text=r['text'];assert isinstance(text,str) and text==unicodedata.normalize('NFC',text)
    if tags:assert text.startswith(tags[0])
    body=text[len(tags[0]) if tags else 0:];assert body.strip() and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    enc=encoder(text,book).encode('utf8');assert len(enc)<=65535 and decoder(enc.decode('utf8'),book)==text
    check_template(text,'Relic arc modes1/4/6/7/8,2047 formatter bound; original CRLF and portraits retained')
    return enc

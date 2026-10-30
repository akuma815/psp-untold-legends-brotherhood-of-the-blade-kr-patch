"""Exact table13 late-NPC subset and supplementary table14/15 quest fields."""
import re,struct,unicodedata
from functools import lru_cache
from collections import defaultdict
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

NPC_KEYS={2568,2569,2571,2572,2573,2574,2575,2577,2578,2579,2581,2582,2583,2586,2589,2590,2591,2592,2593,2594,2595,2614,2615,2616,
          2649,2650,2651,2652,2653,2654,2655,2656,2657,2658,2745,2746,2747,*range(3536,3562),3913,3993}
QUEST_REFS={2346:[(15,23,32)],2669:[(15,61,40),(15,68,40)],2723:[(15,86,36)],2727:[(15,86,24)],3008:[(15,24,32)],3029:[(15,77,40)],
            3030:[(15,77,24)],3032:[(14,42,0)],3066:[(15,76,40)],3067:[(15,78,40)],3068:[(15,78,24)],3069:[(15,91,40)],
            3070:[(15,91,24)],3071:[(15,91,32)],3097:[(15,49,32)],3607:[(15,28,32)],3629:[(15,71,24)],3630:[(15,71,32)],
            3752:[(15,61,24)],3753:[(15,68,24)],3754:[(15,68,32)]}
HELD_KEYS={3544,3548}
POLICY='late_dialogue_20261020_typed_single_portrait_plain_CRLF_v1'

@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,104);assert (off,n)==(336020,18)
    fields=defaultdict(list);rows=[]
    for row in range(n):
        data=db[off+row*260:off+(row+1)*260];words=struct.unpack('<65I',data)
        rows.append(dict(table=13,row=row,stride=260,offset=off+row*260,owner_hash=words[0],hex=data.hex()))
        for word,k in enumerate(words[1:],1):
            if k in NPC_KEYS:fields[k].append((13,row,word*4))
    assert set(fields)==NPC_KEYS and len(NPC_KEYS)==65
    for k,refs in QUEST_REFS.items():
        for table,row,f in refs:
            at,count=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];assert row<count and struct.unpack_from('<I',db,at+row*stride+f)[0]==k
            data=db[at+row*stride:at+(row+1)*stride];rows.append(dict(table=table,row=row,stride=stride,offset=at+row*stride,hex=data.hex()))
        assert k not in fields;fields[k]=refs
    assert len(fields)==86
    assert fields[3548]==[(13,4,132),(13,7,132)]
    return dict(fields=dict(fields),complete_rows=rows,NPC_subset_logical=65,quest_subset_logical=21,held_keys=sorted(HELD_KEYS),
                consumer_basis=['scripts/map_alice148.py','scripts/audit_cache163.py','scripts/context_generic314.py'],
                interpretation='Original table13 selector cells are references, not proof of individual natural triggering or complete phase-order reconstruction.')

ALL_FIELDS=context()['fields']
FIELDS={k:refs for k,refs in ALL_FIELDS.items() if k not in HELD_KEYS}

@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'}
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in ALL_FIELDS:
        s=ss[k];data=raw[s['offset']:s['offset']+s['byte_length']];assert data.hex()==s['source_hex'] and digest(data)==s['source_sha256'] and data==s['source_text'].encode('utf8')
    return {k:ss[k] for k in ALL_FIELDS}

def validate_draft(k,text,book,encoder,decoder):
    s=sources()[k];assert isinstance(text,str) and text.strip() and text==unicodedata.normalize('NFC',text)
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);assert tags==re.findall(r'\[[^\]]+\]',text)
    dialogue=any(t==13 or (t==14 and f==0) or (t==15 and f==32) for t,row,f in ALL_FIELDS[k]);assert len(tags)==int(dialogue)
    if tags:assert re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tags[0]) and s['source_text'].startswith(tags[0]) and text.startswith(tags[0])
    body=text[len(tags[0]) if tags else 0:];assert body.strip() and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text']) and '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    assert re.findall(r'\d+',text)==re.findall(r'\d+',s['source_text'])
    encoded=encoder(text,book).encode('utf8');assert len(encoded)<=65535 and decoder(encoded.decode('utf8'),book)==text
    check_template(text,'Existing single-portrait/plain formatter2047 scope; runtime geometry remains separate')
    return encoded

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    assert r['source_text']==sources()[r['key']]['source_text']
    return validate_draft(r['key'],r['text'],book,encoder,decoder)

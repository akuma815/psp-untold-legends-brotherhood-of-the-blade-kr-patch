"""Finite T12 scalar-numeric cohort; T7 effect text remains manuscript only."""
import re,struct,unicodedata,json
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from ability_corpus_drafts_20261020 import NUMERIC,EFFECTS

POLICY='table12_scalar_numeric_2048_staging16_development_v1'

@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'}
    numeric={k:s for k,s in ss.items() if re.search(r'\$[1-6]',s['source_text'])};assert set(numeric)==set(NUMERIC)|{3081} and len(numeric)==57
    # The already observed native Block definition is exactly original table12 row71.
    off,n=struct.unpack_from('<II',db,96);assert (off,n)==(308604,298)
    sample=json.loads((ROOT/'qa/runtime/20261017_052_emucap_numeric_stage/inputs.json').read_text(encoding='utf8'))['reads'][0]
    assert bytes.fromhex(sample['hex'])[:92]==db[off+71*92:off+72*92]
    fields=defaultdict(list);rows=[];allnumericrefs=0
    for row in range(n):
        data=db[off+row*92:off+(row+1)*92];k=struct.unpack_from('<I',data,64)[0]
        if k not in numeric:continue
        allnumericrefs+=1;slots=[list(data[68+i*3:71+i*3]) for i in range(7)];active=next((i for i,v in enumerate(slots) if v[0]==0),7)
        assert all(v[2] in range(5) for v in slots[:active]) and all(int(v[1])<=active for v in re.findall(r'\$[1-6]',numeric[k]['source_text']))
        rows.append(dict(table=12,row=row,stride=92,key=k,offset=off+row*92,complete_row_hex=data.hex(),active_slots=active,slot_metadata=slots))
        if k in NUMERIC:fields[k].append((12,row,64))
    assert allnumericrefs==228 and set(fields)==set(NUMERIC) and len(fields)==56
    off,n=struct.unpack_from('<II',db,56);assert (off,n)==(211644,164)
    for row in range(n):
        data=db[off+row*64:off+(row+1)*64];k=struct.unpack_from('<I',data,44)[0]
        if k in EFFECTS:
            fields[k].append((7,row,44));rows.append(dict(table=7,row=row,stride=64,key=k,offset=off+row*64,complete_row_hex=data.hex(),consumer_established=False))
    assert set(fields)==set(NUMERIC)|set(EFFECTS) and all(len(fields[k])==1 for k in EFFECTS)
    # Exact source call-site connects definition+0x40 to the same numeric formatter.
    anchors={0x1aafc:0x8e460000,0x1ab04:0x8cc50040,0x1ab08:0x0c01c3a1,0x70eb0:0x24d40044,0x71104:0x2a440007,0x71120:0x34060800}
    for pc,w in anchors.items():assert struct.unpack_from('<I',boot,pc+128)[0]==w,(hex(pc),hex(struct.unpack_from('<I',boot,pc+128)[0]),hex(w))
    return dict(fields=dict(fields),complete_rows=rows,numeric_unique_source_records=57,numeric_reference_cells=228,new_numeric_keys=56,effect_manuscripts=17,
        consumer_basis=['scripts/analyze_numeric051.py','scripts/audit_numeric_stage052.py','scripts/numeric_limits053.py'],source_instruction_anchors={hex(k):hex(v) for k,v in anchors.items()},
        interpretation='Numeric cohort is same original row definition/field64, seven scalar16-unit slots and2048-unit formatter; per-ability/rank gameplay and numeric semantic QA remain pending. Table7 effect consumer not established.')

ALL_FIELDS=context()['fields']
FIELDS={k:refs for k,refs in ALL_FIELDS.items() if k in NUMERIC}

@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in ALL_FIELDS:
        s=ss[k];b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256'] and b==s['source_text'].encode('utf8')
    return {k:ss[k] for k in ALL_FIELDS}

def bound(text):
    tokens=re.findall(r'\$[1-6]',text);literal=re.sub(r'\$[1-6]','',text)
    units=len(literal.encode('utf-16le'))//2+len(tokens)*15+1;size=len(literal.encode('utf8'))+len(tokens)*45+1
    assert units<=2048 and size<=5000
    return dict(max_UTF16_units_including_NUL=units,max_UTF8_bytes_including_NUL=size,numeric_occurrences=len(tokens),slot_staged_units=15,storage_bound_not_numeric_accuracy=True)

def validate_draft(k,text,book,encoder,decoder):
    s=sources()[k];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}#%&*+:<=>\\^~')
    before=re.findall(r'\$[1-6]',s['source_text']);after=re.findall(r'\$[1-6]',text);assert before==after and text.count('$')==len(after)
    a=re.sub(r'\$[1-6]','',s['source_text']);b=re.sub(r'\$[1-6]','',text);assert re.findall(r'\d+',a)==re.findall(r'\d+',b)
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text and len(encoded)<=65535
    check_template(text,'Finite source-bound scalar numeric cohort; runtime geometry is separate')
    if k in FIELDS:bound(text)
    return encoded

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY and r['source_text']==sources()[r['key']]['source_text']
    return validate_draft(r['key'],r['text'],book,encoder,decoder)

def negative_cases(drafts):
    k=2901;r=dict(key=k,source_text=sources()[k]['source_text'],text=drafts[k],control_policy=POLICY)
    return r,[('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3722)),('variable_index',dict(text=r['text'].replace('$1','$2'))),
        ('variable_omission',dict(text=r['text'].replace('$1',''))),('invented_variable',dict(text=r['text']+'$a')),('new_page_control',dict(text=r['text']+'[p]')),
        ('NUL',dict(text=r['text']+'\0')),('overflow',dict(text=r['text']+'가'*2048))]

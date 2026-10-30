"""Original category13 field72 documents; plain or one portrait, no new bracket grammar."""
import re,struct,unicodedata
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from item_description_drafts_20261020 import DRAFTS
import document_body_policy_20261020 as closed

POLICY='category13_field72_plain_or_single_portrait_CRLF_2048_v1'
@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,40);fields=defaultdict(list);rows=[];allkeys=set();cells=0
    for row in range(n):
        raw=db[off+row*84:off+(row+1)*84];k=struct.unpack_from('<I',raw,72)[0]
        if raw[59]!=13 or k==0xffffffff:continue
        allkeys.add(k);cells+=1
        if k in DRAFTS:fields[k].append((5,row,72));rows.append(dict(table=5,row=row,stride=84,offset=off+row*84,complete_row_hex=raw.hex()))
    assert set(fields)==set(DRAFTS) and len(fields)==29 and len(allkeys)==52 and cells==57
    return dict(fields=dict(fields),complete_rows=rows,consumer=closed.context(),category13_body_unique=52,category13_body_reference_cells=57,
        notes=['Aegis row2031/description3638 signet mismatch retained; no source DB fix.',
               '3641 shared by five fragments and3646 by two weapon components; no automatic identity merge.',
               '2718 source first masters plural retained;2719 Den of the Wolf not silently equated with differently named map locations.',
               '3639 legendary healing and revival are recollection and belief, not guaranteed gameplay effect.',
               '2813 literal English bracket note retained; full Korean visible-document completion not claimed, manuscript only.',
               'Natural acquire/read, portrait, geometry and page/reopen checks remain runtime pending.'])
ALL_FIELDS=context()['fields'];FIELDS={k:v for k,v in ALL_FIELDS.items() if k!=2813}
@lru_cache(maxsize=1)
def sources():
    src={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in ALL_FIELDS:
        s=src[k];b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256'] and b==s['source_text'].encode('utf8')
    return {k:src[k] for k in ALL_FIELDS}
def validate_draft(k,text,book,encoder,decoder):
    s=sources()[k];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\t{}$#%&*+:<=>\\^~')
    tags=re.findall(r'\[[^\]]+\]',s['source_text']);assert tags==re.findall(r'\[[^\]]+\]',text)
    if k!=2813:
        assert len(tags)<=1
        if tags:assert re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tags[0]) and text.startswith(tags[0]) and s['source_text'].startswith(tags[0])
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',s['source_text']) and '\r' not in text.replace('\r\n','') and '\n' not in text.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text and len(encoded)+1<=5000
    check_template(text,'Source705DC2048-unit document decoder; geometry/runtime separate')
    return encoded
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY and r['source_text']==sources()[r['key']]['source_text']
    return validate_draft(r['key'],r['text'],book,encoder,decoder)

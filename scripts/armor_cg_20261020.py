"""ColdIron throughGoldthread equipment sets; exact original item consumers."""
import argparse,re,struct,unicodedata,copy
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from armor_cg_drafts_20261020 import DRAFTS
from text_limits import check_template

SPEC=dict(name='armor_cg_20261020',config='development_armor_cg_20261020.json',prior_name='armor_ac_20261020',prior_config='development_armor_ac_20261020.json',
    prior_config_sha256='d866985bd3d37327e417a22eacda199414348295c465053df4148988a469f4ca',prior_artifact_sha256='1560bc1ccebced965420164b5ecfc0dea0c96b3a3b9b4bfcdb35d7864fe6bd5c',
    prior_decisions=1654,expected_states=dict(untranslated=2439,needs_human_review=1430,in_progress=104),write_scope='Exact202 static armor base names, original table5u16field0; no item/effect DB mutation or prefix/suffix policy changes')

@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,40);assert (off,n)==(35748,2088);ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'}
    cohort={struct.unpack_from('<H',db,off+row*84)[0] for row in range(182,384)};assert cohort==set(DRAFTS) and len(cohort)==202
    refs=defaultdict(list)
    for row in range(n):
        raw=db[off+row*84:off+(row+1)*84];k=struct.unpack_from('<H',raw)[0]
        if k in cohort:
            assert raw[59] in [4,5,6,7,8,9]
            refs[k].append(dict(table=5,row=row,field=0,width=2,stride=84,offset=off+row*84,complete_row_hex=raw.hex(),category=raw[59],effect_id=struct.unpack_from('<I',raw,32)[0]))
    assert set(refs)==cohort and sum(map(len,refs.values()))==202
    return {k:dict(source=ss[k],references=v) for k,v in refs.items()}
@lru_cache(maxsize=1)
def context():
    from armor_ac_20261020 import context as prior
    c=copy.deepcopy(prior());c['cohort']='Complete ColdIron throughGoldthread families,table5rows182..383; full original rows/classes and same actual owned title consumer. No shared source name/ID merged.'
    c['semantic_notes']+=['ColdIron,Crystalline,CrystalChain are distinct source labels; no invented elemental resistance or combat behavior from their names.',
        'CompositeMail differs fromAggregateChain in previous cohort; Korean family names remain distinct.',
        'Ethereal follows existing 에테르 proposal;Elysian follows 엘리시안 location proposal. No new approved glossary entry.',
        'Glamorthread,Cured,Eldritch andfabric/plate labels are provisional equipment-title readings. Cured is not a healing-item effect claim.']
    return c
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    b=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\d+',text)==re.findall(r'\d+',s['source_text']);enc=encoder(text,book).encode('utf8');assert len(enc)+1<=250 and decoder(enc.decode('utf8'),book)==text
    check_template(text,'Same original base item-name ownedUTF8slot250; composed-title geometry pending');return enc
def negative_cases():
    k=1608;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=1614)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'\u2603')),('owned_slot_overflow',dict(text='가'*84))]
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

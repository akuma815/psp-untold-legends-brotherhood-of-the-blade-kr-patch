"""Complete armor families Acorn through Cobalt; actual item-name u16 consumer."""
import argparse,re,struct,unicodedata
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from armor_ac_drafts_20261020 import DRAFTS
from text_limits import check_template

SPEC=dict(name='armor_ac_20261020',config='development_armor_ac_20261020.json',prior_name='ability_titles_20261020',prior_config='development_ability_titles_20261020.json',
    prior_config_sha256='2de3c83c6f4ccdf179ff3bab76583b67754506d014ecf4c237d1bfb6d40e35f7',prior_artifact_sha256='951d6d7475f051280c521bb0e66c8a87a42fd71e40e27b0dcf623deb300d1f0e',
    prior_decisions=1476,expected_states=dict(untranslated=2641,needs_human_review=1228,in_progress=104),write_scope='Exact178 static armor base names, original table5u16field0; no item/effect DB mutation or prefix/suffix policy changes')

@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,40);assert (off,n)==(35748,2088);ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'}
    cohort={struct.unpack_from('<H',db,off+row*84)[0] for row in range(4,182)};assert cohort==set(DRAFTS) and len(cohort)==178
    refs=defaultdict(list)
    for row in range(n):
        raw=db[off+row*84:off+(row+1)*84];k=struct.unpack_from('<H',raw)[0]
        if k in cohort:
            assert raw[59] in [4,5,6,7,8,9]
            refs[k].append(dict(table=5,row=row,field=0,width=2,stride=84,offset=off+row*84,complete_row_hex=raw.hex(),category=raw[59],effect_id=struct.unpack_from('<I',raw,32)[0]))
    assert set(refs)==cohort and sum(map(len,refs.values()))==178
    return {k:dict(source=ss[k],references=v) for k,v in refs.items()}

@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    q=ROOT/'qa/static/20261020_armor_ac';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    for name,a,z in [('base_and_effect_name_slots',0x6ff94,0x70180),('selected_owned_title',0x2754c,0x27578)]:
        raw=boot[a+128:z+128];dec=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(dec)))
    return dict(source_roundtrip_windows=windows,consumer='6FF94 item-instance0 definition lhu0->DA6342048wide->DA478owned base slot$i250UTF8 inclNUL;27564->BDCB0owned full title. Effect name slots and original2098/2099/2108/3080 compose unchanged.',
        inherited_evidence=['scripts/names432.py','scripts/repair_names474.py','qa/reports/repair_names_stage483_runtime.json'],
        cohort='Complete related armor families Acorn throughCobalt andinterleaved shields,table5rows4..181; full source rows/classes checked, no story inferred from storage adjacency.',
        exclusions='Rows0..3 AAA names are test-like labels, separately untranslated; not declared unused or deleted. Different same-family pieces/physical records remain distinct.',
        semantic_notes=['Adamant Stitch is translated as firm stitching, not equated with Adamantine material.',
            'Armor categories ground head/body/arm/leg/foot/shield readings; Heater/Targe/Scutum remain shield naming proposals, not appliance or combat-effect claims.',
            'Bestial families have different original pieces and keys; do not merge based on shared adjective.',
            'Set/material names and clothing types are provisional; no automatic family-name conversion applied to source strings.',
            'Existing English affix fragments retained. Korean base-name byte bound does not prove natural prefix/suffix grammar, geometry, acquisition/equip or rarity behavior.'])

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    b=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\d+',text)==re.findall(r'\d+',s['source_text'])
    enc=encoder(text,book).encode('utf8');assert len(enc)+1<=250 and decoder(enc.decode('utf8'),book)==text
    check_template(text,'Original base item-name ownedUTF8 slot250; composed-title geometry pending')
    return enc
def negative_cases():
    k=1277;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=3685)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'\u2603')),('owned_slot_overflow',dict(text='가'*84))]
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

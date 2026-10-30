"""21 original stat labels/help texts: constructor slots -> selected owned help."""
import argparse,sys,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
DRAFTS={2109:'직업',2110:'생명력',2111:'캐릭터의 생명력을 나타냅니다. 생명력이 바닥나면 캐릭터가 죽습니다!',2112:'기력',2113:'캐릭터의 기력을 나타냅니다. 주문을 시전하려면 기력이 필요합니다.',2114:'방어력',2115:'현재 장착한 방어구의 방어 수치입니다. 방어구는 전투 중 일반 피해를 줄여 줍니다.',2116:'근접 피해',2117:'현재 장착한 근접 무기로 가하는 피해량입니다.',2118:'원거리 피해',2119:'현재 장착한 원거리 무기로 가하는 피해량입니다.',
2128:'화염 저항',2129:'캐릭터의 화염 피해 저항력입니다.',2130:'냉기 저항',2131:'캐릭터의 냉기 피해 저항력입니다.',2132:'독 저항',2133:'캐릭터의 독 피해 저항력입니다.',2134:'번개 저항',2135:'캐릭터의 번개 피해 저항력입니다.',2136:'마법 저항',2137:'캐릭터의 마법 피해 저항력입니다.'}
@lru_cache(maxsize=1)
def population():
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};refs={}
    for pc in range(0x57fcc,0x580bc,8):
        w,store=struct.unpack_from('<II',boot,pc+128)
        if w==0x2405ffff:assert pc==0x58044 and store==0xa60501b2;continue
        assert w>>16==0x3405 and store>>16==0xa605
        key=w&65535;field=store&65535;assert key not in refs
        if field%28==0x1b0%28:role='stat_label';index=(field-0x1b0)//28
        else:assert field%28==0x1b2%28;role='stat_help';index=(field-0x1b2)//28
        assert 0<=index<15
        refs[key]=dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=pc+128,width=4,instruction=hex(pc),expected_instruction_hex=boot[pc+128:pc+136].hex(),instance_field=hex(field),slot_index=index,role=role)
    assert set(refs)==set(range(2109,2138)) and set(DRAFTS)==set(refs)-set(range(2120,2128))
    return {k:dict(source=ss[k],references=[refs[k]]) for k in DRAFTS}
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();q=ROOT/'qa/static/20261021_stat_help';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    for name,a,z in [('literal_table29keys',0x57fcc,0x580bc),('fifteen_slot_geometry',0x580bc,0x5813c),('selection_from_fifteen_slots',0x57118,0x571ec),('selected_label_and_help',0x56b44,0x56ce4),('shared_decoder',0x705dc,0x70678)]:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    calls={0x571d0:0x56b44,0x56bc8:0x705dc,0x56bd4:0xbdcb0,0x56bfc:0xbdd74,0x56c30:0x705dc,0x56c3c:0xbdcb0}
    for pc,target in calls.items():assert struct.unpack_from('<I',boot,pc+128)[0]==0x0c000000|(target>>2),(hex(pc),hex(target))
    return dict(source_roundtrip_windows=windows,source_call_targets={hex(k):hex(v) for k,v in calls.items()},
        consumer_chain=['57FCC stores29 sourcekeys into15 28-byte slots atinstance1A0, labels+10/help+12. Classhelp is-1; existingfour attribute labels/eight manuscripts unchanged.',
        '57118 tests15 slot rectangles, stores selectedindex+100,571D0 calls56B44. 56B44 computesindex*28, reads signedhalfword1B0/1B2, calls705DC2048wide.',
        'Label copied byBDCB0 toownedUI5F0, twoLFs andhelp appended/copied throughowned5F8; classindex0 followsseparate classvalue branch. No classdescription invented.',
        'No numeric stats orDB/equipment computations edited. Existing705DCdecoder andownedstring behavior retained; callback reachability andpixel geometry remain runtimeQA.'],
        semantic_notes=['21 complete proposals, elevenlabels/tenhelp sentences. Health생명력/Power기력 andsourcearmor-rating meaning explicitlyretained.',
        'Healthzero condition conveyedas생명력이 바닥나면; no added recovery/deathpenalty. Powerrequiredfor spellcasting, normaldamage mitigation andselectedweapon distinction retained.',
        'Five elementaldamage resistances stayseparate. No percent, immunity, flatdamage rule, cappedvalue or hidden stat inferred.',
        'Previousfourstat labels anddescriptions fromcharactercreation remainunchanged; no term approval or allUIcoverage claim.'],
        class_help_omitted_source_minus1=True,all15_slot_source_keys=list(range(2109,2138)))
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert t.count('!')==s['source_text'].count('!');b=encoder(t,book).encode('utf8');assert len(b)+1<=5000 and decoder(b.decode('utf8'),book)==t
    check_template(t,'Source selectedstat label/help705DC2048wide, ownedcopies; geometry pending');return b
def negative_cases():
    k=2111;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=2120)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text='가'*2048+'!')),('lost_exclamation',dict(text=r['text'].replace('!','')))]
SPEC=dict(name='stat_help_20261021',date='20261021',config='development_stat_help_20261021.json',prior_name='actor_named_20261021',prior_config='development_actor_named_20261021.json',
          prior_config_sha256='b4ee84c0942050e35a3eada4b25df6f0c578c6230a06d19ff0ab88649b8b22c5',prior_artifact_sha256='0d13cf1ebab0d370d8e11b27e9af93a61edf27ff292d226664103e258576de55',
          prior_decisions=3749,expected_states=dict(untranslated=525,needs_human_review=3344,in_progress=104),write_scope='Exact21 stat labels/help keys, original15-slot sourceconsumer; no numericmechanic orclassdescription changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

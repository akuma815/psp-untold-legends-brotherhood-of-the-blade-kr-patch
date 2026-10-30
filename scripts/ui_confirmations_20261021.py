"""Three confirmation messages and one inventory bracket literal, individually authored."""
import argparse,sys,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
DRAFTS={3632:'아직 능력치 포인트를 모두 배분하지 않았습니다.\r\n그래도 나가시겠습니까?',3633:'능력치 포인트를 전혀 배분하지 않고 나가시겠습니까?',3748:'[ 장착 중 ]',4000:'불러온 데이터에 이상이 있는 것 같습니다.'}
LITERAL_KEY=3748
CALLS={3632:[(0x5eeb4,0x5eeb0,0x5e1a8)],3633:[(0x5ef1c,0x5ef18,0x5e1a8)],3748:[(0x27658,0x27654,0x705dc)],4000:[(0x55344,0x55340,0x55568),(0x55390,0x5538c,0x55568)]}
@lru_cache(maxsize=1)
def population():
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};pop={}
    for key,rows in CALLS.items():
        refs=[]
        for at,pc,target in rows:
            assert struct.unpack_from('<I',boot,at+128)[0]==0x34050000|key and struct.unpack_from('<I',boot,pc+128)[0]==0x0c000000|(target>>2)
            refs.append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=at+128,width=4,key=key,instruction=hex(at),call=hex(pc),target=hex(target),role='owned_confirmation_or_literal_label',expected_hex=boot[at+128:at+132].hex()))
        pop[key]=dict(source=ss[key],references=refs)
    assert re.findall(r'\r+\n|\r|\n',pop[3632]['source']['source_text'])==['\r\n']
    assert pop[LITERAL_KEY]['source']['source_text']=='[ Equipped ]'
    return pop
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    from analyze_dispatch040 import classify_byte,START,END
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();q=ROOT/'qa/static/20261021_ui_confirmations';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    spans=[('attribute_confirmation',0x5e1a8,0x5e264),('attribute_exit_conditions',0x5ee8c,0x5ef30),('loaded_data_confirmation',0x55568,0x5560c),('loaded_data_callers',0x55320,0x553bc),('inventory_equipped_literal',0x27624,0x27674),('source_classifier',START,END),('formatted_decoder',0x705dc,0x70678),('wide_formatter',0xda634,0xda740)]
    for label,a,z in spans:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,label);windows.append(dict(name=label,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    words=list(struct.unpack('<40I',boot[START+128:END+128]));assert all(classify_byte(c,words)[0]==0 for c in [91,93])
    anchors={0x5e1c8:0x00a08025,0x5e238:0x0c01c177,0x5e23c:0x02002825,0x55588:0x00a08825,0x55594:0x02209825,0x555f8:0x0c01c177,0x555fc:0x02602825,0x27660:0x0c02f773,0x2766c:0x0c02f75d}
    for at,w in anchors.items():assert struct.unpack_from('<I',boot,at+128)[0]==w,(hex(at),hex(w))
    return dict(source_roundtrip_windows=windows,anchors={hex(k):hex(v) for k,v in anchors.items()},
        consumer_chain=['3632/3633 retain exact original remaining-stat-point decision conditions.5E1A8 saves a1 in s0,5E238 passes s0 to705DC, ownedUI5E0copy andC2EC4 dialog setter. Translation does not confirm/cancel/exit anything.',
        '4000 original load-data warning caller passesa1 through55568s1/s3 to555F8->705DC thenownedUI5E0. Actual damaged saves are not created or loaded.',
        '3748 direct705DC result appended withBDDCC to existing inventory wide text, thenBDD74 joins tooltip text. Brackets are not formatter byte dispatch. Only the fixed interior literal is translated; delimiter count, spaces and no-dollar control structure preserved.'],
        protected_literal_pair=dict(key=3748,source='[ Equipped ]',draft='[ 장착 중 ]',not_general_bracket_permission=True),
        preserved_line_breaks=dict(key=3632,sequence='CR LF',occurrences=1),
        limits=['Static consumer/formatter and exact bytes only. No new confirmation selection, corrupt-save test, equipped comparison activation or pixel layout QA.',
        'No generic square-tag policy is broadened. Exact3748 literal does not become[p]/[i_]/[bg_], nor assert unrelated post-decoder parser behavior.'])
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t)
    if r['key']==LITERAL_KEY:assert t==DRAFTS[LITERAL_KEY] and s['source_text']=='[ Equipped ]'
    else:assert '[' not in t and ']' not in t
    assert re.findall(r'\r+\n|\r|\n',t)==re.findall(r'\r+\n|\r|\n',s['source_text'])
    assert not any(c in t for c in '\0\t{}$#%&*+:<=>\\^~') and not re.findall(r'\d',t)
    b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t;check_template(t,'Source owned confirmation/literal2048wide; runtime layout pending');return b
def negative_cases():
    k=3632;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('scope',dict(key=3631)),('linebreak',dict(text=r['text'].replace('\r\n','\n'))),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text=r['text']+'가'*84)),('literal_delimiter',dict(key=3748,source_text=population()[3748]['source']['source_text'],text='장착 중')),('invented_tag',dict(key=3748,source_text=population()[3748]['source']['source_text'],text='[i_장착중]'))]
SPEC=dict(name='ui_confirmations_20261021',date='20261021',config='development_ui_confirmations_20261021.json',prior_name='ui_wrappers_20261021',prior_config='development_ui_wrappers_20261021.json',prior_config_sha256='2d6380d0e1ce433c857c79e49858fd7865d95b4ef22ac7f9d5715a2704719ebd',prior_artifact_sha256='513ab59896a0d37be47a04bf0d196e261b699c1990d581d10fe50ccaf9afec26',prior_decisions=3919,expected_states=dict(untranslated=372,needs_human_review=3497,in_progress=104),write_scope='Exact3 source-owned confirmation messages and1 fixed bracket literal; preserve all decisions/save data/game behavior')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

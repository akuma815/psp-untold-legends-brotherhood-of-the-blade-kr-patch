"""42 individually authored UI strings bound through original typed wrappers."""
import argparse,sys,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
DRAFTS={
2067:'$q $n에게 말 걸기',2068:'$q 버튼을 길게 눌러 $a 입장',2873:'$a 돌아가기',3750:'$q 버튼을 눌러 $a 입장',
2139:'능력 강화 횟수: $a',2142:'$q 금화 $a개 줍기',2165:'금화 $a개 획득',2167:'$a레벨이 되어야 이 아이템을 사용할 수 있습니다',2168:'요구 레벨: $a',
2891:'생명력 $a 회복',2892:'기력 $a 회복',2893:'생명력 또는 기력 $a 회복',
3525:'$a 님에게 아이템 건네기',3565:'$a 님이 아이템을 건넸습니다',3566:'$a 님이 무언가를 건네려 합니다.',3755:'$a 직업만 사용 가능',
3616:'그 아이템들은 조합할 수 없습니다',3720:'상인과 거래하는 중에는 조합 아이템을 사용할 수 없습니다',4002:'중량 초과 상태에서는 조합 아이템을 사용할 수 없습니다.',
3909:'네트워크 시작 중 ...',3910:'네트워크 종료 중 ...',3911:'게임에 연결 중 ...',3995:'게임의 정원이 이미 찼습니다.',3996:'게임이 이미 시작되었습니다.',3997:'게임에서 추방되었습니다.',3998:'호스트의 연결이 끊겼습니다.',
2944:'허락 없이 아벤을 떠날 순 없어.',2945:'여기서는 튼튼한 밧줄이 필요하겠어.',2946:'이 문들은 마법으로 잠겨 있어!',2947:'이 그릇에 이상한 찌꺼기가 남아 있어.',2948:'이 봉인은 쓰이지 않은 에너지로 타닥거리고 있어.',2949:'차원문이 봉인되어 있어.',2950:'이 홈에 뭔가 들어갈 것 같은데...',3682:'여긴 너무 어두워서 들어갈 수 없어.',
3709:'$n 님은 지금 위험해서 대화할 수 없습니다.',3594:'총 무게',3742:'주문 피해',3743:'이동 속도',3744:'생명력 재생',3745:'기력 재생',3746:'치명타 확률 %%',3764:' 님의 연결이 끊겼습니다!'}
# Explicit key-load/call/target triples. No search result is adopted as a reference.
CALLS={2067:[(0x68404,0x68408,0x70a94)],3709:[(0x683d8,0x683dc,0x70a94)],2068:[(0x2c85c,0x2c858,0x70900)],2873:[(0x236a4,0x236a0,0x70900)],3750:[(0x2c888,0x2c884,0x70900)],
2139:[(0x28bc,0x28c0,0x6fa30)],2142:[(0x4e90,0x4e94,0x6fa30)],2165:[(0x4f6e8,0x4f6f0,0x6fa30)],2167:[(0x281dc,0x281e4,0x6fa30)],2168:[(0x13834,0x1383c,0x6fa30)],2891:[(0x27e5c,0x27e60,0x6fa30)],2892:[(0x27e90,0x27e94,0x6fa30)],2893:[(0x27e00,0x27e04,0x6fa30)],
3525:[(0x19aa8,0x19aa4,0x6fc0c),(0x23928,0x23924,0x6fc0c)],3565:[(0x17068,0x17064,0x6fc0c)],3566:[(0x21d08,0x21d1c,0x6fc0c),(0x29ca8,0x29ca4,0x6fc0c)],3755:[(0x28060,0x28064,0x6fb2c),(0x28148,0x2814c,0x6fb2c)],
3616:[(0x29678,0x29674,0x25370)],3720:[(0x296fc,0x296f8,0x25370)],4002:[(0x29764,0x29760,0x25370)],3909:[(0x6d288,0x6d284,0x6b0dc)],3910:[(0x6d2a0,0x6d29c,0x6b0dc)],3911:[(0x6d270,0x6d26c,0x6b0dc)],3995:[(0x6c014,0x6c010,0x6b42c)],3996:[(0x6c028,0x6c024,0x6b42c)],3997:[(0x6c03c,0x6c038,0x6b42c)],3998:[(0x6c078,0x6c074,0x6b42c)],
3594:[(0x27abc,0x27ac4,0x25a94),(0x27f78,0x27f80,0x25a94)],3742:[(0x27b1c,0x27b24,0x25a94)],3743:[(0x27b3c,0x27b44,0x25a94)],3744:[(0x27b54,0x27b5c,0x25a94)],3745:[(0x27b6c,0x27b74,0x25a94)],3746:[(0x27b90,0x27b98,0x25a94)],3764:[(0x7541c,0x75418,0x70678)]}
GATES={2944:[0x2c37c,0x2c3b8],2945:[0x2c384],2946:[0x2c38c],2947:[0x2c394],2948:[0x2c39c],2949:[0x2c3a4],2950:[0x2c3ac],3682:[0x2c3b4]}

@lru_cache(maxsize=1)
def population():
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};pop={}
    assert len(DRAFTS)==42 and set(DRAFTS)==set(CALLS)|set(GATES)
    for key,calls in CALLS.items():
        refs=[]
        for at,pc,target in calls:
            reg=6 if target==0x6b0dc else 5
            assert struct.unpack_from('<I',boot,at+128)[0]==0x34000000|(reg<<16)|key,(key,hex(at))
            assert struct.unpack_from('<I',boot,pc+128)[0]==0x0c000000|(target>>2)
            refs.append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=at+128,width=4,key=key,instruction=hex(at),call=hex(pc),target=hex(target),role='original_typed_UI_wrapper',expected_hex=boot[at+128:at+132].hex()))
        pop[key]=dict(source=ss[key],references=refs)
    for key,locations in GATES.items():
        refs=[]
        for at in locations:
            assert struct.unpack_from('<I',boot,at+128)[0]==0x34020000|key
            refs.append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=at+128,width=4,key=key,instruction=hex(at),call='0x2c8c0',target='2C354v0 ->705DCa1',role='original_gate_reason_selector',expected_hex=boot[at+128:at+132].hex()))
        pop[key]=dict(source=ss[key],references=refs)
    return pop

@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    from static_cache_20261021 import evidence
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();p=Profile();q=ROOT/'qa/static/20261021_ui_wrappers';q.mkdir(parents=True,exist_ok=True);windows=[]
    spans=[('numeric_a',0x6fa30,0x6fb2c),('lookup_a',0x6fb2c,0x6fc0c),('owned_wide_a',0x6fc0c,0x6fcf4),('integer_label',0x6fcf4,0x6fe20),('percent_label',0x6fe20,0x6ff94),('map_lookup_a',0x70900,0x7095c),('actor_n',0x70a94,0x70b9c),('gate_selector',0x2c354,0x2c3c4),('gate_to_decoder',0x2c8a0,0x2c8d4),('item_property_dispatch',0x25a94,0x25bdc),('inventory_error',0x25370,0x254a8),('network_progress',0x6b0dc,0x6b2c4),('network_error',0x6b42c,0x6b54c),('name_disconnect_concat',0x753d4,0x75454)]
    for label,a,z in spans:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,label);windows.append(dict(name=label,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    for k,rows in CALLS.items():
        for at,pc,target in rows:
            a=min(at,pc)-4;z=max(pc+8,at+4)+4;raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,'key'+str(k)+'_'+hex(at)[2:]);windows.append(dict(key=k,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    anchors={0x6fb00:0x02203825,0x6fbe0:0x02203825,0x6fcd0:0x02203825,0x70b74:0x02203825,0x2c8b4:0x0c00b0d5,0x2c8c0:0x0c01c177,0x2c8c4:0x00402825,0x6b170:0x0c01c177,0x6b4b4:0x0c01c177,0x75418:0x0c01c19e}
    for at,w in anchors.items():assert struct.unpack_from('<I',boot,at+128)[0]==w,(hex(at),hex(w))
    bounds={k:dict(UTF8_including_NUL=len(re.sub(r'\$[a-z]','',v).encode('utf8'))+249*len(re.findall(r'\$[a-z]',v))+1,UTF16_including_NUL=len(re.sub(r'\$[a-z]','',v).encode('utf-16le'))//2+249*len(re.findall(r'\$[a-z]',v))+1) for k,v in DRAFTS.items()}
    assert all(v['UTF8_including_NUL']<=5000 and v['UTF16_including_NUL']<=2048 for v in bounds.values())
    return dict(source_roundtrip_windows=windows,source_anchors={hex(k):hex(v) for k,v in anchors.items()},static_cache=evidence(),conservative_existing_owned_slot_bounds=bounds,
        consumer_chain=['6FA30 converts original numeric a2 and installs owned$a before formatting source key a1 through DA634/2048wide.',
        '6FB2C formats source name key a2 then installs owned$a and formats key a1. 70900 obtains original map u16key and delegates6FB2C. 3755 receives original class-name key. No class/map ID invented.',
        '6FC0C copies caller-owned wide string into$a. 70A94 derives$n from actor+1830definition or literalNPC fallback. Same token ownership and lookup priority retained.',
        '25A94 positive-property dispatch formats original labels via6FCF4 integer or6FE20percent, then copies UI strings. All thresholds, stat arithmetic and percent control remain unchanged.',
        '2C354 selects original gate reason and returns source key in v0;2C8B4 call feeds returnedv0 into705DCa1 at2C8C4. Original jump table and default retained.',
        'Network progress6B0DC takeskeya2 into s1->705DC;network error6B42C keya1->s0->705DC. Existing inventory error25370 keya1->705DC. No network/save/trade/game actions executed.',
        '753D4 copies original player name into stack wide string,70678raw converts3764,BDDCC appends suffix,14F34 queues notification. Leading space and exclamation preserved.'],
        semantic_notes=['42 complete strings individually authored. 아벤/생명력/기력/금화 follow current manuscripts, no approved terminology expansion.',
        'Speaker/name tokens retain exact order; 님 provides a fixed grammatical anchor without guessing variable final consonants. Map/class expansions use noun phrases without a variable-dependent particle.',
        'Gate messages retain first-person observation and access reasons; no NPC identity, quest stage or actual gate activation is inferred.',
        'Source-equal numeric formats3085/3086/3087 and bracketed3748 remain outside this cohort. No RSC duplicate merged.',
        'Bounds use existing249byte-owned-slot envelope and source wrappers; they are not all possible expansion semantics, pixel layout, network or property-popup runtime proof. Current42 new texts require representative runtime checks.'])

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and re.findall(r'\$[a-z]',t)==re.findall(r'\$[a-z]',s['source_text'])
    plain=re.sub(r'\$[a-z]','',t);assert not any(c in plain for c in '\0\r\n\t[]{}$#&*+<=>\\^~')
    assert t.count('%')==s['source_text'].count('%') and t.count(':')==s['source_text'].count(':') and t.count('!')==s['source_text'].count('!')
    assert re.findall(r'\d+',t)==re.findall(r'\d+',s['source_text'])
    if r['key']==3764:assert t.startswith(' ') and not t.startswith('  ')
    b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t;check_template(t,'Pinned source wrappers/owned slots; dynamic/pixel runtime pending');return b

def negative_cases():
    k=2142;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=3748)),('new_control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text=r['text']+'가'*84)),('lost_gold',dict(text=r['text'].replace('$a',''))),('changed_button',dict(text=r['text'].replace('$q','$x'))),('token_order',dict(text='$a 금화 $q 줍기')),('lost_percent',dict(key=3746,source_text=population()[3746]['source']['source_text'],text='치명타 확률 %')),('lost_separator',dict(key=3764,source_text=population()[3764]['source']['source_text'],text=DRAFTS[3764].lstrip()))]

SPEC=dict(name='ui_wrappers_20261021',date='20261021',config='development_ui_wrappers_20261021.json',prior_name='item_events_20261021',prior_config='development_item_events_20261021.json',prior_config_sha256='b963ba97e8704531175baae3c3f4e581256923b37bb6ebce4e5a572fdd24c4a2',prior_artifact_sha256='2ae02fd3ccd80abc2b9c96e6e890726058ae2c68cdb8310597e92364c153989b',prior_decisions=3877,expected_states=dict(untranslated=376,needs_human_review=3493,in_progress=104),write_scope='Exact42 original wrapper-bound static UI texts, no game IDs/logic/network/save changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

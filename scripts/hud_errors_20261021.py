"""43 formatted HUD/inventory errors; two raw-cache messages held outside SSOT."""
import argparse,sys,struct,re,unicodedata
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
DRAFTS={2150:'아이템이 너무 무겁습니다!',2151:'아이템을 넣을 공간이 없습니다!',2536:'탄약이 얼마 남지 않았습니다!',2154:'레벨을 올리려면 SELECT 버튼을 누르세요!',2147:'탄약이 없습니다!',2529:'물약이 없습니다!',2537:'마지막 물약을 사용했습니다!',2535:'물약이 1개 남았습니다!',2534:'물약이 2개 남았습니다!',2533:'물약이 3개 남았습니다!',3653:'순간이동 장치가 활성화되었습니다',2149:'금화가 부족합니다!',2148:'기력이 부족합니다!',2152:'펫이 없습니다!',2153:'이미 펫이 있습니다!',2870:'폭탄이 너무 많습니다!',3043:'방패를 장착하지 않았습니다',3606:'양손 근접 무기를 장착하지 않았습니다!',3042:'활을 장착하지 않았습니다',3617:'원거리 무기 사용 불가',3658:'강화 효과가 이미 적용 중입니다',3842:'근접 무기가 필요합니다!',2155:'떠나기 전에 퀘스트를 완료해야 합니다.',3912:'아군 전환 면역!',3765:'기절 면역!',3766:'속박 면역!',3768:'빙결 면역!',3767:'석화 면역!',3769:'공포 면역!',3509:'멀티플레이를 하려면 WLAN 스위치를 켜야 합니다',4008:'슬립 모드가 활성화되어 연결이 끊겼습니다',
2157:'현재 캐릭터 레벨로는 이 아이템을 사용할 수 없습니다',4001:'공격 중에는 무기를 바꿀 수 없습니다.',2163:'인벤토리에 이 아이템을 넣을 공간이 없습니다.',3994:'해당 플레이어의 인벤토리에 그 아이템을 넣을 공간이 없습니다.',2159:'이 아이템은 버릴 수 없습니다.',2158:'여기서는 그 아이템을 버릴 수 없습니다.',2162:'더 이상 무게를 감당할 수 없습니다.',3999:'해당 플레이어는 더 이상 무게를 감당할 수 없습니다.',2161:'이 아이템은 판매할 수 없습니다.',2160:'이 아이템을 구입할 금화가 부족합니다.',2842:'먼저 이 아이템의 장착을 해제해야 합니다.',3562:'해당 플레이어가 사망했습니다',3563:'거래할 대상이 없습니다',3564:'거래 상대가 너무 멀리 있습니다'}
RAW_CANDIDATES={k:DRAFTS[k] for k in [3509,4008]}
DRAFTS={k:v for k,v in DRAFTS.items() if k not in RAW_CANDIDATES}
@lru_cache(maxsize=1)
def population():
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};refs=defaultdict(list)
    for pc in range(4,len(boot)-135,4):
        previous,call,delay=struct.unpack_from('<III',boot,pc+124)
        if call!=0x0c0053ac:continue
        if delay>>16==0x3405:key=delay&65535;at=pc+4;kind='key_in_delay'
        elif previous>>16==0x3405:
            key=previous&65535;at=pc-4;kind='key_before_call'
            if key in DRAFTS:assert delay in [0x00003025,0x34060000,0],(hex(pc),hex(delay))
        else:continue
        if key in DRAFTS:refs[key].append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=at+128,width=4,key=key,call=hex(pc),instruction=hex(at),binding=kind,target='14EB0',role='HUD_notification',expected_hex=boot[at+128:at+132].hex()))
    for pc in range(0x252e0,0x2535c,4):
        w=struct.unpack_from('<I',boot,pc+128)[0]
        if w>>16==0x3406 and w&65535 in DRAFTS:
            key=w&65535;refs[key].append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=pc+128,width=4,key=key,instruction=hex(pc),binding='inventory_error_switch_a2_key_to_a1',target='25370',role='inventory_error',expected_hex=boot[pc+128:pc+132].hex()))
    assert set(refs)==set(DRAFTS) and len(DRAFTS)==43
    return {k:dict(source=ss[k],references=v) for k,v in refs.items()}
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();q=ROOT/'qa/static/20261021_hud_errors';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    spans=[('notification_decoder_branches',0x14eb0,0x14f34),('owned_four_notification_queue',0x14f34,0x150c0),('inventory_error_switch',0x252b4,0x25370),('inventory_error_owned_dialog',0x25370,0x254a8),('formatted_decoder',0x705dc,0x70678),('raw_decoder',0x70678,0x706fc),('raw_lookup_converter',0xda740,0xda810),('raw_cache_only',0xdb588,0xdb5e4)]
    for label,a,z in spans:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,label);windows.append(dict(name=label,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    for key,item in population().items():
        for ref in item['references']:
            if 'call' not in ref:continue
            pc=int(ref['call'],16);a=min(pc-8,int(ref['instruction'],16));z=pc+12;raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,'key'+str(key)+'_'+hex(pc)[2:]);windows.append(dict(key=key,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d),scope='minimal argument/call window'))
    anchors={0x14f0c:0x0c01c177,0x14ee4:0x0c01c19e,0x14f18:0x0c0053cd,0x14fd0:0x0c02f72c,0x15074:0x0c02f72c,0x2535c:0x0c0094dc,0x25360:0x00c02825,0x25410:0x0c01c177,0x2541c:0x0c02f72c}
    for pc,w in anchors.items():assert struct.unpack_from('<I',boot,pc+128)[0]==w,(hex(pc),hex(w))
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};es={e['id']:e for e in lines(ROOT/'workspace/translation/entries.jsonl')};ds=decisions();s=ss[3096];e=es[s['id']];did=e['development_diagnostic_selection'];assert did
    return dict(source_roundtrip_windows=windows,source_anchors={hex(k):hex(v) for k,v in anchors.items()},
        original17_case_error_target_table_hex=boot[0x139028+128:0x139028+128+17*4].hex(),
        related_conversion_description=dict(source=s,decision=did,manuscript=resolve(ds[did])),
        raw_cache_candidates_not_selected=[dict(key=k,text=v,reason='14EB0a2=1 ->70678/DA740/DB588 cache-only branch. Cachebank identity/loading remainsunresolved; notincluded inSSOT, config orgame writes.') for k,v in RAW_CANDIDATES.items()],
        consumer_chain=['14EB0 carries a1key throughs0, uses705DC whena2zero or70678 rawlookup otherwise, both2048wide; calls14F34 tocopy ownednotification text andmaintain originalfour-slot queue.',
        '252B4 chooses originalerror keys ina2,2535C calls25370 witha1=a2. 25370 copies key tos0,25410calls705DC,2541C copies ownedUI5E0; originaldialog controls/condition mapping unchanged.'],
        semantic_notes=['43 complete selected messages individually authored; twoadditional raw-cache candidate translations remainoutsideSSOT/config. No condition, threshold, status timer, queue limit, trade/drop/save/network action or state changed.',
        '1/2/3potion counts andexclamations retained. Ammo탄약/Power기력/Gold금화 follow current UI proposals; SELECT andWLAN remainidentifiable hardware labels.',
        'Pet stays펫 without asserting summon class or spell identity. Convert uses아군 전환 based onexisting source3096 conversion description, no immunity mechanism changed.',
        'Root/Stun/Freeze/Stone/Fear rendered속박/기절/빙결/석화/공포. Newstatus naming proposals remainhumanreview pending.',
        'Selectederrors distinguishyou versusotherplayer, no space versusweight, droppinghere versusitemcannotdrop, no target versusoutofrange, anddeath versusdisconnect.',
        'Sourcecall/ownedcopy evidence is not natural faulttrigger, trade, hardwareWLAN/SleepMode, network orpixel-layout QA. Allrelease claims withheld.'])
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\d+',t)==re.findall(r'\d+',s['source_text']) and t.count('!')==s['source_text'].count('!')
    if r['key']==3509:assert 'WLAN' in t
    if r['key']==2154:assert 'SELECT' in t
    b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t;check_template(t,'Originalmessage decoders2048wide; conservative250input andownedcopy, geometry pending');return b
def negative_cases():
    k=2535;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=2156)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text=r['text']+'가'*84)),('potion_count',dict(text=r['text'].replace('1','2'))),('lost_exclamation',dict(text=r['text'].replace('!','')))]
SPEC=dict(name='hud_errors_20261021',date='20261021',config='development_hud_errors_20261021.json',prior_name='ui_direct_20261021',prior_config='development_ui_direct_20261021.json',
          prior_config_sha256='56bd8d06cac5c779fc6c685820ca44b88315b1d6b9aa90d86f37b8121c37901c',prior_artifact_sha256='83588648d5ac282cd35be3b5622bec2c8be3c432b2078c9a418c1f4582741439',
          prior_decisions=3827,expected_states=dict(untranslated=425,needs_human_review=3444,in_progress=104),write_scope='Exact43 static formatted HUD/inventoryerror message keys; exclude rawcache3509/4008, preservealloriginalgame conditions andqueue/dialog behavior')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

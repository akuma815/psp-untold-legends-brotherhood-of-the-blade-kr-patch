"""Threeitem event texts/twoidentity forms/tworaw-cache notices after bank proof."""
import argparse,sys,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines
from text_limits import check_template
DRAFTS={2066:'$q $o 줍기',3656:'$o 아이템을 $n에게 건넸습니다.',2166:'$o 획득',2079:' $a $b',3144:'$a%%',3509:'멀티플레이를 하려면 WLAN 스위치를 켜야 합니다',4008:'슬립 모드가 활성화되어 연결이 끊겼습니다'}
FORM_KEYS={2079,3144}
CALLS={2066:[0x70384],3656:[0x704d8],2166:[0x705b0],2079:[0x6fdf0,0x6ff64],3144:[0x6fecc,0x70fec,0x71088]}
RAW={3509:0x73d20,4008:0x73d48}
@lru_cache(maxsize=1)
def population():
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};pop={}
    for key,calls in CALLS.items():
        refs=[]
        for pc in calls:
            assert struct.unpack_from('<II',boot,pc+128)==(0x0c03698d,0x34070000|key)
            refs.append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=pc+128,width=8,key=key,call=hex(pc),target='DA634',key_register='a3',role='item_event_or_numeric_format',expected_hex=boot[pc+128:pc+136].hex()))
        pop[key]=dict(source=ss[key],references=refs)
    for key,pc in RAW.items():
        assert struct.unpack_from('<III',boot,pc+124)==(0x34050000|key,0x0c0053ac,0x34060001)
        pop[key]=dict(source=ss[key],references=[dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=pc+124,width=12,key=key,call=hex(pc),target='14EB0a2=1->70678rawstaticcache',role='raw_cache_notice',expected_hex=boot[pc+124:pc+136].hex())])
    assert set(pop)==set(DRAFTS)
    return pop
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    from static_cache_20261021 import evidence
    cache=evidence();save_json(ROOT/'qa/reports/static_cache_20261021.json',cache)
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();q=ROOT/'qa/static/20261021_item_events';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    for label,a,z in [('pickup_item_composition',0x70180,0x703b0),('give_item_n_and_o',0x703b0,0x70508),('received_item_o',0x70508,0x705dc),('raw_notice_callers',0x73d04,0x73d60)]:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,label);windows.append(dict(name=label,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    # Each unchanged format has at least one independently pinnedcallsite; allknowncalls abovearefixed.
    for key in FORM_KEYS:
        for pc in CALLS[key]:
            raw=boot[pc+120:pc+156];d=p.verify_roundtrip(raw,pc-8,q,'format'+str(key)+'_'+hex(pc)[2:]);windows.append(dict(key=key,start=hex(pc-8),sha256=digest(raw),instructions=len(d),scope='minimal callsite'))
    bounds={}
    for key,text in DRAFTS.items():
        count=len(re.findall(r'\$[a-z]',text));literal=re.sub(r'\$[a-z]','',text)
        bounds[key]=dict(utf8_bytes_including_NUL=count*249+len(literal.encode('utf8'))+1,utf16_units_including_NUL=count*249+len(literal.encode('utf-16le'))//2+1)
        assert bounds[key]['utf8_bytes_including_NUL']<=5000 and bounds[key]['utf16_units_including_NUL']<=2048
    return dict(source_roundtrip_windows=windows,static_cache_source_provenance=cache,
        consumer_chain=['70180 helper setsbase/prefix/suffix, uses samefour originalitemforms, then70368 setsowned$o and70384 formats2066 with2048wide.',
        '703B0 decodesitem key ->70444owned$o; 70474DA1EC installsname$n from actor+1830definition or704BC setsfallbackliteralNPC viaDA478;704D8 formats3656.',
        '70508 decodesitemkey ->70594owned$o ->705B0 formats2166. No recipient name oritemname inferred fromportrait/storageadjacency.',
        '2079 and3144 are unchanged numeric/labelformat controls, not translatedprose. Exactbytes/tokens/percent runs retained.',
        '3509/4008 retain14EB0a2=1. Newsourcecache proof linksformatter+8->DB+4->%s/%s_static.dat, withprioritylookup beforedynamicDB+0. No engine, hardware ornetwork behavior changes.'],
        control_only_identity_entries=sorted(FORM_KEYS),conservative_slot_capacity_bounds=bounds,
        limits=['Bounds use249UTF8bytes perexistingownedslot plusNUL andliteral text; sourcebutton tokens staybyte/orderexact. Static bound isnot nativeformatter or pixelgeometry proof.',
                'Objectparticle isattached tofixed아이템 sounknownitemname finalconsonants donot choosea wrongdynamicparticle; recipient에게 isfixed.',
                'Rawcandidates wereexcluded fromprior43cohort beforestaticcacheprovenance wasclosed; nowselectedundernewboundcontext. Frozenoldreports remainhistorical.',
                'No pickup/trade/network/PSPswitch/SleepMode/save action executed. SourceRSC duplicatesremainseparate andunmodified.'])
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and re.findall(r'\$[a-z]',t)==re.findall(r'\$[a-z]',s['source_text'])
    if r['key'] in FORM_KEYS:assert t==s['source_text']==DRAFTS[r['key']]
    plain=re.sub(r'\$[a-z]','',t);assert not any(c in plain for c in '\0\r\n\t[]{}$#&*+<=>\\^~') and t.count('%')==s['source_text'].count('%')
    if r['key']==3509:assert 'WLAN' in t
    b=encoder(t,book).encode('utf8');assert len(b)+1<=5000 and decoder(b.decode('utf8'),book)==t;check_template(t,'Pinned2048wide formatted/rawconsumers; dynamic ownedslot bounds incontext');return b
def negative_cases():
    k=2066;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=2067)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text=r['text']+'가'*2048)),
        ('lost_object',dict(text=r['text'].replace('$o',''))),('changed_button',dict(text=r['text'].replace('$q','$x'))),('order',dict(text='$o $q 줍기')),('changed_percent_control',dict(key=3144,source_text=population()[3144]['source']['source_text'],text='$a%'))]
SPEC=dict(name='item_events_20261021',date='20261021',config='development_item_events_20261021.json',prior_name='hud_errors_20261021',prior_config='development_hud_errors_20261021.json',
          prior_config_sha256='dcbfd2b4e653cb1953105dde2749b819789f67232517a498f2bc502c1e688313',prior_artifact_sha256='c265b979e1e84e1a9bcc69e4ee88e55d7c78225dfa07f65c92d6f382479c9be6',
          prior_decisions=3870,expected_states=dict(untranslated=418,needs_human_review=3451,in_progress=104),expected_unchanged_static_keys=[2079,3144],write_scope='Exactthree itemmessages/twoidentityformats/tworawcache notices aftersourcebankproof; alloriginalbehaviors preserved')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

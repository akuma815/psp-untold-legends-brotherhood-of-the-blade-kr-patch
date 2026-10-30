"""57 exact static UI entries; pinned constantkey in direct705DC call delay slot."""
import argparse,sys,struct,re,unicodedata
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from ui_direct_drafts_20261021 import DRAFTS
@lru_cache(maxsize=1)
def population():
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};refs=defaultdict(list)
    for pc in range(0,len(boot)-135,4):
        call,delay=struct.unpack_from('<II',boot,pc+128)
        if call!=0x0c01c177 or delay>>16!=0x3405:continue
        key=delay&65535
        if key not in DRAFTS:continue
        refs[key].append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=pc+128,width=8,call=hex(pc),delay_slot=hex(pc+4),expected_hex=boot[pc+128:pc+136].hex(),role='direct_UI_lookup',target='705DC',key_register='a1',key=key))
    assert len(DRAFTS)==57 and set(refs)==set(DRAFTS) and 3748 not in refs
    return {k:dict(source=ss[k],references=v) for k,v in refs.items()}
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();q=ROOT/'qa/static/20261021_ui_direct';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    # Minimal executable callsite windows, not a claim to roundtrip every whole parent function.
    for key,item in population().items():
        for ref in item['references']:
            pc=int(ref['call'],16);a=pc-8;z=pc+28;raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,'key'+str(key)+'_'+hex(pc)[2:]);windows.append(dict(key=key,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d),scope='minimal callsite'))
    for label,a,z in [('shared_decoder',0x705dc,0x70678),('wide_formatter_lookup',0xda634,0xda740)]:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,label);windows.append(dict(name=label,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    return dict(source_roundtrip_windows=windows,
        consumer_chain='Pinned originalJAL705DC with its executed delay slotORI a1,zero,key. This passesexactsource key to705DC->DA6342048wide/5000byte formatter. Originalcallers andgame actions unchanged.',
        semantic_notes=['57 complete texts authored individually: inventory/shop/ability prompts, feedback, teleport/save/exit questions, story/menu andmultiplayer messages. Allnumeric/sourcecontrols andbutton order retained.',
        'SinglePlayer/Join/Host andContinue/Restart stay distinct choices. Kick, save, exit andcancel are translated labels; no such actions executed during this session.',
        'Shop greeting retains Guardian andmerchantshop context; speaker identity not inferred. InstantDeath/Blocked/Resisted are feedback text only, no combatmechanic changes.',
        'No variables added or removed. $q/$x/$c/$t/$u/$d etc retain exact bytes andorder; existing formatter ownership unchanged. No source-equal control-only entries in this cohort.',
        'Static3748[ Equipped ] excluded: bracket-literal versus parsercontrol handling requires separate proof. SourceRSC duplicates not merged or implicitly translated.',
        'Direct lookup proves codeconsumer, not natural route reachability, networking/saving behavior or dialogwidth. All57 actualscreens andnewbutton geometry remain runtimeQA.'])
def tokens(t):return re.findall(r'\$[a-z]',t)
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and tokens(t)==tokens(s['source_text'])
    plain=re.sub(r'\$[a-z]','',t);assert not any(c in plain for c in '\0\r\n\t[]{}$#%&*+<=>\\^~')
    assert t.count('!')==s['source_text'].count('!') and t.count(':')==s['source_text'].count(':') and re.findall(r'\d+',t)==re.findall(r'\d+',s['source_text'])
    if s['source_text'].startswith(' '):assert t.startswith(' ')
    b=encoder(t,book).encode('utf8');assert len(b)+1<=5000 and decoder(b.decode('utf8'),book)==t;check_template(t,'Direct705DC2048wide, sourcebutton controls retained; geometry pending');return b
def negative_cases():
    k=2140;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('excluded_bracket_literal',dict(key=3748)),('new_control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text=r['text']+'가'*2048)),
        ('button_lost',dict(text=r['text'].replace('$x',''))),('button_changed',dict(text=r['text'].replace('$x','$q'))),('button_order',dict(text='$c 닫기 $x 슬롯 지정')),('invented_variable',dict(text=r['text']+'$a'))]
SPEC=dict(name='ui_direct_20261021',date='20261021',config='development_ui_direct_20261021.json',prior_name='stat_help_20261021',prior_config='development_stat_help_20261021.json',
          prior_config_sha256='a91a80fe34c5e44b18fc56f009decd0d563628747a494d45f4e5f739ed24bfcf',prior_artifact_sha256='ae05102b6f9065b9231fea27b3c1a304d319cbf373e77de25d90a2418274d921',
          prior_decisions=3770,expected_states=dict(untranslated=468,needs_human_review=3401,in_progress=104),write_scope='Exact57 directsource UI lookup keys; controls/order preserved, no actions ornetwork/save behavior changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

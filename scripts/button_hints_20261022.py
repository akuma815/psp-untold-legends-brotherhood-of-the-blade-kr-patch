"""Three source-bound fixed bracket hints; original dynamic button tokens preserved."""
import argparse,json,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from text_limits import check_template
import quest_batch_pipeline as pipeline
from pending_story_drafts_20261020 import DRAFTS as OLD_DRAFTS

KEYS={2268,2289,3721};DRAFTS={k:OLD_DRAFTS[k] for k in sorted(KEYS)}
NAME='button_hints_20261022';POLICY='hint3_original_dynamic_buttons_fixed_brackets_CRLF_2048_v1';BASE=ROOT/'workspace/translation'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='npc_pages_preserve_20261022',prior_config='development_npc_pages_preserve_20261022.json',prior_config_sha256='d9a389a91958f64e088d2418265dc901c2be22360474be7590cbe9289f59d4e8',prior_artifact_sha256='f3fa546b4205b9f0d9f78d29d70feccfcc68aa70acb47dca1369453935282481',new_authored_count=0)
LITERALS={
2268:['[캐릭터 화면을 보려면 $y 버튼을 누르세요]','[일시정지 메뉴를 보려면 $z 버튼을 누르세요]'],
2289:['[$z 버튼을 눌러 일시정지 메뉴를 여세요]','["아벤으로 귀환"을 선택하세요]'],
3721:['[생명력 물약을 사용하려면 $l 버튼을 누르세요]','[기력 물약을 사용하려면 $r 버튼을 누른 채 $l 버튼을 누르세요]'],
}
@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key'] in KEYS};assert set(ss)==KEYS
    data=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for s in ss.values():
        b=data[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    return ss

def context():
    from translation_scope import collect
    sc,_=collect();refs={r['key']:r['typed_references'] for r in sc if r['bank']=='trans' and r['key'] in KEYS}
    expected={2268:[(14,41,4)],2289:[(15,76,32)],3721:[(15,74,32)]};fields={k:[(r['table'],r['row'],r['field']) for r in rr] for k,rr in refs.items()};assert fields==expected
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    rows=[]
    for k,rr in fields.items():
        for table,row,f in rr:
            off,n=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];raw=db[off+row*stride:off+(row+1)*stride]
            assert row<n and struct.unpack_from('<I',raw,f)[0]==k;rows.append(dict(table=table,row=row,field=f,key=k,complete_hex=raw.hex()))
    return dict(fields=fields,complete_rows=rows,button_tokens='Original $y/$z/$l/$r order and arguments must be preserved; no literal button-name substitution authorized or adopted.',
        literal_brackets='Source C3024 retains full literal instructional brackets; only the exact three authored pairs are admitted. Original button token order/arguments preserved.',
        quoted_UI_consistency='Held2289 아벤으로 귀환 matches already selected3067 wording, without treating the two records as aliases.',actual_original_event_or_NPC_trigger_tested=False,build_policy_adopted=True,source_runtime='qa/reports/button_hints_source_20261022_runtime.json',release_eligible=False)

FIELDS=context()['fields']

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    k=r['key'];s=sources()[k]['source_text'];t=r['text'];assert r['source_text']==s and t and t==unicodedata.normalize('NFC',t)
    source_tags=re.findall(r'\[[^\]]+\]',s);images=re.findall(r'\[i_[^]]+\]',s)
    assert len(images)==int(k==2289) and len(source_tags)==2+len(images) and all(tag.startswith('[i_') or '$' in tag or tag=='[Select "Recall to Aven"]' for tag in source_tags)
    assert re.findall(r'\[[^\]]+\]',t)==images+LITERALS[k]
    if images:assert s.startswith(images[0]) and t.startswith(images[0])
    assert re.findall(r'\$[A-Za-z0-9]',t)==re.findall(r'\$[A-Za-z0-9]',s) and t.count('$')==s.count('$')
    body=re.sub(r'\[[^\]]+\]','',t);assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',s)==re.findall(r'\r\n+',t) and '\r' not in t.replace('\r\n','') and '\n' not in t.replace('\r\n','')
    data=encoder(t,book).encode('utf8');assert decoder(data.decode('utf8'),book)==t and len(data)<=65535
    check_template(t,'Exact fixed hints; dynamic original two-byte dollar button tokens preserved, not replaced')
    return data

def select():
    source_qa=json.loads((ROOT/'qa/reports/button_hints_source_20261022_runtime.json').read_text(encoding='utf8'));assert source_qa['keys']==sorted(KEYS) and source_qa['all_bindings_nonempty']
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256'];cfg=json.loads(cfgpath.read_text(encoding='utf8'))
    es=lines(BASE/'entries.jsonl');byid={e['id']:e for e in es};before={e['id']:serialized([e]) for e in es};ds=decisions();assert len(ds)==4326
    src=sources();rows={k:dict(key=k,source_text=src[k]['source_text'],text=t,control_policy=POLICY) for k,t in DRAFTS.items()}
    for r in rows.values():validate(r,pipeline.BOOK,encode_unicode,decode_unicode)
    negative=[];sample=rows[2268]
    for label,change in [('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3065)),('binding_removed',dict(text=DRAFTS[2268].replace('$y',''))),('binding_swapped',dict(text=DRAFTS[2268].replace('$y','$l'))),('literal_button_name',dict(text=DRAFTS[2268].replace('$y','SELECT'))),('literal_bracket_lost',dict(text=DRAFTS[2268].replace(']','',1))),('new_control',dict(text='*B'+DRAFTS[2268])),('paragraph_lost',dict(text=DRAFTS[2268].replace('\r\n\r\n','',1))),('NUL',dict(text=DRAFTS[2268]+'\0'))]:
        try:validate(dict(sample,**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261022_before_button_hints';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for k,r in rows.items():
        e=byid[src[k]['id']];old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==DRAFTS[k]
        did=f'development_{NAME}:trans:{k}';records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact three table14/15 hint references only; no DB/code changes'),
            rationale='Original source formatter produces nonempty button glyphs and retains literal instructional brackets. Exact old authored wording and original dollar tokens/order preserved; no literal button mapping.',
            semantic_impact='Existing narrator/Kaylee voice and quoted selected3067 label retained. Mode2/quest-dialogue natural trigger and human semantic/layout approval remain pending.',state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    target={r['source_id'] for r in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in target)
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4329 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_THREE_UNCHANGED_HINT_DRAFTS_ORIGINAL_DYNAMIC_BUTTONS_DEVELOPMENT_SELECTED',authored=3973,selected=3531,working_unselected=442,decision_history=4329,new_authored=0,new_selected=3,negative_cases=negative,
        previous_wording_and_refs_unchanged=True,six_original_dollar_tokens_preserved=True,button_tokens_not_replaced_in_translation_assets=True,new_human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='select':select()
    else:pipeline.audit(SPEC,__import__('button_hints_20261022'),DRAFTS,{})

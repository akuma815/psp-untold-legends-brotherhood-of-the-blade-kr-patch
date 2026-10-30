"""Four exact NPC-only manuscripts with original portrait and p marker order."""
import argparse,json,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from text_limits import check_template
from npc_exception_drafts_20261020 import DRAFTS as OLD_DRAFTS
import quest_batch_pipeline as pipeline

NAME='npc_pages_preserve_20261022';KEYS={2570,2580,2584,2585};POLICY='NPC4_exact_original_portrait_p_order_segment_CRLF_2048_v1'
DRAFTS={k:OLD_DRAFTS[k] for k in sorted(KEYS)};BASE=ROOT/'workspace/translation'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='npc_marker_preserve_20261022',prior_config='development_npc_marker_preserve_20261022.json',prior_config_sha256='b5b1e29cf5ff8a6b1573c38ce8a7e31adb2437cfc92e5ae61049f55b6a74f75f',prior_artifact_sha256='305da171ae78f693504c30b385848954c20ccbf21161b1ef235663965b472f68',new_authored_count=0)

@lru_cache(maxsize=1)
def sources():
    src={s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans' and s['key'] in KEYS};assert set(src)==KEYS
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for s in src.values():
        b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    return src

@lru_cache(maxsize=1)
def context():
    from translation_scope import collect
    scope,_=collect();refs={r['key']:r['typed_references'] for r in scope if r['bank']=='trans' and r['key'] in KEYS}
    expected={2570:[(13,15,60)],2580:[(13,16,80)],2584:[(13,17,76)],2585:[(13,17,80)]}
    fields={k:[(r['table'],r['row'],r['field']) for r in v] for k,v in refs.items()};assert fields==expected and all(r['role']=='npc_dialogue' for rr in refs.values() for r in rr)
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2' and digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    off,n=struct.unpack_from('<II',db,104);rows={}
    for k,rr in fields.items():
        for table,row,field in rr:
            assert row<n and struct.unpack_from('<I',db,off+row*260+field)[0]==k;rows[row]=db[off+row*260:off+(row+1)*260].hex()
    assert boot[0x13c9a4:0x13c9ae]==b'[p]\0[i_\0]\0'
    return dict(fields=fields,complete_table13_rows=rows,source_runtime='qa/reports/npc_pages_source_20261022_runtime.json',consumer_static='qa/reports/npc_markers_20261022_static.json',
        policy='Preserve exact source initial portrait and all[p] markers/order/per-segment CRLF. No forced page-break semantics or other-mode policy adopted.',
        narrative='Existing Kaylee informal and elected-Crown sense, Draven formal and Diana admonition wording retained; no new term or voice approval.',
        runtime_scope='Original source-bound common C3024 fixture is separate from actual NPC actor/phase and geometry.',release_eligible=False)
FIELDS=context()['fields']

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    k=r['key'];s=sources()[k]['source_text'];t=r['text'];assert r['source_text']==s and t and t==unicodedata.normalize('NFC',t)
    tags=re.findall(r'\[[^\]]+\]',s);assert len(tags)==(7 if k==2570 else 2) and re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tags[0]) and tags[1:]==['[p]']*(6 if k==2570 else 1)
    assert re.findall(r'\[[^\]]+\]',t)==tags and s.startswith(tags[0]) and t.startswith(tags[0])
    for a,b in zip(re.split(r'\[i_[^]]+\]|\[p\]',s),re.split(r'\[i_[^]]+\]|\[p\]',t)):assert re.findall(r'\r\n+',a)==re.findall(r'\r\n+',b)
    body=re.sub(r'\[i_[^]]+\]|\[p\]','',t);assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    data=encoder(t,book).encode('utf8');assert decoder(data.decode('utf8'),book)==t and len(data)<=65535
    check_template(t,'NPC706FC cap2048, exact original p markers preserved; geometry separate')
    return data

def select():
    evidence=json.loads((ROOT/'qa/reports/npc_pages_source_20261022_runtime.json').read_text(encoding='utf8'));assert evidence['keys']==sorted(KEYS) and evidence['original_p_positions_verified']
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256'];cfg=json.loads(cfgpath.read_text(encoding='utf8'))
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};byid={e['id']:e for e in es};ds=decisions();assert len(ds)==4322
    src=sources();rows={k:dict(key=k,source_text=src[k]['source_text'],text=t,control_policy=POLICY) for k,t in DRAFTS.items()}
    for r in rows.values():validate(r,pipeline.BOOK,encode_unicode,decode_unicode)
    sample=rows[2570];negative=[]
    for label,change in [('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3115)),('p_removed',dict(text=DRAFTS[2570].replace('[p]','',1))),('p_added',dict(text=DRAFTS[2570]+'[p]')),('portrait_removed',dict(text=DRAFTS[2570].replace('[i_PI_GoodKaylee]',''))),('segment_CRLF_removed',dict(text=DRAFTS[2570].replace('\r\n','',1))),('macro_added',dict(text=DRAFTS[2570]+'*B')),('NUL',dict(text=DRAFTS[2570]+'\0'))]:
        try:validate(dict(sample,**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261022_before_npc_pages_preserve';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for k,r in rows.items():
        e=byid[src[k]['id']];old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==DRAFTS[k]
        did=f'development_{NAME}:trans:{k}';records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Only four original NPC table13 text keys; no DB/code changes'),rationale='Exact original p marker order/paragraphs and portrait retained, source fixture p-vector positions verified. No forced-page semantics or actual NPC natural trigger claim.',semantic_impact='Existing individual wording unchanged; names, offices, voice and layout await human review.',state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    target={d['source_id'] for d in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in target)
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4326 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_FOUR_UNCHANGED_NPC_P_MARKER_DRAFTS_DEVELOPMENT_SELECTED',authored=3973,selected=3528,working_unselected=445,decision_history=4326,new_authored=0,new_selected=4,negative_cases=negative,all_nine_original_p_markers_preserved=True,previous_wording_and_refs_unchanged=True,actual_NPC_runtime_pending=True,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='select':select()
    else:pipeline.audit(SPEC,__import__('npc_pages_preserve_20261022'),DRAFTS,{})

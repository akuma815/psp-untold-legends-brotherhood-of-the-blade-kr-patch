"""Eighteen NPC-only proposals, unchanged wording and complete original *B effects."""
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

NAME='npc_marker_preserve_20261022';POLICY='NPC18_exact_original_marker_and_starB_effect_preserve_v1'
KEYS={2280,2281,2284,2285,2309,2320,2322,2325,2332,2333,2351,2352,2353,2354,2363,2364,2365,2366}
DRAFTS={k:OLD_DRAFTS[k] for k in sorted(KEYS)};BASE=ROOT/'workspace/translation'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='document_zero_20261022',prior_config='development_document_zero_20261022.json',prior_config_sha256='9f1719747a3402d41728eeb30641a391d4a6ef2098cdcebacdbf424ed47447af',prior_artifact_sha256='255060d94ce412374a5227fb295dbebd71d57952471a24a833b60095be3bcc5f',new_authored_count=0)

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
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,104);fields={};rows={}
    for k,rr in refs.items():
        assert rr and all(r['table']==13 and r['role']=='npc_dialogue' for r in rr)
        fields[k]=[(13,r['row'],r['field']) for r in rr]
        for r in rr:
            assert r['row']<n and struct.unpack_from('<I',db,off+r['row']*260+r['field'])[0]==k
            rows[r['row']]=db[off+r['row']*260:off+(r['row']+1)*260].hex()
    assert set(fields)==KEYS
    static=json.loads((ROOT/'qa/reports/npc_markers_20261022_static.json').read_text(encoding='utf8'))
    assert static['status']=='PASS_SOURCE_ASTERISK_REFLEXIVE_DISPATCH_AND_NPC_ACTOR_BOUNDARY'
    return dict(fields=fields,complete_table13_rows=rows,source_runtime='qa/reports/npc_markers_source_20261022_runtime.json',source_static='qa/reports/npc_markers_20261022_static.json',
        excluded_aliases=[2334,2335],policy='Preserve complete source diagnostic suffix byte-for-byte and its final-paragraph consumption order. *B is actor-dependent formatting, not a literal and never translated or removed.',
        known_limitation='English diagnostic suffix and original formatter artifact remain. Needs human review, not distribution. Null-actor fixture is not actual NPC visibility or actor-specific layout.',
        new_wording=False,new_engine_or_DB_changes=False,release_eligible=False)
FIELDS=context()['fields']

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    s=sources()[r['key']]['source_text'];t=r['text'];assert r['source_text']==s and t and t==unicodedata.normalize('NFC',t)
    markers=re.findall(r'\*[^*]*\*',s);assert len(markers)==1 and markers[0] in ['*Bug This if You See It*','*BUG THIS*','*BUG ME*'] and s.endswith(markers[0]) and t.endswith(markers[0])
    assert re.findall(r'\*[^*]*\*',t)==markers and s.count('*')==t.count('*')==2 and s.count('*B')==t.count('*B')==1
    tags=re.findall(r'\[[^\]]+\]',s);assert len(tags)<=1 and all(re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',v) for v in tags)
    assert re.findall(r'\[[^\]]+\]',t)==tags
    if tags:assert s.startswith(tags[0]) and t.startswith(tags[0])
    body=t[len(tags[0]) if tags else 0:-len(markers[0])]
    assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',s)==re.findall(r'\r\n+',t) and t.endswith('\r\n'+markers[0])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    data=encoder(t,book).encode('utf8');assert decoder(data.decode('utf8'),book)==t and len(data)<=65535
    check_template(t,'NPC706FC cap2048; exact original marker/effects preserved, no literal remap')
    return data

def select():
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256'];cfg=json.loads(cfgpath.read_text(encoding='utf8'))
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};byid={e['id']:e for e in es};ds=decisions();assert len(ds)==4304
    src=sources();rows={k:dict(key=k,source_text=src[k]['source_text'],text=t,control_policy=POLICY) for k,t in DRAFTS.items()}
    for r in rows.values():validate(r,pipeline.BOOK,encode_unicode,decode_unicode)
    sample=rows[2309];negative=[]
    for label,change in [('wrong_source',dict(source_text='wrong')),('alias_scope',dict(key=2334)),('marker_removed',dict(text=DRAFTS[2309].split('*')[0])),('marker_translated',dict(text=DRAFTS[2309].split('*')[0]+'[버그 제보]')),('case_changed',dict(text=DRAFTS[2309].replace('*BUG','*bug'))),('extra_macro',dict(text='*B'+DRAFTS[2309])),('portrait_removed',dict(text=DRAFTS[2309].replace('[i_PI_BronMorris]',''))),('page_added',dict(text=DRAFTS[2309]+'[p]')),('paragraph_removed',dict(text=DRAFTS[2309].replace('\r\n',''))),('NUL',dict(text=DRAFTS[2309]+'\0'))]:
        try:validate(dict(sample,**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261022_before_npc_marker_preserve';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for k,r in rows.items():
        e=byid[src[k]['id']];old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==DRAFTS[k]
        did=f'development_{NAME}:trans:{k}';records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact NPC-only table13 refs; complete original diagnostic marker and formatter effects preserved'),
            rationale='Known source*B formatter path is preserved byte-for-byte, not treated as literal. Existing individual wording unchanged. English debug suffix and source quirk explicitly retained for development only.',
            semantic_impact='Source diagnostic text, dynamic substitution and possible formatter side effects retained. Names/voice human review pending; no natural NPC or complete layout claim.',state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    target={d['source_id'] for d in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in target)
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4322 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_18_UNCHANGED_NPC_ONLY_DRAFTS_DEVELOPMENT_SELECTED_ORIGINAL_MACRO_EFFECTS_PRESERVED',authored=3973,selected=3524,working_unselected=449,decision_history=4322,new_authored=0,new_selected=18,negative_cases=negative,
        previous_wording_and_refs_unchanged=True,original_English_diagnostic_suffixes_preserved=True,source_asterisk_literal_remap=False,actual_NPC_runtime_pending=True,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='select':select()
    else:pipeline.audit(SPEC,__import__('npc_marker_preserve_20261022'),DRAFTS,{})

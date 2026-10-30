"""Select unchanged25 existing journal thought drafts after identifying their consumer."""
import argparse,copy,json,struct,unicodedata
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from entry_thought_drafts_20261020 import DRAFTS
from unicode_codec042 import encode_unicode,decode_unicode
from book_role_compat_20261024 import CONFIG as PARENT_CONFIG,derive_compatible

NAME='mode3_journal_20261024';CONFIG=f'development_{NAME}.json';BASE=ROOT/'workspace/translation'
POLICY='mode3_existing_thoughts_preacceptance_Book_context24_v1'

def rows():
    previous=json.loads((BASE/'authored/entry_thoughts_20261020.json').read_text(encoding='utf-8'))['drafts']
    assert len(previous)==25 and {r['key'] for r in previous}==set(DRAFTS)
    for r in previous:
        assert r['text']==DRAFTS[r['key']] and not any(c in r['source_text']+r['text'] for c in '\0\r\n\t[]{}$')
        assert r['text']==unicodedata.normalize('NFC',r['text'])
        book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};assert decode_unicode(encode_unicode(r['text'],book),book)==r['text']
    return [dict(key=r['key'],source_text=r['source_text'],text=r['text'],control_policy=POLICY) for r in previous]

def derive_mode3(cfg):
    assert set(cfg)=={'schema_version','policy','parent_config','parent_config_sha256','trans_overrides','consumer_evidence','consumer_evidence_sha256'}
    assert cfg['schema_version']==11 and cfg['policy']=='development_poc_non_distributable' and cfg['parent_config']==PARENT_CONFIG
    assert cfg['trans_overrides']==rows()
    evidence=ROOT/cfg['consumer_evidence'];assert digest(evidence.read_bytes())==cfg['consumer_evidence_sha256']
    proof=json.loads(evidence.read_text(encoding='utf-8'));assert proof['status']=='PASS_SOURCE_MODE3_PREACCEPTANCE_BOOK_GETTER_DRAW_AND_REENTRY'
    pp=ROOT/'config'/PARENT_CONFIG;assert digest(pp.read_bytes())==cfg['parent_config_sha256']
    plan,outputs=derive_compatible(json.loads(pp.read_text(encoding='utf-8')));plan=copy.deepcopy(plan);outputs=dict(outputs)
    prefix='PSP_GAME/USRDIR/locale/';directory=outputs[prefix+'en_us_dir.dat'];trans=outputs[prefix+'en_us_trans.dat']
    rr=[struct.unpack_from('<IIIHHHH',directory,i) for i in range(0,len(directory),20)];overrides={r['key']:r for r in rows()}
    newtrans=bytearray();newrows=[];source=json.loads((BASE/'authored/entry_thoughts_20261020.json').read_text(encoding='utf-8'))['drafts'];refs={r['key']:r['reference'] for r in source}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    for row in rr:
        key,ep,tp,el,tl,flag,res=row;raw=trans[tp:tp+tl]
        if key in overrides:
            r=overrides[key];assert raw==r['source_text'].encode('utf-8') and struct.unpack_from('<I',db,refs[key]['offset'])[0]==key
            raw=r['text'].encode('utf-8')
        newrows.append((key,ep,len(newtrans),el,len(raw),flag,res));newtrans.extend(raw)
    assert set(overrides)<{r[0] for r in rr} and len(rr)==860
    changes={prefix+'en_us_dir.dat':b''.join(struct.pack('<IIIHHHH',*r) for r in newrows),prefix+'en_us_trans.dat':bytes(newtrans)}
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw
        plan['writes'].append(dict(owner='Compose existing25 mode3 journal drafts with inherited role split',path=path,offset=0,size=len(raw),source_size=len(original),
            expected_sha256=digest(original),final_sha256=digest(raw),derivation='Source parent recipe plus25 exact existing unmodified drafts. Preserve all other860-record payloads and all original English fields.'))
    for old,new in zip(rr,newrows):
        k,ep,tp,el,tl,flag,res=new;assert (k,ep,el,flag,res)==(old[0],old[1],old[3],old[5],old[6])
        actual=newtrans[tp:tp+tl]
        assert actual==(overrides[k]['text'].encode('utf-8') if k in overrides else trans[old[2]:old[2]+old[4]])
    plan['writes'].sort(key=lambda r:(r['path'],r['offset']));plan['diagnostic_input']=cfg
    plan['mode3_journal']=dict(keys=sorted(overrides),original_table14_field8_refs_preserved=True,original_phase_or_condition_code_preserved=True,
        context24_preacceptance_journal_consumer_evidence=cfg['consumer_evidence'],prior_wording_unchanged=True,new_original_selected=25,
        selected_original_total=3565,held_original_total=408,derived_Book_roles_inherited=2)
    plan['font']['scope']='Development3565 selected original units and2 derived Book roles. Mode3 journal25 uses exact existing drafts; final human review pending.'
    return plan,outputs

def select():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    source=ROOT/'qa/reports/mode3_journal_source_20261024_runtime.json';proof=json.loads(source.read_text(encoding='utf-8'))
    assert proof['status']=='PASS_SOURCE_MODE3_PREACCEPTANCE_BOOK_GETTER_DRAW_AND_REENTRY'
    es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4353
    current=json.loads((ROOT/'qa/ssot/20261024_book_role_compat_checkpoint/manifest.json').read_text(encoding='utf-8'))
    assert digest((BASE/'entries.jsonl').read_bytes())==current['entries_sha256']
    pp=ROOT/'config'/PARENT_CONFIG;assert digest(pp.read_bytes())==current['config_sha256']
    snap=ROOT/'qa/ssot/20261024_before_mode3_journal';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',pp]:protected_write(snap/p.name,p.read_text(encoding='utf-8'))
    author=BASE/'authored/entry_thoughts_20261020.json';auth=json.loads(author.read_text(encoding='utf-8'))['drafts'];before={e['id']:serialized([e]) for e in es};records=[]
    for i,r in enumerate(auth):
        e=next(e for e in es if e['id']==r['source_id']);old=e['current_working_decision']
        assert not e['development_diagnostic_selection'] and resolve(ds[old])==r['text'] and r['text']==DRAFTS[r['key']]
        did=f'development_{NAME}:trans:{r["key"]}'
        records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
            wording_ref=dict(path=author.relative_to(ROOT).as_posix(),sha256=digest(author.read_bytes()),json_pointer=f'/drafts/{i}/text'),
            broader_decision_id=old,applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact original table14field8 key; Book phase0/context24 consumer, no phase code modification'),
            rationale='Previously held only for unresolved display consumer. Source Book getter/draw/reentry now verified; exact existing proposal selected without prose changes.',
            semantic_impact='Existing protagonist journal wording and quest context retained. Natural quest progression and final human wording review remain separate.',
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    targets={r['source_id'] for r in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in targets)
    cfg=dict(schema_version=11,policy='development_poc_non_distributable',parent_config=PARENT_CONFIG,parent_config_sha256=digest(pp.read_bytes()),
        trans_overrides=rows(),consumer_evidence=source.relative_to(ROOT).as_posix(),consumer_evidence_sha256=digest(source.read_bytes()))
    protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf-8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4378 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='SELECTED25_UNCHANGED_EXISTING_MODE3_JOURNAL_DRAFTS_NATIVE_KOREAN_PENDING',authored=3973,selected=3565,held=408,
        derived_Book_roles=2,decision_history=4378,new_prose=0,keys=sorted(DRAFTS),human_wording_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);a=p.parse_args();select()

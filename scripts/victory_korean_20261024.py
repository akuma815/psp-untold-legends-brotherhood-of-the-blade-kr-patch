"""Compose one unchanged existing victory-journal draft into source-derived schema12."""
import argparse,copy,json,struct,unicodedata
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from mode3_korean_20261024 import CONFIG as PARENT_CONFIG,derive_mode3
from pending_story_drafts_20261020 import DRAFTS

NAME='victory_journal_20261024';CONFIG=f'development_{NAME}.json';BASE=ROOT/'workspace/translation'
POLICY='direct3991_Book_first_type1_history_quest28_flag0_v1'
AUTHOR=BASE/'authored/pending_story_20261020.json'

def row():
    r=next(r for r in json.loads(AUTHOR.read_text(encoding='utf-8'))['drafts'] if r['key']==3991)
    assert r['text']==DRAFTS[3991] and not any(c in r['source_text']+r['text'] for c in '\r\n[]{}$\0\t')
    assert r['text']==unicodedata.normalize('NFC',r['text']) and len(r['text'].encode('utf-16le'))//2+1<2048
    return dict(key=3991,source_text=r['source_text'],text=r['text'],control_policy=POLICY)

def derive_victory(cfg):
    assert set(cfg)=={'schema_version','policy','parent_config','parent_config_sha256','trans_overrides','consumer_evidence','consumer_evidence_sha256'}
    assert cfg['schema_version']==12 and cfg['policy']=='development_poc_non_distributable' and cfg['parent_config']==PARENT_CONFIG
    assert cfg['trans_overrides']==[row()]
    proof=ROOT/cfg['consumer_evidence'];assert digest(proof.read_bytes())==cfg['consumer_evidence_sha256']
    assert json.loads(proof.read_text(encoding='utf-8'))['status']=='PASS_SOURCE_DIRECT3991_VICTORY_JOURNAL_DECODER_DRAW_REENTRY'
    pp=ROOT/'config'/PARENT_CONFIG;assert digest(pp.read_bytes())==cfg['parent_config_sha256']
    plan,outputs=derive_mode3(json.loads(pp.read_text(encoding='utf-8')));plan=copy.deepcopy(plan);outputs=dict(outputs)
    prefix='PSP_GAME/USRDIR/locale/';directory=outputs[prefix+'en_us_dir.dat'];trans=outputs[prefix+'en_us_trans.dat']
    rr=[struct.unpack_from('<IIIHHHH',directory,i) for i in range(0,len(directory),20)];newtrans=bytearray();newrows=[];r=row();hits=0
    for old in rr:
        key,ep,tp,el,tl,flag,res=old;raw=trans[tp:tp+tl]
        if key==3991:
            assert raw==r['source_text'].encode('utf-8');raw=r['text'].encode('utf-8');hits+=1
        newrows.append((key,ep,len(newtrans),el,len(raw),flag,res));newtrans.extend(raw)
    assert hits==1 and len(rr)==860
    changes={prefix+'en_us_dir.dat':b''.join(struct.pack('<IIIHHHH',*r) for r in newrows),prefix+'en_us_trans.dat':bytes(newtrans)}
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw
        plan['writes'].append(dict(owner='Compose existing victory-journal3991 with inherited mode3 and Book split',path=path,offset=0,size=len(raw),source_size=len(original),
            expected_sha256=digest(original),final_sha256=digest(raw),derivation='Source parent recipe plus one exact existing draft; all other859 record payloads, original keys/English fields and code/history logic preserved.'))
    for old,new in zip(rr,newrows):
        k,ep,tp,el,tl,flag,res=new;assert (k,ep,el,flag,res)==(old[0],old[1],old[3],old[5],old[6])
        assert newtrans[tp:tp+tl]==(r['text'].encode('utf-8') if k==3991 else trans[old[2]:old[2]+old[4]])
    plan['writes'].sort(key=lambda r:(r['path'],r['offset']));plan['diagnostic_input']=cfg
    plan['victory_journal']=dict(key=3991,original_direct_call_and_history_code_preserved=True,
        consumer_evidence=cfg['consumer_evidence'],prior_wording_unchanged=True,new_original_selected=1,
        selected_original_total=3566,held_original_total=407,derived_Book_roles_inherited=2)
    plan['font']['scope']='Development3566 selected original units and2 derived Book roles. Direct victory journal3991 uses exact existing draft; human review pending.'
    return plan,outputs

def select():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    evidence=ROOT/'qa/reports/victory_journal_source_20261024_runtime.json';proof=json.loads(evidence.read_text(encoding='utf-8'))
    assert proof['status']=='PASS_SOURCE_DIRECT3991_VICTORY_JOURNAL_DECODER_DRAW_REENTRY'
    manifest=json.loads((ROOT/'qa/ssot/20261024_mode3_journal_checkpoint/manifest.json').read_text(encoding='utf-8'))
    assert digest((BASE/'entries.jsonl').read_bytes())==manifest['entries_sha256']
    es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4378
    r=row();e=next(e for e in es if e['id']=='ULKS46015-v1.01:en_us/trans:3991');old=e['current_working_decision']
    assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==r['text']
    snapshot=ROOT/'qa/ssot/20261024_before_victory_journal';snapshot.mkdir(parents=True,exist_ok=True)
    pp=ROOT/'config'/PARENT_CONFIG;assert digest(pp.read_bytes())==manifest['config_sha256']
    for path in [BASE/'entries.jsonl',BASE/'terminology.json',pp,ROOT/'docs/HANDOFF.md']:
        protected_write(snapshot/path.name,path.read_text(encoding='utf-8'))
    before={x['id']:serialized([x]) for x in es};did=f'development_{NAME}:trans:3991'
    authored=json.loads(AUTHOR.read_text(encoding='utf-8'))['drafts'];index=next(i for i,x in enumerate(authored) if x['key']==3991)
    record=dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=AUTHOR.relative_to(ROOT).as_posix(),sha256=digest(AUTHOR.read_bytes()),json_pointer=f'/drafts/{index}/text'),
        broader_decision_id=old,applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact original trans3991 payload; original direct call and history predicates unchanged'),
        rationale='Direct3991 journal consumer identified and source decoder/draw/reentry verified. Select existing full draft without prose transformation.',
        semantic_impact='Protagonist victory journal retained. Bounded RAM history fixture does not establish natural ending; final human wording review remains pending.',
        state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None)
    e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    assert all(serialized([x])==before[x['id']] for x in es if x['id']!=e['id'])
    cfg=dict(schema_version=12,policy='development_poc_non_distributable',parent_config=PARENT_CONFIG,parent_config_sha256=digest(pp.read_bytes()),
        trans_overrides=[r],consumer_evidence=evidence.relative_to(ROOT).as_posix(),consumer_evidence_sha256=digest(evidence.read_bytes()))
    protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized([record]))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf-8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4379 and (BASE/'terminology.json').read_bytes()==(snapshot/'terminology.json').read_bytes()
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',dict(status='SELECTED_ONE_EXISTING_DRAFT_KOREAN_RUNTIME_PENDING',authored=3973,selected=3566,held=407,derived_Book_roles=2,
        decision_history=4379,key=3991,new_prose=0,exact_existing_wording_preserved=True,release_eligible=False))
    print('Selected existing3991 draft unchanged;3566 selected,407 held,4379 decisions.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);p.parse_args();select()

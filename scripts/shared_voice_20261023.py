"""Single shared3548 rewritten in plain style as requested; original two bindings kept."""
import argparse,json,struct,re
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from late_dialogue_policy_20261020 import validate_draft
import quest_batch_pipeline as pipeline

KEY=3548;NAME='shared_voice_20261023';POLICY='NPC3548_user_plain_shared_voice_original_two_refs_portrait_v1'
BASE=ROOT/'workspace/translation';FIELDS={KEY:[(13,4,132),(13,7,132)]}
DRAFTS={KEY:'[i_PI_SabineFirehand]우리 운명이 불확실했던 가장 어두운 시간에, 그곳에서 나란히 싸울 수 있었다면 좋았을 텐데...\r\n\r\n하지만 그것은 내 운명이 아니었다. 앞선 누구도 이루지 못한 승리를 거두고 우리의 영광스러운 미래를 굳건히 하는 일은 오직 수호자만의 운명이었다.'}
REVIEW=ROOT/'qa/reports/shared3548_voice_review_20261023.json';CHOICE=ROOT/'qa/reports/shared3548_plain_style_choice_20261023.json'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='praetox_variants_20261023',prior_config='development_praetox_variants_20261023.json',
    prior_config_sha256='122e27d6ef3476f223b0652e265cc80ed29e0bb4e8d1a28033a5dd82b1de5e3b',
    prior_artifact_sha256='03d20c07708623be8d4a96dc8e76cdeb7d1d698d18cf4c77666050caa2c7b969',new_authored_count=0)

@lru_cache(maxsize=1)
def sources():
    s=next(s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==KEY)
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()
    assert digest(raw[s['offset']:s['offset']+s['byte_length']])==s['source_sha256']
    return {KEY:s}

def context():
    review=json.loads(REVIEW.read_text(encoding='utf-8'));choice=json.loads(CHOICE.read_text(encoding='utf-8'))
    assert choice['user_answer']=='이 문장만 두 인물의 성격에 크게 벗어나지 않게 평어체로 번역할 순 없을까?'
    assert choice['scope']=='3548_only_plain_style_preserve_original_shared_references_and_portrait'
    assert choice['review_sha256']==digest(REVIEW.read_bytes())
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,13*8);assert (off,n)==(336020,18)
    for owner in review['owners']:
        at=off+owner['table13_row']*260
        assert db[at:at+260].hex()==owner['table13_complete_hex'] and struct.unpack_from('<I',db,at+132)[0]==KEY
    from translation_scope import collect
    rows,_=collect();refs=next(r['typed_references'] for r in rows if r['bank']=='trans' and r['key']==KEY)
    assert [(r['table'],r['row'],r['field']) for r in refs]==FIELDS[KEY]
    return dict(fields=FIELDS,owners=review['owners'],style_choice=choice,
                choice_sha256=digest(CHOICE.read_bytes()),original_key_and_two_refs_preserved=True,
                original_portrait_preserved=True,natural_speaker_or_phase_proven=False,full_translation_or_release_approval=False)

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==KEY and r['control_policy']==POLICY
    assert r['source_text']==sources()[KEY]['source_text'] and r['text']==DRAFTS[KEY]
    assert '당신' not in r['text'] and '자네' not in r['text'] and '수호자만의 운명이었다.' in r['text']
    context()
    return validate_draft(KEY,r['text'],book,encoder,decoder)

def select():
    review=json.loads(REVIEW.read_text(encoding='utf-8'));es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4348
    assert digest((BASE/'entries.jsonl').read_bytes())==review['entries_sha256']
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256']
    assert digest((ROOT/f"workspace/runtime/{SPEC['prior_name']}/artifact.json").read_bytes())==SPEC['prior_artifact_sha256']
    cfg=json.loads(cfgpath.read_text(encoding='utf-8'));s=sources()[KEY];e=next(e for e in es if e['id']==s['id'])
    old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==review['existing_draft']
    assert KEY not in {x['key'] for x in cfg['trans_overrides']}
    choice=dict(status='USER_REQUESTED_SINGLE_SHARED_PLAIN_STYLE_REVISION',authority='user',date_local='2026-10-23',
        user_answer='이 문장만 두 인물의 성격에 크게 벗어나지 않게 평어체로 번역할 순 없을까?',
        scope='3548_only_plain_style_preserve_original_shared_references_and_portrait',
        review_path=REVIEW.relative_to(ROOT).as_posix(),review_sha256=digest(REVIEW.read_bytes()),
        prior_polite_proposal_not_approved=True,agent_authored_plain_revision=DRAFTS[KEY],
        common_address='수호자: established player role instead of speaker-dependent 당신/자네',
        exact_wording_human_approval=False,style_direction_human_selected=True,full_translation_or_release_approval=False)
    protected_write(CHOICE,json.dumps(choice,ensure_ascii=False,indent=2)+'\n')
    row=dict(key=KEY,source_text=s['source_text'],text=DRAFTS[KEY],control_policy=POLICY);validate(row,pipeline.BOOK,encode_unicode,decode_unicode)
    negative=[]
    for label,mut in [('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3544)),
        ('old_polite_not_selected',dict(text=review['existing_draft'])),('portrait_lost',dict(text=DRAFTS[KEY].replace('[i_PI_SabineFirehand]',''))),
        ('new_page',dict(text=DRAFTS[KEY]+'[p]')),('NUL',dict(text=DRAFTS[KEY]+'\0')),
        ('new_variable',dict(text=DRAFTS[KEY]+'$a')),('overflow',dict(text=DRAFTS[KEY]+'가'*2048))]:
        try:validate(dict(row,**mut),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261023_before_shared_voice';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf-8'))
    protected_write(snap/'manifest.json',json.dumps(dict(entries_sha256=review['entries_sha256'],config_sha256=SPEC['prior_config_sha256'],artifact_sha256=SPEC['prior_artifact_sha256'],terminology_sha256=digest((BASE/'terminology.json').read_bytes())),indent=2)+'\n')
    author=BASE/f'authored/{NAME}.json';protected_write(author,json.dumps(dict(policy='individual_manual_development_revision_per_user_plain_style_request',drafts=[dict(**row,before=review['existing_draft'],references=FIELDS[KEY],human_reviewed=False)]),ensure_ascii=False,indent=2)+'\n')
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    before={x['id']:serialized([x]) for x in es};did=f'development_{NAME}:trans:{KEY}'
    d=dict(id=did,source_id=s['id'],source_sha256=s['source_sha256'],wording_ref=dict(path=author.relative_to(ROOT).as_posix(),sha256=digest(author.read_bytes()),json_pointer='/drafts/0/text'),broader_decision_id=old,
        applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Only shared3548; original table13row4/7field132 and Sabine portrait retained'),
        rationale='User requested this one sentence in plain style compatible with both characters; manually rewritten complete entry. No automatic prose rule or other-key change.',
        semantic_impact='Speaker-dependent polite/hage address removed in this one shared entry; player role used for you. Original shared-source/portrait inconsistency retained by scope.',
        human_style_choice_ref=dict(path=CHOICE.relative_to(ROOT).as_posix(),sha256=digest(CHOICE.read_bytes())),
        state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None)
    cfg['trans_overrides'].append(row);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    assert all(serialized([x])==before[x['id']] for x in es if x['id']!=s['id'])
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized([d]))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf-8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4349 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    chars=set();final_decisions=decisions()
    for x in es:
        if x['state']=='untranslated':continue
        latest=x['development_diagnostic_selection'] or x.get('current_working_decision') or x['decision_ids'][-1]
        chars.update(c for c in resolve(final_decisions[latest]) if 0xac00<=ord(c)<=0xd7a3)
    report=dict(status='PASS_SHARED3548_USER_REQUESTED_PLAIN_REVISION_DEVELOPMENT_SELECTED',authored=3973,selected=3538,working_unselected=435,decision_history=4349,
        new_authored_source_entries=0,new_selected=1,negative_cases=negative,modern_Hangul_unique_demand=len(chars),
        old_authored_files_and_other_entries_unchanged=True,approved_terminology_decisions=14,exact_wording_human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

def cold_prepare(q):
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    art=ROOT/f'workspace/runtime/{NAME}/artifact.json';a=json.loads(art.read_text(encoding='utf-8'));assert len(a['files'])==80
    for rel,m in a['files'].items():
        raw=(art.parent/'disc'/rel).read_bytes();assert len(raw)==m['size'] and digest(raw)==m['sha256']
    print(json.dumps(dict(artifact_sha256=digest(art.read_bytes()))))

def recover_report():
    """Read-only validation after a post-write reporting loop was interrupted."""
    snap=ROOT/'qa/ssot/20261023_before_shared_voice';before=lines(snap/'entries.jsonl');es=lines(BASE/'entries.jsonl')
    ds=decisions();assert len(ds)==4349 and len(es)==len(before)==3973
    s=sources()[KEY];did=f'development_{NAME}:trans:{KEY}'
    for old,new in zip(before,es):
        if old['id']!=s['id']:assert old==new
        else:
            expected=dict(old,state='needs_human_review',context_id=NAME,development_diagnostic_selection=did,decision_ids=old['decision_ids']+[did])
            assert new==expected and resolve(ds[did])==DRAFTS[KEY] and resolve(ds[old['current_working_decision']])==json.loads(REVIEW.read_text(encoding='utf-8'))['existing_draft']
    cfg=json.loads((ROOT/'config'/SPEC['config']).read_text(encoding='utf-8'));prior=json.loads((snap/SPEC['prior_config']).read_text(encoding='utf-8'))
    row=dict(key=KEY,source_text=s['source_text'],text=DRAFTS[KEY],control_policy=POLICY)
    expected=json.loads(json.dumps(prior));expected['trans_overrides'].append(row);assert cfg==expected
    assert (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    validate(row,pipeline.BOOK,encode_unicode,decode_unicode)
    chars=set()
    for x in es:
        latest=x['development_diagnostic_selection'] or x.get('current_working_decision') or x['decision_ids'][-1]
        chars.update(c for c in resolve(ds[latest]) if 0xac00<=ord(c)<=0xd7a3)
    error=dict(status='POST_SELECTION_REPORTING_PERFORMANCE_ERROR_RECOVERED_WITHOUT_RESELECT',
        issue='Final character-demand report reparsed complete decision history once per3973 entries; reporting only, after selection writes and eight negative cases.',
        exact_owned_process_stopped=dict(pid=7320,start_local='2026-10-23 23:28:15.311',command='python.exe -B scripts/shared_voice_20261023.py select'),
        fix='Load complete decision history once; validate persisted entries/config/wording against before snapshot; regenerate only report',
        selection_writer_reruns=0,extra_native_attempts=0,emulator_processes_affected=0)
    save_json(ROOT/'qa/reports/shared_voice_reporting_performance_error_20261023.json',error)
    report=dict(status='PASS_SHARED3548_USER_REQUESTED_PLAIN_REVISION_DEVELOPMENT_SELECTED',authored=3973,selected=3538,working_unselected=435,decision_history=4349,
        new_authored_source_entries=0,new_selected=1,negative_cases=['wrong_source','outside_scope','old_polite_not_selected','portrait_lost','new_page','NUL','new_variable','overflow'],
        modern_Hangul_unique_demand=len(chars),old_authored_files_and_other_entries_unchanged=True,approved_terminology_decisions=14,
        exact_wording_human_approval=False,post_write_report_recovered_against_before_snapshot=True,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

def cold_preflight(q):
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf-8'))
    cpu=read('before_cpu')['state'];ranges=read('before_ranges')['reads'];assert cpu['cpu.pc']==0x08804000+0x4f358
    t=DRAFTS[KEY];v=t.replace('\r',' ');clean=re.sub(r'\[i_[^]]+\]','',v)
    pre=dict(artifact_name=NAME,artifact_sha256=digest((ROOT/f'workspace/runtime/{NAME}/artifact.json').read_bytes()),kind='korean',cold_boot=True,
        other_artifact_state_imports=0,cpu=cpu,ranges=ranges,cases=[dict(key=KEY,text=t,expected=v,input_units=len(v)+1,
        clean_units=len(clean)+1,clean_hex=(clean+'\0').encode('utf-16le').hex(),images=1,p_markers=0)])
    protected_write(q/'preflight.json',json.dumps(pre,ensure_ascii=False,indent=2)+'\n');print(json.dumps(pre,ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit','cold-prepare','cold-preflight','recover-report']);p.add_argument('--q');a=p.parse_args()
    if a.action=='select':select()
    elif a.action=='audit':pipeline.audit(SPEC,__import__('shared_voice_20261023'),DRAFTS,{})
    elif a.action=='cold-prepare':cold_prepare(ROOT/a.q)
    elif a.action=='recover-report':recover_report()
    else:cold_preflight(ROOT/a.q)

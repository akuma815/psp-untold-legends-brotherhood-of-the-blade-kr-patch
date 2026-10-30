"""User-approved eleven exact prose fragments, source-derived schema25 overlay."""
import argparse,copy,json,shutil
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from optional_layout_preflight_20261030 import frozen_rows,rewrite,PARENT,ENTRIES,PREFIX
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
NAME='optional_layout_20261030';CONFIG='development_'+NAME+'.json'
BASE=ROOT/'workspace/translation'
PARENT_CONFIG='development_dialogue3541_20261026.json'
HUB='qa/reports/optional_layout11_review_20261030.json'
APPROVAL='workspace/translation/approvals/20261030_optional_layout11.json'
AUTHOR='workspace/translation/authored/optional_layout_20261030.json'
TERMS='2764534652f859271e620515543e6f45e2804a941497de1e9b166719c0b5ea9a'
ANSWER='11개 모두 제시한 범위로 반영'
QUESTION='["request_user_input_async","call_3ae525d772904478a7c92b0354f0519e",0]'
KEYS={3647,2320,2362,2377,2405,2407,3552,2561,2823,2919,2675}
def rd(path):return json.loads(path.read_text(encoding='utf8'))
def approved_rows():
    hub,rows=frozen_rows();assert hub==HUB and {r['key'] for r in rows}==KEYS
    a=rd(ROOT/APPROVAL);author=rd(ROOT/AUTHOR)
    assert a['answer']==ANSWER and a['question_item_id']==QUESTION and a['authority']=='user'
    assert a['hub_sha256']==digest((ROOT/HUB).read_bytes()) and a['pairs']==rows and not a['full_wording_layout_support_or_release_approval']
    assert author['records']==[dict(r,text=r['after']) for r in rows]
    return a,rows
def configuration():
    a,rows=approved_rows()
    return dict(schema_version=25,policy='development_poc_non_distributable',parent_config=PARENT_CONFIG,parent_config_sha256=digest((ROOT/'config'/PARENT_CONFIG).read_bytes()),parent_artifact='workspace/runtime/dialogue3541_20261026/artifact.json',parent_artifact_sha256=PARENT,hub=HUB,hub_sha256=digest((ROOT/HUB).read_bytes()),approval=APPROVAL,approval_sha256=digest((ROOT/APPROVAL).read_bytes()),author=AUTHOR,author_sha256=digest((ROOT/AUTHOR).read_bytes()),exact_trans_keys=sorted(KEYS),scope='Only11 exact user-chosen prose fragment pairs;all other body/paragraphs/portraits/controls/numbers/refs/game behavior retained. No wholewording/layout/support/releaseapproval.',release_eligible=False)
def select():
    snap=ROOT/'qa/ssot/20261030_before_optional_layout25';assert not snap.exists() and not (ROOT/APPROVAL).exists() and not (ROOT/AUTHOR).exists()
    hub,rows=frozen_rows();assert {r['key'] for r in rows}==KEYS
    entries=BASE/'entries.jsonl';oldraw=entries.read_bytes();terms=BASE/'terminology.json'
    assert digest(oldraw)==ENTRIES and digest(terms.read_bytes())==TERMS and digest((ROOT/'workspace/runtime/dialogue3541_20261026/artifact.json').read_bytes())==PARENT
    es=lines(entries);oldlines=oldraw.splitlines(keepends=True);by={e['id']:e for e in es};ds=decisions();assert len(es)==3973 and len(ds)==4426
    for r in rows:
        e=by[r['id']];assert e['source_sha256']==r['source_sha256'] and e['development_diagnostic_selection']==r['previous_decision']
        assert resolve(ds[r['previous_decision']])==r['before'] and e['release_selection'] is None and not e['distribution_eligible']
    files=['workspace/translation/entries.jsonl','workspace/translation/terminology.json','config/'+PARENT_CONFIG,'workspace/runtime/dialogue3541_20261026/artifact.json','workspace/runtime/dialogue3541_20261026/expected_writes.json','scripts/build_font_folder.py','scripts/book_role_runtime_20261024.py','scripts/manual_play_20261024.py','docs/HANDOFF.md','docs/HANDOFF_2026-10-30.md','AGENTS.md','README.md','qa/reports/continuation_queue_20261024.json',HUB,'qa/reports/optional_layout_preflight_20261030.json']
    for rel in files:
        dest=snap/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest);assert dest.read_bytes()==(ROOT/rel).read_bytes()
    save_json(snap/'manifest.json',dict(status='BEFORE_USER_APPROVED11_SCHEMA25_SELECTION',pins={p:digest((ROOT/p).read_bytes()) for p in files},before_entries_sha256=ENTRIES,parent24_all80_preserved=True))
    a=dict(status='USER_APPROVED_EXACT11_FRAGMENT_EDITS',authority='user',date_local='2026-10-30',question_item_id=QUESTION,answer=ANSWER,hub=HUB,hub_sha256=digest((ROOT/HUB).read_bytes()),pairs=rows,entries_before_sha256=ENTRIES,terminology_before_sha256=TERMS,parent24_artifact_sha256=PARENT,full_wording_layout_support_or_release_approval=False,exclusions=['Portraits,paragraphs,controls,numbers,references,otherprose','Original title-map/credits/name-entry scope','Allheld404 andother6localcandidates','Fullwording/layout/support/releaseapproval'])
    protected_write(ROOT/APPROVAL,json.dumps(a,ensure_ascii=False,indent=2)+'\n')
    protected_write(ROOT/AUTHOR,json.dumps(dict(policy='Only the eleven frozen exact manually authored user-selected pairs',records=[dict(r,text=r['after']) for r in rows]),ensure_ascii=False,indent=2)+'\n')
    added=[]
    for i,r in enumerate(rows):
        e=by[r['id']];did=f'{NAME}:trans:{r["key"]}'
        added.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=AUTHOR,sha256=digest((ROOT/AUTHOR).read_bytes()),json_pointer=f'/records/{i}/text'),broader_decision_id=r['previous_decision'],applicability=dict(revision='ULKS46015-v1.01',context=NAME,scope='Only exact declared11 fragments'),rationale='User selected all11 frozen proposals;reduce isolated finalfragments preserving source meaning andvoice.',semantic_impact='Exactdeclaredprosefragments only;otherbody/controls/numbers/refs preserved.',human_wording_choice_ref=dict(path=APPROVAL,sha256=digest((ROOT/APPROVAL).read_bytes())),state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        e['development_diagnostic_selection']=did;e['current_working_decision']=did;e['context_id']=NAME;e['decision_ids'].append(did)
    selected={r['id'] for r in rows};assert sum(bool(e['development_diagnostic_selection']) for e in es)==3569
    newlines=[serialized([e]).encode('utf8') if e['id'] in selected else raw for e,raw in zip(es,oldlines)]
    assert sum(a!=b for a,b in zip(newlines,oldlines))==11 and all(a==b for a,b,e in zip(newlines,oldlines,es) if e['id'] not in selected)
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(added));protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    temp=entries.with_name('entries.optional_layout25.pending');assert not temp.exists();temp.write_bytes(b''.join(newlines));temp.replace(entries)
    assert len(decisions())==4437 and digest(terms.read_bytes())==TERMS
    save_json(ROOT/'qa/reports/optional_layout25_20261030_selection.json',dict(status='PASS_USER_APPROVED11_SSOT_SELECTED_SCHEMA25_BUILD_RUNTIME_PENDING',original_entries=3973,selected=3569,held=404,derived=2,decisions=4437,modified_entries=11,other3962_raw_lines_identical=True,terms_unchanged=True,before_entries_sha256=ENTRIES,entries_sha256=digest(entries.read_bytes()),approval=APPROVAL,keys=sorted(KEYS),current_launcher_still24=True,release_eligible=False))
    qp=ROOT/'qa/reports/continuation_queue_20261024.json';q=rd(qp);q.update(status='APPROVED11_SELECTED_BUILD25_PENDING_LAUNCHER24_RETAINED',optional_wordings_pending=0,optional_wordings_applied_to_SSOT=11,optional11_applied=True,user_answer=ANSWER,approval=APPROVAL,current_launcher='dialogue3541_20261026',next_action='Build schema25 fromimmutable source;verify two locale files/11payloads/78parent files,then coldnew25 necessaryruntime41pages beforelauncher adoption. No old24stateimport,noISO.',work_continues=True);save_json(qp,q)
    main=ROOT/'docs/HANDOFF.md';dated=ROOT/'docs/HANDOFF_2026-10-30.md';assert main.read_bytes()==dated.read_bytes()
    text=main.read_text(encoding='utf8')+'\n\n## 사용자11개승인·SSOT선택반영/schema25빌드전\n\n사용자가“11개 모두 제시한 범위로 반영”을선택했다.정확전후·선택질문id·현재원문/원고/허브해시를승인원장에기록하고해당11원고선택만갱신했다.다른3962원고rawline/용어/제품24는같고3973원문·3569선택·404보류·파생2/결정4437이다.아직제품25빌드·실행전이므로기본실행은24를유지한다.다음immutable source schema25/2언어파일·11payload·다른78파일동일검증→새25coldboot/필요41쪽실제검증후채택.전체문안·지원범위·배포승인은아님/ISO0.\n'
    for p in [main,dated]:p.write_text(text,encoding='utf8',newline='\n')
    notice='2026-10-30 사용자11개정확문안승인→SSOT11선택반영/3962rawline·용어동일/결정4437.제품schema25빌드·실행전/기본24유지.다음immutable source25빌드·2파일11payload/78동일→새25cold런타임41쪽검증/old24stateimport금지.원문3973선택3569보류404파생2·ISO0.HANDOFF=dated30. 아래미반영/대기는과거기록.\n\n'
    for name in ['AGENTS.md','README.md']:
        p=ROOT/name;p.write_text(notice+p.read_text(encoding='utf8'),encoding='utf8',newline='\n')
    print('SELECTED approved11;SSOT11/other3962bytesexact;decisions4437;schema25buildpending;launcher24retained.')
def derive_optional_layout(cfg):
    assert cfg==configuration();approval,rows=approved_rows();es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions()
    for r in rows:
        e=es[r['id']];did=f'{NAME}:trans:{r["key"]}'
        assert did in e['decision_ids'] and resolve(ds[did])==r['after'] and e['release_selection'] is None and not e['distribution_eligible']
        if e['development_diagnostic_selection']!=did:
            from second_review_apply_20261030 import assert_descendant_selection
            assert_descendant_selection(e,r)
    from dialogue3541_20261026 import derive_dialogue3541
    parentcfg=rd(ROOT/'config'/PARENT_CONFIG);plan,outputs=derive_dialogue3541(parentcfg)
    parent=rd(ROOT/'workspace/runtime/dialogue3541_20261026/artifact.json');assert digest((ROOT/'workspace/runtime/dialogue3541_20261026/artifact.json').read_bytes())==PARENT
    for p,pin in plan['all_source_files'].items():
        raw=outputs.get(p);computed=dict(size=len(raw),sha256=digest(raw)) if raw is not None else dict(size=pin['size'],sha256=pin['sha256']);assert computed==parent['files'][p],('Parent24 reconstruction drift',p)
    plan=copy.deepcopy(plan);outputs=dict(outputs);previous=dict(outputs)
    newdir,newtrans=rewrite(outputs[PREFIX+'dir.dat'],outputs[PREFIX+'trans.dat'],rows);changes={PREFIX+'dir.dat':newdir,PREFIX+'trans.dat':newtrans}
    expected=rd(ROOT/'qa/reports/optional_layout_preflight_20261030.json');expected=next(x for x in expected['variants'] if x['choice']=='all11')
    assert {p:digest(b) for p,b in changes.items()}==expected['planned_file_sha256']
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for p,raw in changes.items():
        source=(ROOT/'extracted/disc'/p).read_bytes();outputs[p]=raw;plan['writes'].append(dict(owner='User-approved exact11 optionalprosefragments',path=p,offset=0,size=len(raw),source_size=len(source),expected_sha256=digest(source),final_sha256=digest(raw),derivation='Immutable source through pinnedparent24;rewrite exact11UTF8payloads only;recalculate860translationoffsets/lengths;preserveEnglish/flags/keys/order/allotherpayloads.'))
    assert {p for p in outputs if outputs[p]!=previous[p]}==set(changes)
    plan['writes'].sort(key=lambda x:(x['path'],x['offset']));plan['diagnostic_input']=cfg
    plan['approved_optional_layout11']=dict(approval=APPROVAL,keys=sorted(KEYS),parent24_all80_source_derived_match=True,parent_other78_files_identical=True,logical_payload_changes=11,binary_files_changed=2,prose_UTF8_delta=-218,fullwording_layout_support_release_approval=False,native_validation_pending=True,release_eligible=False)
    plan['font']['scope']='Same five fonts/code/WAD/DB andselected3569+derived2. Only11exactuserapprovedprosefragments;fullwording/layout/releaseapproval separate.'
    return plan,outputs
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('operation',choices=['select']);ap.parse_args();select()

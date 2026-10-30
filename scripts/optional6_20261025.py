"""User-approved exact six ability wording edits, layered over immutable schema22."""
import argparse,copy,json,re,shutil,struct,unicodedata
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write

NAME='optional6_20261025';CONFIG='development_'+NAME+'.json'
PARENT='development_title_original_20261025.json'
BASE=ROOT/'workspace/translation'
PACKET='workspace/translation/review/20261025_optional6_wording_review/packet.json'
APPROVAL='workspace/translation/approvals/20261025_optional6.json'
AUTHOR='workspace/translation/authored/optional6_20261025.json'
KEYS={3096,3104,3116,3122,3129,3131}
PREFIX='PSP_GAME/USRDIR/locale/en_us_'
BEFORE_ENTRIES='ad40660cc0c6c586d47a6cfb6b2e2a9099c4f4088959c6d35c7fad04bfd3b894'
TERMS='2764534652f859271e620515543e6f45e2804a941497de1e9b166719c0b5ea9a'
PARENT_ARTIFACT='8d2bd3a0e28e2c20a167fbce035c21ae3d3618f6512f9022424ec065a8a24c5a'

def frozen_rows():
    checkpoint=json.loads((ROOT/'qa/ssot/20261025_optional6_review_checkpoint/manifest.json').read_text(encoding='utf8'))
    raw=(ROOT/PACKET).read_bytes();assert digest(raw)==checkpoint['pins'][PACKET]
    packet=json.loads(raw);assert packet['entries_sha256']==BEFORE_ENTRIES and packet['terminology_sha256']==TERMS and packet['artifact_sha256']==PARENT_ARTIFACT
    inventory=json.loads((ROOT/packet['inventory']).read_text(encoding='utf8'));assert digest((ROOT/packet['inventory']).read_bytes())==packet['inventory_sha256']
    by={(r['bank'],r['key']):r for r in inventory['records']};rows=[]
    for p in packet['proposals']:
        r=by['trans',p['key']];assert r['wording']==p['before'] and r['source']==p['source'] and r['status']=='selected'
        assert not p['applied'] and not p['approved'] and p['after']!=p['before']
        assert '\0' not in p['after'] and unicodedata.normalize('NFC',p['after'])==p['after']
        assert re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\r\n',p['before'])==re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\r\n',p['after'])
        assert len(p['after'].encode('utf8'))+1<=5000 and len(p['after'].encode('utf-16le'))//2+1<=2048
        assert len(p['font_metric_checks'])==5 and all(x['all_proposed_characters_in_current_font'] and x['after_template_advance']<=x['before_template_advance'] for x in p['font_metric_checks'])
        if p['key'] in [3104,3116,3131]:
            old='모든 방어의 피해 경감량이 $1 증가합니다. 방어 중';new='막기로 받는 피해가 $1 더 감소합니다. 막기 중'
            assert p['before'].count(old)==1 and p['after']==p['before'].replace(old,new)
        elif p['key']==3129:assert p['before'].count('방어는')==1 and p['after']==p['before'].replace('방어는','막기는')
        elif p['key']==3122:assert p['after']==p['before'].replace('피해를 줄 기회가 있습니다.','피해를 줄 수 있습니다.')
        elif p['key']==3096:assert p['after']=='적 중 $1를 $2초 동안 아군으로 바꾸어 싸우게 합니다.'
        rows.append(dict(id=r['id'],bank='trans',key=p['key'],title=p['title'],source_sha256=r['source_sha256'],source=r['source'],before=p['before'],after=p['after'],previous_decision=r['decision']))
    assert {r['key'] for r in rows}==KEYS and len(rows)==6
    return packet,rows

def approved_rows():
    p,rows=frozen_rows();a=json.loads((ROOT/APPROVAL).read_text(encoding='utf8'))
    assert a['answer']=='6개 모두 제안대로 반영 (권장)' and a['packet_sha256']==digest((ROOT/PACKET).read_bytes())
    assert a['pairs']==rows and not a['full_wording_layout_or_release_approval']
    authored=json.loads((ROOT/AUTHOR).read_text(encoding='utf8'));assert authored['records']==[dict(r,text=r['after']) for r in rows]
    return a,rows

def configuration():
    a,rows=approved_rows()
    return dict(schema_version=23,policy='development_poc_non_distributable',parent_config=PARENT,parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        parent_artifact='workspace/runtime/title_original_20261025/artifact.json',parent_artifact_sha256=PARENT_ARTIFACT,
        packet=PACKET,packet_sha256=digest((ROOT/PACKET).read_bytes()),approval=APPROVAL,approval_sha256=digest((ROOT/APPROVAL).read_bytes()),
        author=AUTHOR,author_sha256=digest((ROOT/AUTHOR).read_bytes()),exact_trans_keys=sorted(KEYS),
        scope='Only six frozen source/current/proposed pairs:four blocking-clarity andtwo grammar edits. Titles,variables,numbers,controls,effects,all other prose,original title-map and credits/name-entry decisions retained.',release_eligible=False)

def select():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    packet,rows=frozen_rows();entries=BASE/'entries.jsonl';terms=BASE/'terminology.json';oldraw=entries.read_bytes()
    assert digest(oldraw)==BEFORE_ENTRIES and digest(terms.read_bytes())==TERMS
    assert digest((ROOT/'workspace/runtime/title_original_20261025/artifact.json').read_bytes())==PARENT_ARTIFACT
    ds=decisions();assert len(ds)==4419;es=lines(entries);oldlines=oldraw.splitlines(keepends=True)
    assert len(oldlines)==len(es) and all(json.loads(raw)==e for raw,e in zip(oldlines,es))
    by={e['id']:e for e in es};before={e['id']:serialized([e]) for e in es}
    for r in rows:
        e=by[r['id']];assert e['source_sha256']==r['source_sha256'] and e['development_diagnostic_selection']==r['previous_decision']
        assert resolve(ds[r['previous_decision']])==r['before'] and e['release_selection'] is None and not e['distribution_eligible']
    snap=ROOT/'qa/ssot/20261025_before_optional6';assert not snap.exists()
    files=['workspace/translation/entries.jsonl','workspace/translation/terminology.json','config/'+PARENT,
        'workspace/runtime/title_original_20261025/artifact.json','workspace/runtime/title_original_20261025/expected_writes.json',
        'scripts/build_font_folder.py','scripts/book_role_runtime_20261024.py','scripts/manual_play_20261024.py',
        'docs/HANDOFF.md','docs/HANDOFF_2026-10-25.md','AGENTS.md','README.md','qa/reports/continuation_queue_20261024.json',PACKET]
    for n in files:
        target=snap/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,target);assert target.read_bytes()==(ROOT/n).read_bytes()
    save_json(snap/'manifest.json',dict(status='BEFORE_EXACT_APPROVED6',pins={n:digest((ROOT/n).read_bytes()) for n in files},source_parent22_preserved=True))
    approval=dict(status='USER_APPROVED_EXACT6_SCOPED_WORDING',authority='user',date_local='2026-10-25',question_item_id='["request_user_input_async","call_4159e79ac98e4bb6b2a3792496ca7a37",0]',
        answer='6개 모두 제안대로 반영 (권장)',packet=PACKET,packet_sha256=digest((ROOT/PACKET).read_bytes()),pairs=rows,
        entries_before_sha256=BEFORE_ENTRIES,terminology_before_sha256=TERMS,artifact_before_sha256=PARENT_ARTIFACT,
        approved_blocking_keys=[3104,3116,3129,3131],approved_grammar_keys=[3096,3122],
        exclusions=['Ability titles including 방어','Numbers,variable order,control tags,effects and definitions','All other text and label terminology','Title-map original scope','Whole wording/layout/release approval'],full_wording_layout_or_release_approval=False)
    protected_write(ROOT/APPROVAL,json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
    protected_write(ROOT/AUTHOR,json.dumps(dict(policy='Exact six user-selected frozen pairs;no corpus normalization',records=[dict(r,text=r['after']) for r in rows]),ensure_ascii=False,indent=2)+'\n')
    added=[]
    for i,r in enumerate(rows):
        e=by[r['id']];did=f'{NAME}:trans:{r["key"]}'
        added.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=AUTHOR,sha256=digest((ROOT/AUTHOR).read_bytes()),json_pointer=f'/records/{i}/text'),
            broader_decision_id=r['previous_decision'],applicability=dict(revision='ULKS46015-v1.01',context=NAME,scope='Only the exact frozen6 string and declared fragment edits'),
            rationale='User selected all six exact proposals;blocking clarity and grammar only.',semantic_impact='No mechanic/numeric/control changes or full wording/layout/release approval.',human_wording_choice_ref=dict(path=APPROVAL,sha256=digest((ROOT/APPROVAL).read_bytes())),
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        e['development_diagnostic_selection']=did;e['current_working_decision']=did;e['context_id']=NAME;e['decision_ids'].append(did)
    selected={r['id'] for r in rows};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in selected)
    assert len(es)==3973 and sum(bool(e['development_diagnostic_selection']) for e in es)==3569
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(added));protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    newlines=[serialized([e]).encode('utf8') if e['id'] in selected else raw for raw,e in zip(oldlines,es)]
    assert all(a==b for a,b,e in zip(oldlines,newlines,es) if e['id'] not in selected)
    tmp=entries.with_name(entries.name+'.optional6.pending');assert not tmp.exists();tmp.write_bytes(b''.join(newlines));tmp.replace(entries)
    assert len(decisions())==4425 and digest(terms.read_bytes())==TERMS
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',dict(status='PASS_EXACT_APPROVED6_SELECTED_BUILD_RUNTIME_PENDING',authored=3973,selected=3569,held=404,derived_Book=2,decisions=4425,
        modified_entries=6,other3967_entries_byte_equal=True,approved_label_decisions=19,terms_byte_equal=True,entries_sha256=digest(entries.read_bytes()),terminology_sha256=TERMS,approval=APPROVAL,release_eligible=False))
    queuepath=ROOT/'qa/reports/continuation_queue_20261024.json';queue=json.loads(queuepath.read_text(encoding='utf8'));queue.update(status='EXACT6_APPROVED_SELECTED_BUILD23_PENDING',pending_optional6=dict(answer_received=True,answer=approval['answer'],approval=APPROVAL,selection_completed=True,new_build_runtime_pending=True),deferred_optional6_approval_requested=True,deferred_optional6_prose_applied=True,next_action='Build source-derived schema23,verify only6trans logical payload differences/78parent files identical,then necessary original ability previews before launcher adoption. No ISO.')
    save_json(queuepath,queue)
    note='# 2026-10-25 승인6개 원고 반영 / schema23 빌드 전\n\n사용자가 준비한6개 모두 제안대로 반영을 선택했다. 정확 원문/현행/제안 packet에 승인 기록을 결합하고 해당6개 decision만 추가했다. 작성3973/선택3569/보류404/파생2 유지,결정4425이며 다른3967항목과 용어는 같다. 제목 방어·수치/변수/효과·타이틀 지도 원문 등 기존 결정은 유지한다. 원고 선택만 반영됐고 현재 실행 기본값은 검증된22다. 다음23 source 빌드와 해당 실제 표시를 검증한 후 채택한다. ISO/배포 승인이 아니다.\n'
    (ROOT/'docs/OPTIONAL6_APPLY_2026-10-25.md').write_text(note,encoding='utf8',newline='\n');old=(ROOT/'docs/HANDOFF.md').read_text(encoding='utf8')
    for n in ['docs/HANDOFF.md','docs/HANDOFF_2026-10-25.md']:(ROOT/n).write_text(note+'\n---\n\n'+old,encoding='utf8',newline='\n')
    print('SELECTED exact approved6,3973/3569/404+Book2,4425decisions,other3967/terms unchanged;schema23 build/runtime pending,launcher22 retained.')

def derive_optional6(cfg):
    assert cfg==configuration();approval,rows=approved_rows()
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    from title_original_20261025 import derive_original_title
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions()
    for r in rows:
        did=f'{NAME}:trans:{r["key"]}';e=es[r['id']]
        assert e['development_diagnostic_selection']==did and did in e['decision_ids'] and resolve(ds[did])==r['after']
        assert e['release_selection'] is None and not e['distribution_eligible'] and ds[did]['approval'] is None
    plan,outputs=derive_original_title(json.loads((ROOT/'config'/PARENT).read_text(encoding='utf8')))
    parent_artifact=json.loads((ROOT/'workspace/runtime/title_original_20261025/artifact.json').read_text(encoding='utf8'));assert digest((ROOT/'workspace/runtime/title_original_20261025/artifact.json').read_bytes())==PARENT_ARTIFACT
    for path,item in plan['all_source_files'].items():
        raw=outputs.get(path);expected=dict(size=len(raw),sha256=digest(raw)) if raw is not None else dict(size=item['size'],sha256=item['sha256'])
        assert expected==parent_artifact['files'][path],('Parent22 source reconstruction drift',path)
    plan=copy.deepcopy(plan);outputs=dict(outputs);parent=dict(outputs);overrides={r['key']:r for r in rows}
    olddir=outputs[PREFIX+'dir.dat'];oldtrans=outputs[PREFIX+'trans.dat'];directory=bytearray();trans=bytearray();changed=[];assert len(olddir)==860*20
    for at in range(0,len(olddir),20):
        key,ep,tp,el,tl,flag,res=struct.unpack_from('<IIIHHHH',olddir,at);payload=oldtrans[tp:tp+tl]
        if key in overrides:
            r=overrides[key];assert payload==r['before'].encode('utf8');payload=r['after'].encode('utf8');changed.append(key)
        assert len(payload)<65536;directory.extend(struct.pack('<IIIHHHH',key,ep,len(trans),el,len(payload),flag,res));trans.extend(payload)
    assert set(changed)==KEYS and len(changed)==6
    changes={PREFIX+'dir.dat':bytes(directory),PREFIX+'trans.dat':bytes(trans)}
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw
        plan['writes'].append(dict(owner='User-approved exact6 ability wording',path=path,offset=0,size=len(raw),source_size=len(original),expected_sha256=digest(original),final_sha256=digest(raw),derivation='Immutable source through schema22;exact6 trans payload changes only;all other payloads/English fields/flags/order retained;recalculate offsets/lengths.'))
    assert {p for p in outputs if outputs[p]!=parent[p]}==set(changes)
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['approved_optional6']=dict(approval=APPROVAL,trans_keys=sorted(KEYS),selected=3569,held=404,decisions=4425,parent22_all80_source_derived_match=True,parent_other78_files_unchanged=True,new_native_payload_validation_pending=True,release_eligible=False)
    plan['font']['scope']='Same selected3569+derivedBook2;exact approved6 blocking/grammar changes over schema22. All font/code/graphics/other prose preserved;full wording/layout/release review pending.'
    return plan,outputs

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);p.parse_args();select()

"""Schema26: exact user-selected chronology phrase and five Templar labels."""
import argparse,copy,json,re,shutil,struct,unicodedata
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve

NAME='second_review_apply_20261030'
CONFIG='development_'+NAME+'.json'
BASE=ROOT/'workspace/translation'
PACKET='workspace/translation/review/20261030_second_review25_choices/packet.json'
PARENT_CONFIG='development_optional_layout_20261030.json'
PARENT='39c2a18a28102c9ed4e95aa6dc7e9d2bb2ea32c2e95ab88cc466d890c0710c3d'
ENTRIES='f7894e7aea806531bb0e610e160de96bfaa9703c3e91751ffac03ef134d0aa55'
TERMS='2764534652f859271e620515543e6f45e2804a941497de1e9b166719c0b5ea9a'
APPROVAL='workspace/translation/approvals/20261030_second_review6.json'
AUTHOR='workspace/translation/authored/'+NAME+'.json'
BEFORE='qa/ssot/20261030_before_second_review26'
QUESTION='["request_user_input_async","call_52570ecdda38417c8d73c983b3eb01cc",0]'
ANSWER='6개 모두 제안대로 반영 (권장)'
STATIC={1386,1582,1638,1834,2030}
PREFIX='PSP_GAME/USRDIR/locale/en_us_'
rd=lambda p:json.loads((ROOT/p).read_text(encoding='utf8'))
tokens=lambda text:re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\d+|\r\n',text)


def frozen_rows():
    proposal=rd(PACKET);assert proposal['artifact_sha256']==PARENT and proposal['entries_sha256']==ENTRIES
    current=rd('workspace/translation/review/20261030_schema25_second_review_v20/packet.json')
    by={r['id']:r for r in current['records']};rows=[]
    for item in proposal['rows']:
        old=by[item['id']]
        assert old['wording']==old['payload_text']==item['before'] and old['status']=='selected'
        assert old['source_sha256']==item['source_sha256']
        text=item['before']
        for change in item['exact_changes']:
            assert text.count(change['before'])==1
            text=text.replace(change['before'],change['after'],1)
        assert text==item['after'] and tokens(text)==tokens(item['before']) and '\0' not in text
        assert text==unicodedata.normalize('NFC',text)
        if item['bank']=='static':
            assert item['key'] in STATIC and item['exact_changes']==[dict(before='성당기사',after='성전기사')]
            assert len(text.encode('utf8'))<250
        else:
            assert item['key']==2561 and item['exact_changes']==[dict(before='얼마 전 케일리처럼',after='얼마 전 케일리가 그랬듯')]
            assert text.endswith('서두르게, 젊은 영웅. 더는 시간이 없을까 두렵네.')
        rows.append(dict(id=item['id'],bank=item['bank'],key=item['key'],source=old['source'],source_sha256=item['source_sha256'],
                         previous_decision=old['decision'],before=item['before'],after=text,
                         before_sha256=item['before_sha256'],after_sha256=item['after_sha256'],exact_changes=item['exact_changes']))
    assert len(rows)==6 and {r['key'] for r in rows}==STATIC|{2561}
    return rows


def approved_rows():
    rows=frozen_rows();a=rd(APPROVAL);author=rd(AUTHOR)
    assert a['authority']=='user' and a['answer']==ANSWER and a['question_item_id']==QUESTION
    assert a['packet_sha256']==digest((ROOT/PACKET).read_bytes()) and a['pairs']==rows
    assert author['records']==[dict(r,text=r['after']) for r in rows]
    assert not a['whole_wording_support_distribution_approval']
    return rows


def configuration():
    rows=approved_rows()
    return dict(schema_version=26,policy='development_poc_non_distributable',
                parent_config=PARENT_CONFIG,parent_config_sha256=digest((ROOT/'config'/PARENT_CONFIG).read_bytes()),
                parent_artifact='workspace/runtime/optional_layout_20261030/artifact.json',parent_artifact_sha256=PARENT,
                packet=PACKET,packet_sha256=digest((ROOT/PACKET).read_bytes()),
                approval=APPROVAL,approval_sha256=digest((ROOT/APPROVAL).read_bytes()),
                author=AUTHOR,author_sha256=digest((ROOT/AUTHOR).read_bytes()),
                exact_static_keys=sorted(STATIC),exact_trans_keys=[2561],
                terminology_sha256=digest((BASE/'terminology.json').read_bytes()),
                scope='Exact approved six scoped edits only; current3569+derived2 and user exclusion404 retained. Portraits/controls/paragraphs/numbers/references/other prose preserved. Not whole-wording/support/distribution approval.',
                release_eligible=False)


def select():
    snapshot=ROOT/BEFORE;assert not snapshot.exists() and not (ROOT/APPROVAL).exists() and not (ROOT/AUTHOR).exists()
    rows=frozen_rows();entries=BASE/'entries.jsonl';oldraw=entries.read_bytes();terms_path=BASE/'terminology.json'
    assert digest(oldraw)==ENTRIES and digest(terms_path.read_bytes())==TERMS
    assert digest((ROOT/'workspace/runtime/optional_layout_20261030/artifact.json').read_bytes())==PARENT
    es=lines(entries);by={e['id']:e for e in es};ds=decisions();assert len(es)==3973 and len(ds)==4437
    for row in rows:
        e=by[row['id']];assert e['development_diagnostic_selection']==row['previous_decision']
        assert resolve(ds[row['previous_decision']])==row['before'] and e['release_selection'] is None and not e['distribution_eligible']
    files=['workspace/translation/entries.jsonl','workspace/translation/terminology.json',
           'scripts/build_font_folder.py','scripts/optional_layout_20261030.py','scripts/book_role_runtime_20261024.py',
           'scripts/manual_play_20261024.py','config/'+PARENT_CONFIG,
           'workspace/runtime/optional_layout_20261030/artifact.json','workspace/runtime/optional_layout_20261030/expected_writes.json',
           'docs/HANDOFF.md','docs/HANDOFF_2026-10-30.md','AGENTS.md','README.md','qa/reports/continuation_queue_20261024.json',PACKET]
    for name in files:
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    approval=dict(status='USER_APPROVED_EXACT_SIX_SECOND_REVIEW_CHOICES',authority='user',date_local='2026-10-30',
                  question_item_id=QUESTION,answer=ANSWER,packet=PACKET,packet_sha256=digest((ROOT/PACKET).read_bytes()),
                  pairs=rows,entries_before_sha256=ENTRIES,terminology_before_sha256=TERMS,parent25_artifact_sha256=PARENT,
                  whole_wording_support_distribution_approval=False,
                  preserved=['Other3967 original entry lines','Derived4009/4010','Original404 excluded payloads',
                             'Portraits/paragraphs/controls/numbers/references','Approved2561 finalsentence','Original title-map/credits/name-entry scope'])
    protected_write(ROOT/APPROVAL,json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
    protected_write(ROOT/AUTHOR,json.dumps(dict(policy='Only six exact approved fragments; no rule outside these IDs',records=[dict(r,text=r['after']) for r in rows]),ensure_ascii=False,indent=2)+'\n')
    terms=rd('workspace/translation/terminology.json');assert len(terms['approved_decisions'])==19
    additions=[]
    for i,row in enumerate(rows):
        e=by[row['id']];did=f'{NAME}:{row["bank"]}:{row["key"]}'
        additions.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
                              wording_ref=dict(path=AUTHOR,sha256=digest((ROOT/AUTHOR).read_bytes()),json_pointer=f'/records/{i}/text'),
                              broader_decision_id=row['previous_decision'],applicability=dict(revision='ULKS46015-v1.01',context=NAME,scope='Only declared exact fragment in this key'),
                              rationale='User selected all six independently reviewed/curated exact proposals.',
                              semantic_impact='Disambiguate recent Kaylee comparison or exact Templar label consistency;no full wording/support/release approval.',
                              human_wording_choice_ref=dict(path=APPROVAL,sha256=digest((ROOT/APPROVAL).read_bytes())),
                              state='needs_human_review',approval=None,distribution_eligible=False,
                              independent_semantic_review=dict(path='qa/reports/second_review25_20261030_audit.json',sha256=digest((ROOT/'qa/reports/second_review25_20261030_audit.json').read_bytes()),
                                                               scope='Pre-edit independent review; exact chosen minimally changed phrase also has follow-up; five labels have user terminology choice. Not full human approval.')))
        e.update(development_diagnostic_selection=did,current_working_decision=did,context_id=NAME);e['decision_ids'].append(did)
        if row['bank']=='static':
            terms['approved_decisions'].append(dict(id=f'approved-second-review26-{row["key"]}-20261030',source_id=e['id'],source_sha256=e['source_sha256'],
                                                    source_referent=row['source'],approved_wording=row['after'],state='approved',
                                                    applicability='Only this exact five-set item label; no faction-identity claim or other-key normalization',
                                                    approval=dict(authority='user',date_local='2026-10-30',chosen_answer=ANSWER,choice_ref=APPROVAL,scope='Exact label only'),
                                                    normalization_policy='Exact full label replacement only'))
    targets={r['id'] for r in rows};oldlines=oldraw.splitlines(keepends=True)
    newlines=[serialized([e]).encode('utf8') if e['id'] in targets else raw for e,raw in zip(es,oldlines)]
    assert len(newlines)==3973 and sum(a!=b for a,b in zip(oldlines,newlines))==6
    assert sum(bool(e['development_diagnostic_selection']) for e in es)==3569 and len(terms['approved_decisions'])==24
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(additions))
    temp=entries.with_name('entries.second_review26.pending');assert not temp.exists();temp.write_bytes(b''.join(newlines));temp.replace(entries)
    temp=terms_path.with_name('terminology.second_review26.pending');assert not temp.exists();temp.write_text(json.dumps(terms,ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(terms_path)
    assert len(decisions())==4443
    protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    report=dict(status='SIX_EXACT_APPROVED_CHOICES_SELECTED_SCHEMA26_BUILD_RUNTIME_PENDING',
                selected=3569,derived=2,excluded_unknown404=True,decisions=4443,modified_original_entries=6,
                other3967_raw_lines_identical=True,approved_label_decisions=24,old19_term_decisions_preserved=True,
                entries_sha256=digest(entries.read_bytes()),terminology_sha256=digest(terms_path.read_bytes()),
                approval=APPROVAL,launcher_retained='optional_layout_20261030',release_eligible=False)
    save_json(ROOT/'qa/reports/second_review26_20261030_selection.json',report)
    save_json(snapshot/'manifest.json',dict(before={n:digest((snapshot/n).read_bytes()) for n in files},entries_before=ENTRIES,entries_after=report['entries_sha256'],parent25_unchanged=True))
    q=rd('qa/reports/continuation_queue_20261024.json');q.update(status=report['status'],second_review_wording_choices_pending=False,
        second_review6_answer=ANSWER,second_review6_approval=APPROVAL,decisions=4443,decision_history=4443,
        candidate_config='config/'+CONFIG,candidate_build='workspace/runtime/'+NAME+'/disc',current_launcher_still25=True,
        next_action='Source-derived schema26 build/verify and only3locale files/6logicalpayload delta. Necessary original dialogue2561 ten pages and five original item labels;preserve source/current25/user saves/noISO.',work_continues=True)
    save_json(ROOT/'qa/reports/continuation_queue_20261024.json',q)
    h=(ROOT/'docs/HANDOFF.md').read_text(encoding='utf8');assert h==(ROOT/'docs/HANDOFF_2026-10-30.md').read_text(encoding='utf8')
    note='\n\n## 사용자6개승인·schema26원고선택반영\n\n사용자가6개모두제안대로반영을선택했다.2561한구절과Templar장비5개만선택반영했고다른3967원고rawline/파생2/기존19승인용어는같다.정확장비5개승인을용어원장에추가해24개,결정4443이다.작성3973/선택3569+파생2/범위제외404유지·게임25와실행기는아직보존한다.다음원본schema26/3locale6payload·다른77파일동일→실제2561열쪽·장비5표시→재현/검토/비공개패키지갱신후채택이다.전체문안/지원/배포승인은별도·ISO0.\n'
    for name in ['docs/HANDOFF.md','docs/HANDOFF_2026-10-30.md']:(ROOT/name).write_text(h+note,encoding='utf8',newline='\n')
    print('SELECTED6/other3967rawsame/terms19+5/decisions4443;schema26buildpending/launcher25retained.')


def assert_descendant_selection(entry,parent_row):
    """Only the exact approved26 child of parent25's2561 may supersede selection."""
    rows=approved_rows();row=next(r for r in rows if r['bank']=='trans' and r['key']==2561)
    did=f'{NAME}:trans:2561';parent_did='optional_layout_20261030:trans:2561'
    assert parent_row['key']==2561 and row['id']==entry['id'] and row['before']==parent_row['after']
    assert row['previous_decision']==parent_did and parent_did in entry['decision_ids']
    assert entry['development_diagnostic_selection']==did and resolve(decisions()[did])==row['after']
    assert entry['release_selection'] is None and not entry['distribution_eligible']


def derive_second_review(cfg):
    assert cfg==configuration();rows=approved_rows();es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions()
    for row in rows:
        e=es[row['id']];did=f'{NAME}:{row["bank"]}:{row["key"]}'
        assert e['development_diagnostic_selection']==did and resolve(ds[did])==row['after']
        assert e['release_selection'] is None and not e['distribution_eligible']
    from optional_layout_20261030 import derive_optional_layout
    plan,outputs=derive_optional_layout(rd('config/'+PARENT_CONFIG))
    parent=rd('workspace/runtime/optional_layout_20261030/artifact.json')
    for path,pin in plan['all_source_files'].items():
        raw=outputs.get(path);computed=dict(size=len(raw),sha256=digest(raw)) if raw is not None else dict(size=pin['size'],sha256=pin['sha256'])
        assert computed==parent['files'][path],('Parent25 source reconstruction drift',path)
    plan=copy.deepcopy(plan);outputs=dict(outputs);prior=dict(outputs)
    from review17_20261024 import static_rows
    old=outputs[PREFIX+'static.dat'];static=bytearray(old[:4]);bykey={r['key']:r for r in rows if r['bank']=='static'};changed=[]
    for key,payload in static_rows(old):
        if key in bykey:
            row=bykey[key];assert payload==row['before'].encode('utf8');payload=row['after'].encode('utf8');changed.append(key)
        static.extend(struct.pack('<IH',key,len(payload)));static.extend(payload)
    assert set(changed)==STATIC
    from optional_layout_preflight_20261030 import rewrite
    directory,trans=rewrite(outputs[PREFIX+'dir.dat'],outputs[PREFIX+'trans.dat'],[r for r in rows if r['bank']=='trans'])
    changes={PREFIX+'static.dat':bytes(static),PREFIX+'dir.dat':directory,PREFIX+'trans.dat':trans}
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw
        plan['writes'].append(dict(owner='User-approved secondreview six exact edits',path=path,offset=0,size=len(raw),source_size=len(original),expected_sha256=digest(original),final_sha256=digest(raw),
                                  derivation='Immutable source through exactly reconstructed25;5static labels+1trans phrase only, all remaining payloads/English/keys/flags/refs preserved.'))
    assert {p for p in outputs if outputs[p]!=prior[p]}==set(changes)
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['approved_second_review6']=dict(approval=APPROVAL,static_keys=sorted(STATIC),trans_keys=[2561],
                                        parent25_all80_source_derived_match=True,other77_parent_files_identical=True,
                                        selected3569_derived2_excluded404=True,native_validation_pending=True,release_eligible=False)
    plan['font']['scope']='Same five fonts/code/WAD/DB andselected3569+derived2;exact6userapprovedsecondreviewedits only;whole-wording/support/release approval separate.'
    return plan,outputs


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['select']);parser.parse_args();select()

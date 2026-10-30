"""Retain three source-identical numeric controls; reuse identical verified payload."""
import argparse,copy,json,struct
from collections import Counter
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from victory_korean_20261024 import CONFIG as PARENT_CONFIG,derive_victory

NAME='retained_numeric_formats_20261024';CONFIG=f'development_{NAME}.json'
BASE=ROOT/'workspace/translation';BASIS='victory_journal_20261024'
TEXTS={3085:'$a - $b',3086:'$a / $b',3087:'(x$a)'}

def rows():
    authored=json.loads((BASE/'authored/residual_static_20261022.json').read_text(encoding='utf-8'))['drafts']
    records=[r for r in authored if r['key'] in TEXTS]
    assert len(records)==3 and all(r['source_text']==r['text']==TEXTS[r['key']] for r in records)
    return [dict(key=k,source_text=t,text=t,policy='source_identical_numeric_control_no_prose_transformation') for k,t in sorted(TEXTS.items())]

def config():
    pp=ROOT/'config'/PARENT_CONFIG
    paths=['qa/reports/numeric_inventory_20261024_runtime.json','qa/reports/count_ammo_reference_20261024_runtime.json']
    return dict(schema_version=13,policy='development_poc_non_distributable',parent_config=PARENT_CONFIG,parent_config_sha256=digest(pp.read_bytes()),
        retained_static_formats=rows(),runtime_evidence=[dict(path=p,sha256=digest((ROOT/p).read_bytes())) for p in paths])

def derive_retained(cfg):
    assert cfg==config() and cfg['schema_version']==13
    proof=[json.loads((ROOT/r['path']).read_text(encoding='utf-8')) for r in cfg['runtime_evidence']]
    assert proof[0]['status']=='PASS_READ_ONLY_NATIVE_RANGE_AND_RATIO_LOOKUP_AND_DRAW_OWNER'
    assert proof[1]['status']=='PASS_NATIVE3087_INTEGER_SLOT_FORMAT_AND_VISIBLE_KOREAN_TOOLTIP_SOURCE_ARROWS_FIXTURE'
    pp=ROOT/'config'/PARENT_CONFIG;plan,outputs=derive_victory(json.loads(pp.read_text(encoding='utf-8')))
    # Existing range/ratio observations used another artifact. These two whole
    # files, including formatter code/static templates, are identical to basis.
    basis=json.loads((ROOT/f'workspace/runtime/{BASIS}/artifact.json').read_text(encoding='utf-8'))
    earlier=json.loads((ROOT/f'workspace/runtime/{proof[0]["artifact"]}/artifact.json').read_text(encoding='utf-8'))
    for path in ['PSP_GAME/SYSDIR/EBOOT.BIN','PSP_GAME/USRDIR/locale/en_us_static.dat']:
        assert basis['files'][path]==earlier['files'][path]
    raw=outputs['PSP_GAME/USRDIR/locale/en_us_static.dat'];found={};p=4
    while p<len(raw):
        key,n=struct.unpack_from('<IH',raw,p)
        if key in TEXTS:found[key]=raw[p+6:p+6+n]
        p+=6+n
    assert p==len(raw) and found=={k:v.encode('ascii') for k,v in TEXTS.items()}
    plan=copy.deepcopy(plan);plan['diagnostic_input']=cfg
    plan['retained_numeric_formats']=dict(keys=sorted(TEXTS),source_bytes_unchanged=True,new_Hangul_prose=0,
        consumer_code_and_original_templates_unchanged=True,native_scope='3085/3086 prior natural UI;3087 declared source-Arrows RAM fixture',
        selected_original_total=3569,held_original_total=404,new_physical_payload_changes=0)
    plan['font']['scope']='Development3569 selected source units and2 derived Book roles;three numeric controls retained byte-identical,no new Hangul prose.'
    return plan,outputs

def audit_payload(write_config=False):
    cfg=config();path=ROOT/'config'/CONFIG
    if write_config:assert not path.exists()
    else:assert json.loads(path.read_text(encoding='utf-8'))==cfg
    from build_font_folder import derive
    plan,outputs=derive('unicode_hangul_alias_fallback',diagnostic=cfg)
    root=ROOT/f'workspace/runtime/{BASIS}';art=json.loads((root/'artifact.json').read_text(encoding='utf-8'))
    assert set(outputs)<=set(art['files']) and len(art['files'])==80
    for rel,m in art['files'].items():
        expected=outputs[rel] if rel in outputs else (ROOT/'extracted/disc'/rel).read_bytes()
        actual=(root/'disc'/rel).read_bytes()
        assert expected==actual and len(actual)==m['size'] and digest(actual)==m['sha256'],rel
    if write_config:protected_write(path,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    report=dict(status='PASS_SOURCE_REDERIVED_SCHEMA13_ALL80_EQUAL_EXISTING_VERIFIED_PAYLOAD_NO_COPY',
        recipe=path.relative_to(ROOT).as_posix(),recipe_sha256=digest(path.read_bytes()),payload_basis=f'workspace/runtime/{BASIS}/disc',
        frozen_basis_artifact_sha256=digest((root/'artifact.json').read_bytes()),frozen_basis_origin_recipe=PARENT_CONFIG,
        basis_artifact_metadata_not_rewritten=True,all80_payload_bytes_equal=True,source_rederived=True,
        original_static_controls_retained=sorted(TEXTS),new_Hangul_prose=0,new_game_bytes=0,new_disc_roots=0,
        inherited_runtime_evidence=cfg['runtime_evidence'],range_ratio_EBOOT_and_static_whole_files_equal=True,
        control_metadata_only=True,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_payload.json',report)
    print(json.dumps(report))

def select():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    report=json.loads((ROOT/f'qa/reports/{NAME}_payload.json').read_text(encoding='utf-8'))
    assert report['all80_payload_bytes_equal'] and report['new_game_bytes']==0
    assert digest((ROOT/'config'/CONFIG).read_bytes())==report['recipe_sha256']
    old=json.loads((ROOT/'qa/ssot/20261024_victory_journal_checkpoint/manifest.json').read_text(encoding='utf-8'))
    assert digest((BASE/'entries.jsonl').read_bytes())==old['entries_sha256']
    es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4379
    assert Counter(e['state'] for e in es)==dict(needs_human_review=3566,in_progress=407)
    author=BASE/'authored/residual_static_20261022.json';aa=json.loads(author.read_text(encoding='utf-8'))['drafts']
    before={e['id']:serialized([e]) for e in es};records=[]
    for k,t in sorted(TEXTS.items()):
        e=next(e for e in es if e['id']==f'ULKS46015-v1.01:en_us/static:{k}:occurrence1')
        broader=e['current_working_decision'];assert not e['development_diagnostic_selection'] and resolve(ds[broader])==t
        i=next(i for i,r in enumerate(aa) if r['key']==k);assert aa[i]['source_text']==aa[i]['text']==t
        did=f'development_{NAME}:static:{k}'
        records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],broader_decision_id=broader,
            wording_ref=dict(path=author.relative_to(ROOT).as_posix(),sha256=digest(author.read_bytes()),json_pointer=f'/drafts/{i}/text'),
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Retain original numeric control bytes;no prose,token or gameplay change'),
            rationale='Source wrapper/owned formatting and native output now verified. Original numeric control is identical to existing working proposal and active payload.',
            semantic_impact='No translated prose or numerical meaning change.3087 uses declared source-Arrows fixture;natural acquisition not claimed.',
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    target={r['source_id'] for r in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in target)
    snap=ROOT/'qa/ssot/20261024_before_retained_numeric';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',ROOT/'docs/HANDOFF.md',ROOT/'config'/CONFIG]:protected_write(snap/p.name,p.read_text(encoding='utf-8'))
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf-8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4382 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',dict(status='SELECTED3_SOURCE_IDENTICAL_NUMERIC_CONTROLS_NO_NEW_GAME_BYTES',
        authored=3973,selected=3569,held=404,derived_Book_roles=2,decision_history=4382,new_Hangul_prose=0,new_game_bytes=0,
        reused_payload_basis=report['payload_basis'],active_recipe='config/'+CONFIG,basis_origin_recipe_not_rewritten=PARENT_CONFIG,
        human_wording_approval=False,release_eligible=False))
    print('Selected3 source-identical controls;3569 selected,404 held,4382 decisions;game bytes/copies0.')

def checkpoint():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4382 and Counter(e['state'] for e in es)==dict(needs_human_review=3569,in_progress=404)
    before=lines(ROOT/'qa/ssot/20261024_before_retained_numeric/entries.jsonl');old={e['id']:e for e in before}
    for e in es:
        if e['id'] in {f'ULKS46015-v1.01:en_us/static:{k}:occurrence1' for k in TEXTS}:
            assert resolve(ds[e['development_diagnostic_selection']])==TEXTS[next(k for k in TEXTS if e['id'].endswith(f':{k}:occurrence1'))]
        else:assert e==old[e['id']]
    payload=json.loads((ROOT/f'qa/reports/{NAME}_payload.json').read_text(encoding='utf-8'));assert payload['all80_payload_bytes_equal']
    cfg=ROOT/'config'/CONFIG;basis=ROOT/f'workspace/runtime/{BASIS}/artifact.json'
    assert digest(cfg.read_bytes())==payload['recipe_sha256'] and digest(basis.read_bytes())==payload['frozen_basis_artifact_sha256']
    scope=lines(BASE/'scope/current_entries.jsonl');held={e['id'] for e in es if not e['development_diagnostic_selection']}
    assert len(held)==404 and sum(e['selected'] for e in scope)==3569 and all(not e['typed_references'] for e in scope if e['id'] in held)
    queuepath=ROOT/'qa/reports/continuation_queue_20261024.json';queue=json.loads(queuepath.read_text(encoding='utf-8'));queue['records']=[r for r in queue['records'] if r['id'] in held]
    assert {r['id'] for r in queue['records']}==held
    hashes=dict(entries_sha256=digest((BASE/'entries.jsonl').read_bytes()),terminology_sha256=digest((BASE/'terminology.json').read_bytes()),config_sha256=digest(cfg.read_bytes()),artifact_sha256=digest(basis.read_bytes()))
    queue.update(status='PASS_404_HELD_ORIGINAL_BYTES_BY_UNCHANGED_PAYLOAD_AND_CURRENT_SELECTION',selected=3569,working_unselected=404,decision_history=4382,
        prior_held_remaining=35,newly_authored_held=369,held_bank_counts=dict(Counter(r['bank'] for r in queue['records'])),held_with_typed_refs=0,held_without_typed_refs=404,
        groups=dict(Counter(r['context'] for r in queue['records'])),current_config='config/'+CONFIG,current_build=payload['payload_basis'],
        payload_origin_config='config/'+PARENT_CONFIG,current_recipe_payload_verification=f'qa/reports/{NAME}_payload.json',**hashes)
    assert queue['held_bank_counts']==dict(static=92,trans=49,rsc=263)
    manifest=dict(hashes,selected=3569,held=404,derived_Book_roles=2,decision_history=4382,modern_Hangul_unique_demand=984,
        all80_source_rederived_equal_existing_payload=True,payload_basis=payload['payload_basis'],frozen_artifact_origin_config='config/'+PARENT_CONFIG,
        active_recipe='config/'+CONFIG,payload_equality_report_sha256=digest((ROOT/f'qa/reports/{NAME}_payload.json').read_bytes()))
    snap=ROOT/'qa/ssot/20261024_retained_numeric_checkpoint';assert not (snap/'manifest.json').exists()
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfg]:protected_write(snap/p.name,p.read_text(encoding='utf-8'))
    protected_write(snap/'manifest.json',json.dumps(manifest,indent=2)+'\n');save_json(queuepath,queue)
    save_json(ROOT/f'qa/reports/{NAME}_checkpoint.json',dict(manifest,status='CURRENT3569_404_THREE_NUMERIC_CONTROLS_RETAINED_WITHOUT_BYTE_CHANGE',
        authored_source_units=3973,new_Hangul_prose=0,new_payload_bytes=0,new_disc_roots=0,native_payload_evidence_inherited_from_identical_bytes=True,
        prior3566_entry_records_identical=True,remaining404_original_payloads_inherited_from_verified407_less_three_identity_controls=True,
        owned_native_attempts_today=13,all_owned_attempts_closed=True,held_bank_counts=queue['held_bank_counts'],whole_game_denominator_established=False,
        full_translation_or_release_approval=0,release_eligible=False))
    current=(ROOT/'docs/HANDOFF.md').read_text(encoding='utf-8')
    title='# 인계 문서 — 2026-10-24 최신 체크포인트'
    addition=f'''

현재 작성 원본 항목 **3,973 / 개발 선택 3,569 / 보류 404 / 파생Book 2 / 결정 이력 4,382 / 한글 수요 984자**다. 추가3개는 원문 그대로인 숫자 서식이며 새 한글 문장은0이다.3973은 조사 목록으로 전체 게임 완료율 분모가 아니다. 최종 번역·배포 승인은0이다.

한국어만 지원하며 공간 부족 시 다른 언어의 공간을 활용한다. 현재 공간 부족·회수·삭제0,원본/재현 보존,ISO0이다. 사용자 부재 중 문안·제품 범위 결정은 미루고 독립 작업을 계속한다. 오늘 소유13실행은 모두 복구 종료했고 예약0이다.

## 현재 재현 입력과 검증 폴더

현재 recipe는 `config/{CONFIG}`(schema13)다. 원본 재파생 결과 **80개 파일 전체가 기존 `workspace/runtime/{BASIS}/disc`와 같아**, 이 폴더를 계속 사용하고 추가 복사본을 만들지 않았다. 이 폴더의 고정artifact는 schema12 `config/{PARENT_CONFIG}`에서 만들어졌다는 원래 이력을 보존한다. 두 설정의 입력 메타데이터를 같은 것으로 주장하지 않으며 schema13의 바이트 동등성 보고서로 연결한다.

- 현재recipe SHA-256: `{hashes['config_sha256']}`
- 기존artifact SHA-256: `{hashes['artifact_sha256']}`
- 재파생/기존폴더 대조: `python -B scripts/retained_numeric_formats_20261024.py audit_payload`
- 별도 새 폴더 재생성이 필요할 때: `python -B scripts/build_font_folder.py --variant unicode_hangul_alias_fallback --name retained_numeric_formats_20261024 --diagnostic-config config/{CONFIG}`. 지금은 실행하지 않아 새 disc 루트0이다. 기존 고정artifact에 새recipe를 덮어씌우지 않는다.

## 원문 숫자 서식3개 기술 종료

3085 `$a - $b`,3086 `$a / $b`,3087 `(x$a)`의 원래바이트·토큰·숫자 의미를 유지한다. 앞의 둘은 이전 자연 소지품 관찰이 있고,현재 EBOOT와static 파일 전체가 그때와 같음을 확인했다.3087은 실제 화살 정의를 참조한 선언된6바이트 RAM 시험에서 전체‘(x2)’와 한글 툴팁을 확인했다. 자연 획득·장착·진행·저장은 검증하지 않았다. 상세한 복구 경계와 관찰 한계는 아래 기록 및 보고서를 따른다.

실제 소비/소유 경로가 확인되어 기존 원문 동일 초안을 개발 선택한 것이며 문안 변환·새한글·새게임바이트·새에뮬레이터 실행은0이다. 다른3566개 원고/선택 레코드와 용어는 그대로고 결정3개만 추가했다. 새recipe는 같은실행파일을 사용하므로 기존 네이티브 증거의 범위를 그대로 물려받는다.

보류404개는 **static92 / trans49 / RSC263**이고,그중 현재 채택한 typed-reference를 가진 보류 항목은0개다. 미참조=미사용 또는 게임전체추출완료로 해석하지 않는다. RSC263은 직렬화 준비와 초기 파일요청 부재 관찰까지만 있으며 실제 로더/소비·버퍼 계약은 미확정이다. BOOT inline/graphics 등의 별도 범위도 게임 전체 완료를 선언하기 전에 남는다.

- [현재고정SSOT/recipe](../qa/ssot/20261024_retained_numeric_checkpoint/manifest.json)
- [80파일 동등성](../qa/reports/{NAME}_payload.json)
- [현재선택 검증](../qa/reports/{NAME}_checkpoint.json)
- [404개 잔여 목록](../qa/reports/continuation_queue_20261024.json)
- [복귀 후 검토 사항](DEFERRED_REVIEW_2026-10-24.md)

다음은 복귀 후 판단할 항목의 정확한 원문/기존원고/근거를 현재 고정본에 묶어 정리하는 것이다. 의사결정이나 일괄 교정을 먼저 실행하지 않는다. 아래는 앞선 같은 날 단계의 상세 증거로,이전 카운트/최신 경로 표기는 해당 시점의 기록이다.

---

'''
    doc=title+addition+current;assert '\ufffd' not in doc and '??' not in doc
    for p in [ROOT/'docs/HANDOFF.md',ROOT/'docs/HANDOFF_2026-10-24.md']:p.write_text(doc,encoding='utf-8')
    notice='2026-10-24 한국어전용·사용자부재중계속. 작성3973/선택3569/보류404/파생Book2/결정4382/한글수요984. 숫자3개 원문동일 서식의 기술검증을 선택이력에 연결,새한글/게임바이트/폴더복사0. 현재recipe retained_numeric_formats_20261024(schema13),검증payload victory_journal_20261024(disc)의 고정artifact는schema12출신. 80파일원본재파생동등성으로연결. 소유13실행모두복구종료,예약0. 다른언어공간필요시활용승인·원본보존·ISO0. docs/HANDOFF.md기준.'
    for p in [ROOT/'AGENTS.md',ROOT/'README.md',BASE/'README.md']:
        parts=p.read_text(encoding='utf-8').split('\n\n',2);p.write_text(parts[0]+'\n\n'+notice+'\n\n'+parts[2],encoding='utf-8')
    assert (ROOT/'docs/HANDOFF.md').read_bytes()==(ROOT/'docs/HANDOFF_2026-10-24.md').read_bytes()
    print(json.dumps(manifest))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','audit_payload','select','checkpoint']);a=p.parse_args()
    if a.action=='prepare':audit_payload(True)
    elif a.action=='audit_payload':audit_payload()
    elif a.action=='select':select()
    else:checkpoint()

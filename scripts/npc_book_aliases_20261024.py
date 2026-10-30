"""Source2334/2335 shared NPC and Book consumers; no product selection."""
import argparse,json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,protected_write
from allegrex_profile import Profile

NAME='shared_voice_20261023';BASE=ROOT/'workspace/translation'
PINS=dict(entries_sha256='46a6b3e514c2035a09f62409345c4fc5fe1e1c4d9fb247ef9bc29f25dd1d0998',
    terminology_sha256='f01592af2339abc882a7b20436b62eb28de1c6ff51f7fa36371be1b63cbeba6a',
    config_sha256='ed2076f7645df9915d550a868910c3c43472d309494740a22fdff50a39d7d83a',
    artifact_sha256='061a82d920b2498834198876dfd5388593a9de3616897bd53ea7bc0bd03ab546')

def fixed():
    for path,key in [(BASE/'entries.jsonl','entries_sha256'),(BASE/'terminology.json','terminology_sha256'),
        (ROOT/f'config/development_{NAME}.json','config_sha256'),(ROOT/f'workspace/runtime/{NAME}/artifact.json','artifact_sha256')]:assert digest(path.read_bytes())==PINS[key],str(path)
    return PINS

def static():
    fixed();snapshot=ROOT/'qa/ssot/20261024_resume_baseline';snapshot.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',ROOT/f'config/development_{NAME}.json']:
        protected_write(snapshot/p.name,p.read_text(encoding='utf-8'))
    b=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(b)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    from translation_scope import collect
    scope,_=collect();src={s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    from npc_exception_drafts_20261020 import DRAFTS
    records=[]
    for k,field in [(2334,40),(2335,24)]:
        refs=next(r['typed_references'] for r in scope if r['bank']=='trans' and r['key']==k)
        assert {(r['table'],r['row'],r['field']) for r in refs}=={(13,8,12 if k==2334 else 16),(15,81,field)}
        s=src[k];raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert digest(raw)==s['source_sha256'] and raw.hex()==s['source_hex']
        assert s['source_text'].endswith('*BUG THIS*') and s['source_text'].count('*B')==1
        records.append(dict(key=k,source=s,existing_held_draft=DRAFTS[k],references=refs,
            null_actor_expected=s['source_text'].replace('\r',' ').replace('*B','Itself'),
            expected_scope='Prediction for preserved null-actor async Book formatting only; not actual Bron actor formatting'))
    t14,n14=struct.unpack_from('<II',db,14*8);t15,n15=struct.unpack_from('<II',db,15*8)
    assert (t14,n14,t15,n15)==(340700,45,342680,134)
    links=[]
    for i in range(n14):
        for j,index in enumerate(struct.unpack_from('<6h',db,t14+i*44+18)):
            if index==81:links.append(dict(table14_row=i,reference_slot=j))
    out=ROOT/'workspace/analysis/npc_book_aliases_20261024';p=Profile();windows=[]
    for name,a,z in [('body_title_prefetch',0x4f3b4,0x4f524),('NPC_actor_decoder',0x706fc,0x707cc)]:
        raw=b[128+a:128+z];r=p.verify_roundtrip(raw,a,out,name)
        (out/(name+'.listing.txt')).write_text(''.join('{:08X} {}\n'.format(x['pc'],x['assembly']) for x in r),encoding='utf-8')
        windows.append(dict(name=name,start=a,end_exclusive=z,sha256=digest(raw),instructions=len(r)))
    report=dict(status='SOURCE_TWO_NPC_BOOK_ALIASES_AND_PRESERVED_STAR_B_BOUNDARY',records=records,verified_windows=windows,
        original_table13_row8_hex=db[336020+8*260:336020+9*260].hex(),original_table15_row81_hex=db[t15+81*56:t15+82*56].hex(),
        signed_table14_six_slot_links_to_row81=links,missing_known_link_not_unused_proof=True,
        intervention_plan=dict(table15_row=73,fields={24:2335,40:2334},previous_fields={24:2502,40:2266},bytes=8,
            meaning='Borrow the two original row81 text keys into existing first quest; no original row81 acquisition claim'),
        SSOT_or_game_changed=False,new_selected=0,release_eligible=False)
    save_json(ROOT/'qa/reports/npc_book_aliases_20261024_static.json',report)
    art=ROOT/f'workspace/runtime/{NAME}/artifact.json';a=json.loads(art.read_text(encoding='utf-8'))
    for rel,m in a['files'].items():
        raw=(art.parent/'disc'/rel).read_bytes();assert len(raw)==m['size'] and digest(raw)==m['sha256']
    protected_write(snapshot/'manifest.json',json.dumps(dict(PINS,all80_verified=True,authored=3973,selected=3538,held=435,decisions=4349),indent=2)+'\n')
    old=ROOT/'docs/HANDOFF_2026-10-23.md';oldsha=digest(old.read_bytes())
    doc='''# 인계 문서 — 2026-10-24

사용자의 “다시 진행”으로 재개했다. 작성3973 / 개발선택3538 / 보류435 / 결정4349 / 현대 한글수요984. 승인명칭14,전체 번역·배포 승인0이다. 현재 폴더는 `workspace/runtime/shared_voice_20261023/disc`, 설정은 `config/development_shared_voice_20261023.json`이다.80파일과 원고/용어/설정/아티팩트 해시를 재검사하고 오늘 재개 snapshot을 보존했다.3973개를 전체 게임 완료 분모로 삼지 않는다.

현재 작업은2334·2335의 브론 일반대사와table15행81 제목·Book본문 공유를 분리해 확인하는 것이다. 두 원문 끝의 *BUG THIS*는 기존 *B 치환 경로를 포함하므로 임의 삭제·리터럴 취급·자동 교정하지 않는다. 원래 NPC 객체의706FC actor 처리와 null-actor707CC 공통/Book 처리를 구분한다. table14의 알려진6개 signed index필드에는 행81 연결이 없지만,다른 경로·사용·미사용을 단정하지 않는다.

오늘 정적 조사 시점에는 새 원고/개발선택/빌드/실행0이며435개는 계속 원문이다. 다음은 같은 검증 아티팩트의 자체 상태에서 첫퀘스트행73의 두4바이트 텍스트 참조만 원본행81 값으로 바꿔 실제 Book처리·표시를 비교한다. 원래행81 자연획득·실제 브론 대화·엔딩 검증이 아니다. 조사 뒤CPU와 관련범위를 자체 상태로 복구하고,정확한 소유 launch/PID/시작 정체성만 종료한다. 오류 시 상태를 폐기하고 실패를PASS에서 제외한다.

사용자 결정 유지:3548 한 문구 평어체·원래 두 참조/사빈 초상화 보존,3544 영문 실패 의미,제작진 본문 전체 원문 보존,여관명 및 정확한13표시명 범위. ISO 생성 금지,다른 PPSSPP 보존,원본·이전 원고·실패/QA 보존. 삭제 거부된 `workspace/runtime/map_corpus_20261020/disc` 삭제를 재시도하지 않는다.25개mode3 등 동등한 부재 조사와 엔딩까지 순차 플레이를 반복하지 않는다. 새 중지 지시 전까지 번역·재삽입 우선으로 계속한다.

- [전날 인계](HANDOFF_2026-10-23.md)
- [재개 고정본](../qa/ssot/20261024_resume_baseline/manifest.json)
- [두 공유문구 원본/초안/참조/치환 경계](../qa/reports/npc_book_aliases_20261024_static.json)
- [현재435개 보류 목록](../qa/reports/continuation_queue_20261023.json)
'''
    assert '\ufffd' not in doc
    protected_write(ROOT/'docs/HANDOFF_2026-10-24.md',doc);(ROOT/'docs/HANDOFF.md').write_text(doc,encoding='utf-8');assert digest(old.read_bytes())==oldsha
    notice='2026-10-24 재개·계속 진행. 작성3973 / 개발선택3538 / 보류435 / 결정4349 / 한글수요984. 현재shared_voice_20261023 검증본 고정.2334/2335 NPC와Book 제목/본문 공유를 원문부터 확인 중.3548 한 문구 평어체·3544 실패 의미·제작진 원문·승인명칭14 유지. ISO 생성 금지,다른 PPSSPP 보존. docs/HANDOFF.md가 현재 기준이다.'
    for path in [ROOT/'AGENTS.md',ROOT/'README.md',BASE/'README.md']:
        text=path.read_text(encoding='utf-8');parts=text.split('\n\n',2);assert parts[1].startswith('2026-10-23 계속 진행.')
        path.write_text(parts[0]+'\n\n'+notice+'\n\n'+parts[2],encoding='utf-8')
    print(json.dumps(dict(status=report['status'],source_alias_keys=[2334,2335],all80_verified=True,new_selected=0,known_table14_links=len(links))))

def prepare(q):
    fixed();source=ROOT/'qa/runtime/20261023_shared_voice_korean_attempt02';pre=json.loads((source/'preflight.json').read_text(encoding='utf-8'))
    assert pre['artifact_name']==NAME and pre['artifact_sha256']==PINS['artifact_sha256']
    state=source/'exact_before_prefetch.ppst';assert pre['cpu']['cpu.pc']==0x08804000+0x4f358
    context=pre['ranges'][1];rowptr=struct.unpack_from('<I',bytes.fromhex(context['hex']),4)[0];t15=rowptr-73*56
    assert 0x08800000<t15<0x0a000000
    report=json.loads((ROOT/'qa/reports/npc_book_aliases_20261024_static.json').read_text(encoding='utf-8'))
    pre=dict(pre,source_state=state.relative_to(ROOT).as_posix(),source_state_sha256=digest(state.read_bytes()),
        cold_boot=False,same_artifact_state_imports=1,other_artifact_state_imports=0,kind='source',cases=report['records'],T15_address=t15,
        limitation='Original text keys through actual Book consumers; first-row reference fixture, not source row81 acquisition or Bron speaking.')
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    protected_write(q/'preflight.json',json.dumps(pre,ensure_ascii=False,indent=2)+'\n');print(json.dumps(pre,ensure_ascii=True))

def audit(q,active_keys=None,artifact_name=NAME,report_name='npc_book_aliases_source_20261024_runtime',case_prefix=''):
    from environment_owned_scope_20261022 import environment
    from PIL import Image
    fixed();read=lambda name:json.loads((q/(name+'.json')).read_text(encoding='utf-8'))
    case_read=lambda name:read(case_prefix+name)
    active_keys=active_keys or {2334:2334,2335:2335}
    pre=read('preflight');ranges=read('before_full_ranges')['reads'];assert [x['length'] for x in ranges]==[1980,136,7504]
    assert read('final_cpu')['state']==pre['cpu'] and read('final_ranges')['reads']==ranges
    if 'source_state' in pre:
        assert digest((ROOT/pre['source_state']).read_bytes())==pre['source_state_sha256']
        assert read('same_artifact_import_cpu')['state']==pre['cpu'] and read('same_artifact_import_ranges')['reads']==pre['ranges']
    else:assert pre['cold_boot'] and pre['other_artifact_state_imports']==0
    before=bytearray.fromhex(ranges[2]['hex'])
    for field,key,label in [(24,2335,'body'),(40,2334,'title')]:
        key=active_keys[key]
        old={24:2502,40:2266}[field];assert struct.unpack_from('<I',before,73*56+field)[0]==old
        struct.pack_into('<I',before,73*56+field,key);assert case_read(label+'_reference')['written']==4
        cpu=case_read(label+'_async_cpu')['state'];dest=pre['cpu']['cpu.s0']+{24:0x2c,40:0x6c}[field]
        assert (cpu['cpu.pc'],cpu['cpu.a1'],cpu['cpu.a2'],cpu['cpu.a3'])==(0x08804000+0x707cc,key,0,dest)
        case=next(x for x in pre['cases'] if x['key']==key);expected=(case['null_actor_expected']+'\0').encode('utf-16le').hex()
        assert case_read(label+'_full')['hex']==case_read('reentry_'+label+'_full')['hex']==expected
    assert case_read('edited_T15')['hex']==before.hex()
    shots=[]
    def mask(label):
        path=q/f'{case_prefix}Book_alias_{label}.png';assert digest(path.read_bytes())==case_read('Book_alias_'+label)['provenance']['sha256']
        pixels=Image.open(path).convert('RGB').crop((212,44,478,236)).tobytes()
        shots.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes())))
        return bytes(min(pixels[i:i+3])>160 for i in range(0,len(pixels),3))
    first=mask('visible');assert first==mask('right')==mask('reopen') and first!=mask('close')
    visual=read('visual_review');assert visual['source_portrait_tag_literal_visible_in_Book'] and visual['source_title_and_body_overlap'] and not visual['normal_Book_legibility_pass']
    assert read('terminal_bootstrap')['runtime_reservation_count']==0
    artifact_path=ROOT/f'workspace/runtime/{artifact_name}/artifact.json';a=json.loads(artifact_path.read_text(encoding='utf-8'))
    assert digest(artifact_path.read_bytes())==pre['artifact_sha256']
    for rel,m in a['files'].items():
        raw=(ROOT/f'workspace/runtime/{artifact_name}/disc'/rel).read_bytes();assert len(raw)==m['size'] and digest(raw)==m['sha256']
    report=dict(status='OBSERVED_ORIGINAL_TEXT_BOOK_ROLE_COLLISION_NOT_LEGIBILITY_PASS',artifact_name=artifact_name,artifact_sha256=pre['artifact_sha256'],lookup_keys=active_keys,
        source_title=2334,source_body=2335,full_expanded_UTF16_NUL_and_reentry=True,source_star_B_to_Itself=True,
        original_portrait_tag_literal_in_Book=True,title_and_body_overlap=True,Book_legibility_pass=False,
        screenshots=shots,first_tab_reopen_text_masks_equal=True,CPU_and9620_bytes_restored=True,all80_verified_after=True,
        reference_edits=2,reference_bytes=8,original_NPC_actor_or_row81_quest_acquisition_verified=False,
        source_original_disc_runtime_comparison=False,observation_scope='Untranslated2334/2335 through Book on fixed development artifact and declared first-quest reference fixture; not natural retail quest visibility',
        local_prepare_stdout_parse_error_before_launch_preserved=(q/'local_prepare_stdout_parse_error.json').exists(),tracking_unavailable_without_folder_ROM_identity=True,
        environment=environment(q),SSOT_or_game_changed=False,new_selected=0,release_eligible=False)
    save_json(q/'completed.json',report);save_json(ROOT/f'qa/reports/{report_name}.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='screenshots'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['static','prepare','audit']);p.add_argument('--q');a=p.parse_args()
    if a.action=='static':static()
    elif a.action=='prepare':prepare(ROOT/a.q)
    else:audit(ROOT/a.q)

"""One context-complete map-title batch; 96 individual proposals, one folder build."""
import argparse, copy, json, re
from collections import Counter
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized, protected_write
from audit_translation138 import resolve
from map_name_policy import population, validate
from unicode_codec042 import encode_unicode, decode_unicode
from translation_scope import collect

BASE=ROOT/'workspace/translation'
NAME='map_corpus_20261020'
PRIOR_CONFIG='development_second533.json'
CONFIG='development_map_corpus_20261020.json'
PRIOR_SHA='fbb9f8dd90da427363ef3ee3d80ab330a00fab2b7743b8496a7c0a9146b777b9'
# Every value below is an individual draft. No automated English/Korean naming rule.
DRAFTS={
139:'아벤 시',
35:'비밀 지하묘지',36:'금지된 지하묘지',37:'깊은 묘실',40:'긴 길',39:'고대 수로',43:'잊힌 지하묘지',38:'서쪽 지하묘지',
41:'동쪽 지하묘지 1층',42:'동쪽 지하묘지 2층',51:'블리크 광산',58:'음울한 소굴',52:'나이트폴 무덤',53:'셰도파인',
62:'썩어 가는 둥지',57:'매로록 북부',60:'사악한 굴',71:'애시펠 동굴',
102:'꿈의 신전 1층',84:'꿈의 신전 2층',85:'꿈의 신전 3층',78:'리븐 평원',70:'데드아이 능선',66:'매로록 남부',
72:'콜드로어 소굴',73:'아이언스톤 공동',79:'헐떡이는 동굴',80:'펠루트 땅굴',81:'비명의 전당 1층',82:'비명의 전당 2층',
86:'금지된 제단',89:'헤일샤드 요새 1층',88:'헤일샤드 요새 2층',87:'헤일샤드 요새 3층',90:'글룸폴 황무지',
91:'프로스트웨일 동굴',92:'빛나는 동굴',93:'수정 고개 서부',94:'수정 고개 동부',95:'빛을 잃은 땅',
96:'흰서리 수용소 1층',97:'흰서리 수용소 2층',140:'흰서리 수용소 3층',98:'아이센 전당 서부',100:'아이센 전당 동부',99:'아이센 전당 심부',
101:'꿈의 공간',103:'빙하 대초원',106:'수정 탑 1층',105:'수정 탑 2층',104:'수정 탑 3층',107:'시버다크',
114:'악몽의 신전 1층',115:'악몽의 신전 2층',138:'악몽의 신전 3층',108:'판데모니엄의 문',109:'불타는 미궁',110:'지옥의 심연',111:'흑요석 동굴',
112:'메리디언 탑',113:'메리디언 요새',116:'메리디언 지하감옥',117:'서밋 탑',118:'서밋 요새',119:'서밋 지하감옥',
120:'스파이어 탑',121:'스파이어 요새',122:'스파이어 지하감옥',123:'아르도르의 고개',124:'제니스 탑',125:'제니스 요새',126:'제니스 지하감옥',
127:'피너클 탑',128:'피너클 요새',129:'피너클 지하감옥',130:'마리아나스 수비성 1층',131:'마리아나스 수비성 2층',
132:'마리아나스 수비성 3층',133:'마리아나스 수비성 4층',134:'마리아나스 수비성 5층',135:'봉인실 1층',136:'봉인실 2층',137:'봉인실 3층',
44:'명예의 전당 1층',45:'명예의 전당 2층',46:'명예의 전당 3층',50:'잃어버린 지하묘지',49:'어스레스트 묘실 1층',48:'어스레스트 묘실 2층',47:'어스레스트 묘실 3층',
141:'잠자는 늑대의 굴',142:'잠자는 늑대의 신전',143:'잠자는 늑대의 소굴',144:'엘리시안 석실 1층',145:'엘리시안 석실 2층',146:'엘리시안 석실 3층'
}
RATIONALES={
139:'Established city spelling 아벤; City is a geographical label, not an additional political title.',
35:'Current2286/2287/2292 use 비밀 지하묘지; source shared place identity.',
36:'Current2314 uses 금지된 지하묘지; preserve source modifier.',
38:'Current2343/2344/2345 use 서쪽 지하묘지.',
51:'Current2446/2447 use 블리크 광산.',
53:'Current2438/2443/2445/2447/2448 use 셰도파인.',
57:'Current2510/2512 use 매로록 북부; direction is geographical, not a floor.',
66:'Current2512 uses 매로록 남부; keep distinct from northern entrance.',
70:'Current2512/2516/2517/2545 use 데드아이 능선.',
73:'Current2516/2517 use 아이언스톤 공동.',
78:'Current2562 uses 리븐 평원.',
81:'Current2549/3759 use 비명의 전당; retain original level number.',
82:'Current2549/3759 use 비명의 전당; retain original level number.',
84:'Current2561/2562 use 꿈의 신전; retain original level2.',
85:'Same Temple of Dreams referent as2561/2562; distinct original level3.',
102:'Same Temple of Dreams referent as2561/2562; distinct original level1.',
96:'Source2908/2919 link this place to captives and Nepharath experiments; 수용소 is a provisional contextual noun.',
97:'Same Hoarfrost Asylum referent as2908/2919; original level2 retained.',
140:'Same Hoarfrost Asylum referent; original table16 explicitly names level3 despite some quest prose mentioning two levels.',
135:'Source2737 identifies the Vault as a magical chamber guarding the enemy beneath Marianas Guard; 봉인실 remains a proposal.',
136:'Same magical Vault referent, distinct original level2.',
137:'Same magical Vault referent, distinct original level3.',
130:'Source3586 calls Marianas Guard an ancient prison,3716 its defensive fortress; 수비성 is provisional and not a claim about visited geometry.',
131:'Same Marianas Guard referent; original level2 retained.',
132:'Same Marianas Guard referent; original level3 retained.',
133:'Same Marianas Guard referent; original level4 retained.',
134:'Same Marianas Guard referent; original level5 retained.'
}

def decisions():
    rr=[d for p in [BASE/'diagnostic_decisions.jsonl',*sorted(BASE.glob('decisions_*.jsonl'))] for d in lines(p)]
    result={d['id']:d for d in rr};assert len(result)==len(rr);return result

def packet():
    p=BASE/'packets'/NAME
    return p

def prepare():
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();src=lines(BASE/'baseline/source_entries.jsonl');pop=population()
    assert len(DRAFTS)==96 and len(ds)==655
    missing={k for k,v in pop.items() if not es[v['source']['id']]['development_diagnostic_selection']}
    assert missing==set(DRAFTS) and all(es[pop[k]['source']['id']]['state']=='untranslated' for k in DRAFTS)
    prior=ROOT/'config'/PRIOR_CONFIG;assert digest(prior.read_bytes())==PRIOR_SHA
    snap=ROOT/'qa/ssot/20261020_before_map_corpus';snap.mkdir(parents=True,exist_ok=True)
    for path in [BASE/'entries.jsonl',BASE/'terminology.json',prior]:protected_write(snap/path.name,path.read_text(encoding='utf8'))
    _,survey=collect();protected_write(packet()/'scope_before.json',json.dumps(survey,ensure_ascii=False,indent=2)+'\n')
    contexts=[];drafts=[];book={'mapping':{c:None for c in range(0xac00,0xd7a4)}}
    for key,v in pop.items():
        s=v['source'];e=es[s['id']];did=e['development_diagnostic_selection']
        name=s['source_text'].split(' Level ')[0]
        query=re.sub(r'^(The |A )','',name)
        # Full name matches are translator context, not proof of reference completeness.
        anchors=[]
        for a in src:
            if a['bank']!='trans' or query.casefold() not in a['source_text'].casefold():continue
            ae=es[a['id']];ad=ae['development_diagnostic_selection']
            anchors.append(dict(source_id=a['id'],source_text=a['source_text'],source_sha256=a['source_sha256'],current_draft=resolve(ds[ad]) if ad else None,decision_ref=ad))
        text=resolve(ds[did]) if did else DRAFTS[key]
        r=dict(key=key,source_text=s['source_text'],text=text);validate(r,book)
        contexts.append(dict(source=s,reference=dict(table=16,row=v['row'],field=0,width=2,offset=v['offset'],expected_hex=v['expected_hex']),
                             kind='Map title',selected_before=bool(did),existing_decision=did,anchors=anchors,
                             consumer_evidence=['qa/reports/map_reference_stage245_native.json','qa/reports/threat_names_stage526_components.json']))
        if key in DRAFTS:
            drafts.append(dict(source_id=s['id'],source_sha256=s['source_sha256'],key=key,source_text=s['source_text'],text=text,
                               rationale=RATIONALES.get(key,'Individual source-bound Map-label draft; keep geographical/floor distinctions and do not infer plot from storage order.'),
                               open_issues='Proper-name pronunciation and descriptive naming are provisional; human semantic and presentation review pending.',
                               human_reviewed=False,independent_review=None,distribution_eligible=False))
    protected_write(packet()/'contexts.jsonl',serialized(contexts))
    protected_write(BASE/'authored'/f'{NAME}.json',json.dumps(dict(policy='individual_manual_development_proposals',drafts=drafts),ensure_ascii=False,indent=2)+'\n')
    # Meaningful invalid-input cases protect the broadened population guard.
    r=dict(key=134,source_text=pop[134]['source']['source_text'],text=DRAFTS[134]);rejected=[]
    for label,mut in [('wrong_source',dict(source_text=r['source_text']+'!')),('wrong_floor',dict(text='마리아나스 수비성 4층')),
                      ('embedded_NUL',dict(text=r['text']+'\0')),('invented_control',dict(text=r['text']+'[p]')),('new_line',dict(text=r['text']+'\n')),('unmapped_glyph',dict(text=r['text']+'漢'))]:
        try:validate(dict(r,**mut),book)
        except (AssertionError,ValueError):rejected.append(label)
        else:raise AssertionError('Accepted invalid map label: '+label)
    all_names=[dict(key=c['source']['key'],text=(DRAFTS[c['source']['key']] if not c['selected_before'] else resolve(ds[c['existing_decision']]))) for c in contexts]
    report=dict(status='PASS_MAP_CORPUS_CONTEXT_AND_CODEC',enumerated_map_records=113,prior_selected=17,new_individual_drafts=len(drafts),
                source_utf16_units=sum(pop[k]['source']['source_utf16_units'] for k in DRAFTS),draft_utf16_units=sum(len(r['text'].encode('utf-16le'))//2 for r in drafts),
                rejected_invalid_cases=rejected,longest_selected_map_name=max(all_names,key=lambda r:len(r['text'])),
                source_controls='113 original names are plain strings without brackets/dollar tokens; numbered suffixes retained',
                runtime_plan='Representative longest title, late area/floor, and existing familiar title on one new build; no natural-visit/full-playthrough claim',
                human_approval=False,release_eligible=False)
    save_json(ROOT/'qa/reports/map_corpus_20261020_preflight.json',report);print(json.dumps(report,ensure_ascii=False))

def apply():
    pre=json.loads((ROOT/'qa/reports/map_corpus_20261020_preflight.json').read_text(encoding='utf8'));assert pre['new_individual_drafts']==96
    snap=ROOT/'qa/ssot/20261020_before_map_corpus'
    assert (BASE/'entries.jsonl').read_bytes()==(snap/'entries.jsonl').read_bytes()
    assert (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    prior=ROOT/'config'/PRIOR_CONFIG;assert digest(prior.read_bytes())==PRIOR_SHA
    cfg=copy.deepcopy(json.loads(prior.read_text(encoding='utf8')))
    es=lines(BASE/'entries.jsonl');byid={e['id']:e for e in es};before={e['id']:serialized([e]) for e in es}
    authored=BASE/'authored'/f'{NAME}.json';drafts=json.loads(authored.read_text(encoding='utf8'))['drafts'];assert len(drafts)==96
    ds=[];book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};terms=json.loads((BASE/'terminology.json').read_text(encoding='utf8'))
    for i,d in enumerate(drafts):
        e=byid[d['source_id']];assert e['state']=='untranslated' and not e['decision_ids'] and e['source_sha256']==d['source_sha256']
        r=dict(key=d['key'],source_text=d['source_text'],text=d['text']);validate(r,book);cfg['static_overrides'].append(r)
        did=f'development_map_20261020:static:{d["key"]}'
        ds.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
                       wording_ref=dict(path=authored.relative_to(ROOT).as_posix(),sha256=digest(authored.read_bytes()),json_pointer=f'/drafts/{i}/text'),
                       applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope=f'Exact static{d["key"]}; original table16 row; no global renaming'),
                       rationale=d['rationale'],semantic_impact=d['open_issues'],state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None,
                       mechanical_evidence=['qa/reports/map_corpus_20261020_preflight.json']))
        e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
        terms['candidate_decisions'].append(dict(id=f'term-map-{d["key"]}-20261020',source_referent=d['source_text'],candidate_wording_decision_ref=did,
                                                 applicability=f'Exact static{d["key"]} Map label; no implicit prose replacement',state='unresolved',approval=None,evidence=['qa/reports/map_corpus_20261020_preflight.json']))
    target={d['source_id'] for d in drafts}
    assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in target)
    assert Counter(e['state'] for e in es)==dict(untranslated=3511,needs_human_review=459,in_progress=3)
    protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    protected_write(BASE/'decisions_map_20261020.jsonl',serialized(ds))
    # Both candidate and log are complete before atomically replacing the work state.
    temp=BASE/'entries.jsonl.map_pending';temp.write_text(serialized(es),encoding='utf8');temp.replace(BASE/'entries.jsonl')
    save_json(BASE/'terminology.json',terms)
    assert len(decisions())==751
    save_json(ROOT/'qa/reports/map_corpus_20261020_selection.json',dict(status='PASS_96_MAP_DEVELOPMENT_SELECTIONS',authored=462,selected=459,working_unselected=3,
             decisions=751,all_map_titles_selected=113,previous366_wordings_unchanged=True,config_sha256=digest((ROOT/'config'/CONFIG).read_bytes()),human_approval=False,release_eligible=False))
    print('PASS map corpus: +96 authored/selected; authored462 selected459 working3; map113/113')

def audit():
    from audit_appearance028 import candidate_audit
    from audit_selection044 import audit_selection
    import struct
    old=candidate_audit('second_relic_534',PRIOR_CONFIG,unicode_hangul=True)
    root,plan,artifact,cfg,book=candidate_audit(NAME,CONFIG,unicode_hangul=True)
    assert cfg['static_overrides'][:-96]==old[3]['static_overrides'] and cfg['trans_overrides']==old[3]['trans_overrides']
    assert {r['key'] for r in cfg['static_overrides'][-96:]}==set(DRAFTS) and plan['selected_development_draft_count']==459
    path='PSP_GAME/USRDIR/locale/en_us_static.dat'
    changed=[p for p,m in artifact['files'].items() if m!=old[2]['files'][p]];assert changed==[path]
    def records(raw):
        p=4;rr=[]
        while p<len(raw):
            k,n=struct.unpack_from('<IH',raw,p);rr.append((k,raw[p+6:p+6+n]));p+=6+n
        assert p==len(raw);return rr
    logical=[]
    a=records((old[0]/'disc'/path).read_bytes());b=records((root/'disc'/path).read_bytes());assert len(a)==len(b)==2852
    for (k,x),(kk,y) in zip(a,b):
        assert k==kk
        if x!=y:logical.append(k);assert y==DRAFTS[k].encode('utf8')
    assert set(logical)==set(DRAFTS) and len(logical)==96
    audit_selection(NAME,CONFIG,459,'qa/reports/map_corpus_20261020_selection_audit.json')
    ds=decisions();es=lines(BASE/'entries.jsonl');chars=set()
    for e in es:
        if e['state']=='untranslated':continue
        did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1]
        chars.update(c for c in resolve(ds[did]) if 0xac00<=ord(c)<=0xd7a3)
    result=dict(status='PASS_MAP_CORPUS_96_LOGICAL_CHANGES_80_FILES',authored=462,selected=459,working_unselected=3,decision_history=751,
                map_population=113,map_selected=113,new_map_keys=logical,changed_files_vs534=changed,other79_files_byte_equal=True,
                prior363_selected_values_unchanged=True,source_code_and_font_byte_equal=True,modern_Hangul_unique_demand=len(chars),
                config_sha256=digest((ROOT/'config'/CONFIG).read_bytes()),artifact_sha256=digest((root/'artifact.json').read_bytes()),
                static_growth_bytes=(root/'disc'/path).stat().st_size-(old[0]/'disc'/path).stat().st_size,
                native_representative_QA_pending=True,all96_visual_QA=False,new_ISO=False,release_eligible=False)
    save_json(ROOT/'qa/reports/map_corpus_20261020_build.json',result);print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','apply','audit']);a=p.parse_args();globals()[a.action]()

"""Seven original table16 Map labels, individual drafts and guarded development inputs."""
import copy
import json
import struct
import unicodedata
from collections import Counter
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized, protected_write
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode, decode_unicode
from text_limits import check_template

# Individually authored proposals; not a word-substitution rule or naming approval.
DRAFTS = [
    (54,16,'Sacred Vaults','성스러운 묘실','Existing2479/2480 recovery context identifies a sacred burial place;preserve existing draft name without declaring final lore approval.'),
    (55,17,'Lightfall Grove','라이트폴 숲','Named grove follows existing quest wording;Lightfall pronunciation remains provisional.'),
    (56,20,'Snoutrott Den','스나우트롯 소굴','Named tribe den linked to2465 conflict;tribal name remains provisional.'),
    (59,18,'Tornwood Forest','톤우드 숲','Individually follows earlier quest draft name;no global Forest/Grove rule.'),
    (63,23,'Wallowpit Level 1','왈로핏 1층','Preserve numbered level1 without adding underground direction or connecting it to a geographic claim.'),
    (64,24,'Wallowpit Level 2','왈로핏 2층','Preserve numbered level2;no inferred descent or area order.'),
    (65,25,'Wallowpit Level 3','왈로핏 3층','Preserve numbered level3;no inferred descent or area order.'),
]
KEYS = [x[0] for x in DRAFTS]
BASE = ROOT/'workspace/translation'
DB_SHA = 'd852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
OLD_CONFIG_SHA = '5a04db915c78ee885b682b5fcc0f3627145260966fd35a3888c7adb9d659a1bf'

def source(key):
    rows=[s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='static' and s['key']==key]
    assert len(rows)==1
    return rows[0]

def validate(r,book,encoder=encode_unicode,decoder=decode_unicode):
    assert set(r)=={'key','source_text','text'}
    spec=next(x for x in DRAFTS if x[0]==r['key'])
    key,index,english,_,_=spec
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)==DB_SHA
    off,count=struct.unpack_from('<II',db,16*8)
    assert (off,count)==(350184,113) and struct.unpack_from('<H',db,off+index*2)[0]==key
    s=source(key); raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256'] and r['source_text']==s['source_text']==english
    text=r['text']; assert text and text==unicodedata.normalize('NFC',text)
    assert not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(text,book).encode('utf8')
    assert decoder(encoded.decode('utf8'),book)==text and len(encoded)<=65535
    check_template(text,'Original table16 Map title;one-line native width remains QA obligation')
    if key in [63,64,65]:
        assert [c for c in text if c.isdigit()]==[str(key-62)]
    return encoded

def decisions():
    rows=[d for p in [BASE/'diagnostic_decisions.jsonl',*sorted(BASE.glob('decisions_*.jsonl'))] for d in lines(p)]
    result={d['id']:d for d in rows};assert len(rows)==len(result)
    return result

def context():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261018_419_checkpoint/entries.jsonl').read_bytes()
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)==DB_SHA
    off,n=struct.unpack_from('<II',db,16*8);table=db[off:off+n*2]
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();rows=[]
    for key,index,english,text,rationale in DRAFTS:
        s=source(key);assert es[s['id']]['state']=='untranslated'
        assert struct.unpack_from('<H',table,index*2)[0]==key
        matches=[];query=english.split(' Level')[0].replace(' Den','')
        for x in lines(BASE/'baseline/source_entries.jsonl'):
            if query.casefold() not in x['source_text'].casefold():continue
            e=es[x['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision')
            matches.append(dict(source=x,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
        rows.append(dict(source=s,table16_index=index,table16_byte_offset=off+index*2,original_cell_hex=table[index*2:index*2+2].hex(),
            source_bound_matches=matches,query=query,query_scope='Case-insensitive source substring only;not reference completeness'))
    dest=BASE/'packets/map_places421';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'contexts.json',json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    protected_write(dest/'REVIEW.md','''# 지도 지명7개 원문 문맥 — 421

원본T4 table16의7개u16 이름 key와 원문 span을 연결한다. 검증된 지도 경로는2CE20→708B4→130EE0(table16+행×2)→lhu key→705DC→Map 제목이다. 기존245의 원본 기계어 왕복·실행 증거를 소비 경로 근거로 보존한다. 이번7개 지명의 자연 방문·지도 모양·table17 근접 알림 증거가 아니다.

기존 퀘스트 초안의 성스러운 묘실·라이트폴 숲·스나우트롯·톤우드 숲·왈로핏을 개별 대조한다. 승인된 이름은 울부짖는 소나무 여관뿐이다. 신규 지명은 개발용 후보이며 인간 명칭·발음 승인은 남는다. Level1/2/3의 번호는 유지하고 지하·위아래 이동을 임의로 추가하지 않는다.

static34는 여관이며 table16행34의static3034(학자의 길)와 다르다. 인물·아이템 소비 경로는 이7개 지도 제목 문맥으로 해결되지 않는다.
''')
    save_json(ROOT/'qa/reports/map_places_stage421_context.json',dict(status='PASS_421_SEVEN_SOURCE_BOUND_TABLE16_NAMES',keys=KEYS,table16_sha256=digest(table),db_sha256=DB_SHA,
        prior_consumer_evidence='qa/reports/map_reference_stage245_native.json',ssot_unchanged=True,release_eligible=False))
    print('PASS421 seven original table16 Map names;SSOT unchanged')

def draft():
    es=lines(BASE/'entries.jsonl'); original=serialized(es)
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261018_419_checkpoint/entries.jsonl').read_bytes()
    assert len(decisions())==529
    ctx=json.loads((BASE/'packets/map_places421/contexts.json').read_text(encoding='utf8'))
    assert [r['source']['key'] for r in ctx]==KEYS
    snap=ROOT/'qa/ssot/20261019_422_before_map_places';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',ROOT/'config/development_gorgein410.json']:
        protected_write(snap/p.name,p.read_text(encoding='utf8'))
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};rows=[]
    for key,index,english,text,rationale in DRAFTS:
        validate(dict(key=key,source_text=english,text=text),book)
        s=source(key);rows.append(dict(source_id=s['id'],source_sha256=s['source_sha256'],source_text=english,text=text,rationale=rationale,
            human_reviewed=False,independent_review=None,release_eligible=False))
    dest=BASE/'authored/map_places422.json'
    protected_write(dest,json.dumps(dict(policy='individual_manual_proposals_not_approved',drafts=rows),ensure_ascii=False,indent=2)+'\n')
    terms=json.loads((BASE/'terminology.json').read_text(encoding='utf8'));approved=copy.deepcopy(terms['approved_decisions']);ds=[]
    before={e['id']:serialized([e]) for e in es}
    for i,(spec,row) in enumerate(zip(DRAFTS,rows)):
        key,index,english,text,rationale=spec;e=next(e for e in es if e['id']==row['source_id'])
        assert e['state']=='untranslated' and not e['decision_ids']
        did=f'working422:static:{key}'
        ds.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
            wording_ref=dict(path=dest.relative_to(ROOT).as_posix(),sha256=digest(dest.read_bytes()),json_pointer=f'/drafts/{i}/text'),
            applicability=dict(revision='ULKS46015-v1.01',context='map_places421',write_scope=f'Exact static{key} record;no global rename'),
            rationale=rationale,semantic_impact='Proper-name pronunciation/lore/geography remain human review;numbered levels preserved.',
            state='in_progress',approval=None,distribution_eligible=False,independent_semantic_review=None,
            mechanical_evidence=['qa/reports/map_places_stage421_context.json']))
        e.update(state='in_progress',context_id='map_places421',current_working_decision=did);e['decision_ids'].append(did)
        terms['candidate_decisions'].append(dict(id=f'term-map-{key}-422',source_referent=english,candidate_wording_decision_ref=did,
            applicability=f'Exact static{key} Map title;no approval inherited from quest drafts',state='unresolved',approval=None,evidence=['qa/reports/map_places_stage421_context.json']))
    targets={r['source_id'] for r in rows}
    assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in targets)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3662,needs_human_review=301,in_progress=10)
    assert terms['approved_decisions']==approved
    protected_write(BASE/'decisions_422.jsonl',serialized(ds));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8');save_json(BASE/'terminology.json',terms)
    save_json(ROOT/'qa/reports/map_places_stage422_drafts.json',dict(status='PASS_422_SEVEN_INDIVIDUAL_MAP_DRAFTS',authored=311,selected=301,unselected=10,decisions=536,previous304_unchanged=True,approved_terms_unchanged=True,release_eligible=False))
    print('PASS422 authored311/selected301/pending10')

def preflight():
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};rows=json.loads((BASE/'authored/map_places422.json').read_text(encoding='utf8'))['drafts'];positive=[];negative=[]
    for spec,row in zip(DRAFTS,rows):
        r=dict(key=spec[0],source_text=row['source_text'],text=row['text']);validate(r,book);positive.append(r['key'])
        for label,mut in [('wrong_source',dict(source_text=r['source_text']+'!')),('embedded_NUL',dict(text=r['text']+'\0')),('newline',dict(text=r['text']+'\n')),('invented_control',dict(text=r['text']+'[p]'))]:
            try: validate(dict(r,**mut),book)
            except (AssertionError,ValueError):negative.append(dict(key=r['key'],rejected=label))
            else:raise AssertionError('Accepted invalid Map label')
    save_json(ROOT/'qa/reports/map_places_stage423_preflight.json',dict(status='PASS_423_SEVEN_EXACT_SOURCE_CODEC_NAMES',positive_keys=positive,negative_cases=negative,human_approval=False,release_eligible=False))
    print('PASS423 seven positives/28 rejection checks')

def select():
    assert json.loads((ROOT/'qa/reports/map_places_stage423_preflight.json').read_text(encoding='utf8'))['status']=='PASS_423_SEVEN_EXACT_SOURCE_CODEC_NAMES'
    ds=decisions();assert len(ds)==536
    prior=ROOT/'config/development_gorgein410.json';assert digest(prior.read_bytes())==OLD_CONFIG_SHA
    cfg=copy.deepcopy(json.loads(prior.read_text(encoding='utf8')));es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es}
    snap=ROOT/'qa/ssot/20261019_424_before_map_selection';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',prior]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    out=[];book={'mapping':{c:None for c in range(0xac00,0xd7a4)}}
    for key,_,english,_,_ in DRAFTS:
        s=source(key);e=next(e for e in es if e['id']==s['id']);old=ds[f'working422:static:{key}']
        assert e['state']=='in_progress' and e['decision_ids']==[old['id']] and e['development_diagnostic_selection'] is None
        r=dict(key=key,source_text=english,text=resolve(old));validate(r,book);cfg['static_overrides'].append(r)
        did=f'development424:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=old['wording_ref'],broader_decision_id=old['id'],
            applicability=old['applicability'],rationale='Source421/manual422/preflight423;unchanged development value for native Map QA.',semantic_impact=old['semantic_impact'],
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None,
            mechanical_evidence=['qa/reports/map_places_stage421_context.json','qa/reports/map_places_stage422_drafts.json','qa/reports/map_places_stage423_preflight.json']))
        e['decision_ids'].append(did);e.update(state='needs_human_review',development_diagnostic_selection=did)
    targets={r['source_id'] for r in out};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in targets)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3662,needs_human_review=308,in_progress=3)
    dest=ROOT/'config/development_map_places424.json';protected_write(dest,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    protected_write(BASE/'decisions_424.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8')
    save_json(ROOT/'qa/reports/map_places_stage424_selection.json',dict(status='PASS_424_SEVEN_UNCHANGED_DEVELOPMENT_MAP_SELECTIONS',authored=311,selected=308,unselected=3,decisions=543,
        config_sha256=digest(dest.read_bytes()),approved_terms=1,approved_translations=0,release_eligible=False))
    print('PASS424 authored311/selected308/pending3')

if __name__=='__main__':
    import sys
    dict(context=context,draft=draft,preflight=preflight,select=select)[sys.argv[1]]()

"""Four source-bound item/actor names;u16 fields,not misleading u32 comparisons."""
import copy,json,struct,unicodedata
from collections import Counter
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from allegrex_profile import Profile
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from map_places421 import decisions
BASE=ROOT/'workspace/translation'
DRAFTS=[
 (2263,5,2039,84,'Druidic Wreath','드루이드 화환','Exact2480 quest object name;retain distinction from2483 Wreath of Eternity,without asserting separate items.'),
 (3001,2,150,112,'Marrowtusk','매로터스크','Named Wallowpit warrior in2464/2465;provisional transliteration matches current quest draft.'),
 (766,2,126,112,'Krelgaak Snoutrott','크렐가크 스나우트롯','Exact Snoutrott leader in2465/2466/2467;preserve full individual and tribe/family wording.'),
 (776,2,236,112,'Matron Skulkgra','여족장 스컬크그라','Matron leadership title follows2472/2476 context;source portrait tag PI_MatronSkulgra remains untouched.')
]
KEYS=[s[0] for s in DRAFTS]
SPANS=[('item_title_producer',0x6ff94,0x70180),('item_title_consumer',0x274d0,0x275e0),
 ('actor_hash_to_table2_row',0x5c520,0x5c590),('actor_row_install',0x3b49c,0x3b500),
 ('actor_name_load',0x20d30,0x20d78),('target_name_draw',0x3834c,0x383cc)]

def source(key):
    rows=[s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='static' and s['key']==key];assert len(rows)==1
    return rows[0]

def validate(r,book,encoder=encode_unicode,decoder=decode_unicode):
    assert set(r)=={'key','source_text','text'}
    key,table,row,stride,english,_,_=next(x for x in DRAFTS if x[0]==r['key'])
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,table*8);assert row<n and struct.unpack_from('<H',db,off+row*stride)[0]==key
    if table==2:assert db[off+row*stride+2:off+row*stride+4]==b'\xcc\xcc'
    s=source(key);raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text']==english and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    enc=encoder(t,book).encode('utf8');assert decoder(enc.decode('utf8'),book)==t
    assert len(enc)+1<=250 # conservative item-owned UTF8 bound;not a claim every actor consumer uses250.
    return enc

def context():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_430_checkpoint/entries.jsonl').read_bytes()
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    latest=(ROOT/'workspace/runtime/map_places_425/disc/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes()
    out=ROOT/'workspace/analysis/names432';out.mkdir(parents=True,exist_ok=True);windows=[]
    for name,a,z in SPANS:
        raw=boot[128+a:128+z];assert raw==latest[128+a:128+z]
        rows=Profile().verify_roundtrip(raw,a,out,name)
        (out/(name+'.listing.txt')).write_text(''.join(f'{r["pc"]:08X} {r["assembly"]}\n' for r in rows),encoding='utf8')
        windows.append(dict(name=name,start=a,end=z,sha256=digest(raw),roundtrip_instructions=len(rows),latest425_equal=True))
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();rows=[]
    for key,table,row,stride,english,_,_ in DRAFTS:
        s=source(key);assert s['source_text']==english and es[s['id']]['state']=='untranslated'
        off,n=struct.unpack_from('<II',db,table*8);raw=db[off+row*stride:off+(row+1)*stride];assert struct.unpack_from('<H',raw)[0]==key
        matches=[];query=english.replace('Matron ','')
        for x in lines(BASE/'baseline/source_entries.jsonl'):
            if query.casefold() not in x['source_text'].casefold():continue
            e=es[x['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision')
            matches.append(dict(source=x,decision_ref=did,current_draft=resolve(ds[did]) if did else None))
        rows.append(dict(source=s,table=table,row=row,stride=stride,field=0,width=2,complete_row_hex=raw.hex(),row_sha256=digest(raw),
            field2_padding_hex=raw[2:4].hex(),actor_hash=f'{struct.unpack_from("<I",raw,4)[0]:08x}' if table==2 else None,matches=matches))
    packet=BASE/'packets/names432';packet.mkdir(parents=True,exist_ok=True)
    protected_write(packet/'contexts.json',json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    protected_write(packet/'REVIEW.md','''# 드루이드 화환·고르진 인물 이름4개 — 432

원본T4 table5행2039의u16필드0은2263이고 table2행150/126/236의u16필드0은3001/766/776이다. table2필드2의CCCC패딩 때문에 이름 번호를u32 전체와 비교하면 일치하지 않는다. 앞선u32 부정 검색은 그 범위의 사실일 뿐 미사용 근거가 아니다.

아이템 이름은6FF94의s0+0 아이템 행 포인터→lhu필드0→DA634→UTF16 이름→DA478의$i 소유250바이트UTF8 버퍼→원본2098/2099/2108/3080 조합이다.097의단검/바지 실증은 동일원본코드의 이 경로를 뒷받침하지만 화환 실물 획득·착용·보상은 입증하지 않는다.

배우 이름은5C520의hash검색/stride112→table2행,3B4E8의객체+1D50 보관,20D5C/3835C의해당포인터→lhu필드0→705DC→문자열복사→383AC/C9850표시로 연결된다.기계어 각범위를 원본왕복·현재425동일성으로 검증했다. UI 도달과 폭은 신규 실행검증 과제다.

이름은 기존 퀘스트 초안과 개별 대조하고 아직 미승인인 개발용 후보로 유지한다. Druidic Wreath와Wreath of Eternity의 원문 호칭 차이를 임의로 없애지 않는다. Matron은여족장으로 쓰며 원문 초상화 태그PI_MatronSkulgra를 이름Skulkgra에 맞춰 고치지 않는다. 자연전투·사망·퀘스트완료·보상·명칭승인은 별도다.
''')
    save_json(ROOT/'qa/reports/names_stage432_context.json',dict(status='PASS_432_FOUR_TYPED_U16_NAME_FIELDS_AND_STATIC_CONSUMERS',keys=KEYS,rows=[dict(key=r['source']['key'],table=r['table'],row=r['row'],width=2) for r in rows],windows=windows,
        prior_u32_negative_search_not_unused_proof=True,source_game_SSOT_changes=0,new_runtime=False,release_eligible=False))
    print('PASS432 item2263/table5row2039 and actor3001/766/776 table2row150/126/236,u16 fields')

def draft():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_430_checkpoint/entries.jsonl').read_bytes();assert len(decisions())==543
    assert json.loads((ROOT/'qa/reports/names_stage432_context.json').read_text(encoding='utf8'))['keys']==KEYS
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};terms=json.loads((BASE/'terminology.json').read_text(encoding='utf8'));approved=copy.deepcopy(terms['approved_decisions'])
    snap=ROOT/'qa/ssot/20261019_433_before_names';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',ROOT/'config/development_map_places424.json']:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};rows=[]
    for key,table,row,stride,english,text,rationale in DRAFTS:
        validate(dict(key=key,source_text=english,text=text),book);s=source(key)
        rows.append(dict(source_id=s['id'],source_sha256=s['source_sha256'],source_text=english,text=text,rationale=rationale,human_reviewed=False,release_eligible=False))
    dest=BASE/'authored/names433.json';protected_write(dest,json.dumps(dict(policy='individual_manual_development_candidates',drafts=rows),ensure_ascii=False,indent=2)+'\n');out=[]
    for i,(spec,r) in enumerate(zip(DRAFTS,rows)):
        key=spec[0];e=next(e for e in es if e['id']==r['source_id']);assert e['state']=='untranslated' and not e['decision_ids'];did=f'working433:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=dest.relative_to(ROOT).as_posix(),sha256=digest(dest.read_bytes()),json_pointer=f'/drafts/{i}/text'),
            applicability=dict(revision='ULKS46015-v1.01',context='names432',write_scope=f'Exact static{key} record;no prose replacement'),rationale=r['rationale'],
            semantic_impact='Name pronunciation/title/lore remain human review;other mentions need same-referent evidence.',state='in_progress',approval=None,distribution_eligible=False,independent_semantic_review=None,
            mechanical_evidence=['qa/reports/names_stage432_context.json']))
        e.update(state='in_progress',context_id='names432',current_working_decision=did);e['decision_ids'].append(did)
        terms['candidate_decisions'].append(dict(id=f'term-name-{key}-433',source_referent=spec[4],candidate_wording_decision_ref=did,applicability=f'Exact static{key} name;not human-approved',state='unresolved',approval=None,evidence=['qa/reports/names_stage432_context.json']))
    ids={r['source_id'] for r in rows};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in ids)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3658,needs_human_review=308,in_progress=7) and terms['approved_decisions']==approved
    protected_write(BASE/'decisions_433.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8');save_json(BASE/'terminology.json',terms)
    save_json(ROOT/'qa/reports/names_stage433_drafts.json',dict(status='PASS_433_FOUR_INDIVIDUAL_NAME_DRAFTS',authored=315,selected=308,unselected=7,decisions=547,previous311_wordings_unchanged=True,release_eligible=False))
    print('PASS433 authored315/selected308/pending7')

def preflight():
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};rows=json.loads((BASE/'authored/names433.json').read_text(encoding='utf8'))['drafts'];neg=[]
    for spec,row in zip(DRAFTS,rows):
        r=dict(key=spec[0],source_text=row['source_text'],text=row['text']);validate(r,book)
        for name,change in [('wrong_source',dict(source_text=r['source_text']+'!')),('NUL',dict(text=r['text']+'\0')),('newline',dict(text=r['text']+'\n')),('resource_tag',dict(text=r['text']+'[p]')),('owned_buffer_overflow',dict(text='x'*250))]:
            try:validate(dict(r,**change),book)
            except (AssertionError,ValueError):neg.append(dict(key=r['key'],rejected=name))
            else:raise AssertionError('Invalid name accepted')
    save_json(ROOT/'qa/reports/names_stage434_preflight.json',dict(status='PASS_434_FOUR_SOURCE_BOUND_NAMES_CODEC_AND_CAPACITY',keys=KEYS,rejected_cases=neg,release_eligible=False))
    print('PASS434 four positives/20 negative checks')

def select():
    assert json.loads((ROOT/'qa/reports/names_stage434_preflight.json').read_text(encoding='utf8'))['keys']==KEYS;ds=decisions();assert len(ds)==547
    prior=ROOT/'config/development_map_places424.json';assert digest(prior.read_bytes())=='6b4110d2604adea8fcd115555e0909c89dbcff1a72db8cc9f3a601289a14dd43'
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};cfg=copy.deepcopy(json.loads(prior.read_text(encoding='utf8')));out=[]
    snap=ROOT/'qa/ssot/20261019_435_before_names_selection';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',prior]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    for spec in DRAFTS:
        key=spec[0];s=source(key);e=next(e for e in es if e['id']==s['id']);old=ds[f'working433:static:{key}'];assert e['state']=='in_progress' and e['decision_ids']==[old['id']]
        cfg['static_overrides'].append(dict(key=key,source_text=spec[4],text=resolve(old)));did=f'development435:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=old['wording_ref'],broader_decision_id=old['id'],applicability=old['applicability'],
            rationale='Manual433/source432/preflight434;unchanged technical development selection;runtime pending.',semantic_impact=old['semantic_impact'],state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None,
            mechanical_evidence=['qa/reports/names_stage432_context.json','qa/reports/names_stage433_drafts.json','qa/reports/names_stage434_preflight.json']))
        e['decision_ids'].append(did);e.update(state='needs_human_review',development_diagnostic_selection=did)
    ids={r['source_id'] for r in out};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in ids)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3658,needs_human_review=312,in_progress=3)
    dest=ROOT/'config/development_names435.json';protected_write(dest,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/'decisions_435.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8')
    save_json(ROOT/'qa/reports/names_stage435_selection.json',dict(status='PASS_435_FOUR_UNCHANGED_NAME_DEVELOPMENT_SELECTIONS',authored=315,selected=312,unselected=3,decisions=551,config_sha256=digest(dest.read_bytes()),release_eligible=False))
    print('PASS435 authored315/selected312/pending3')

if __name__=='__main__':
    import sys
    dict(context=context,draft=draft,preflight=preflight,select=select)[sys.argv[1]]()

"""Eight individual names tied to Repair Gates;source u16 fields and consumer paths."""
import copy,json,re,struct,unicodedata
from collections import Counter
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from allegrex_profile import Profile
from map_places421 import decisions
BASE=ROOT/'workspace/translation'
DRAFTS=[
 (61,16,15,2,'Shattercove West','섀터코브 서부','Source2521 explicitly crosses West then East;retain directional distinction.'),
 (74,16,26,2,'Shattercove East','섀터코브 동부','Same named cove as West;do not collapse two table16 rows.'),
 (75,16,27,2,'Splinterfull Woods','스플린터풀 숲','Existing2521/2530 route anchor;provisional pronunciation.'),
 (76,16,29,2,'Dreadwind Moor','드레드윈드 황야','Existing2521 provisional place name;moor rendered without inventing wetland mechanics.'),
 (77,16,33,2,'Waning Wastes','쇠락의 황무지','2521 places Whispering Chasm here;individually retained descriptive proposal.'),
 (83,16,46,2,'Whispering Chasm','속삭이는 심연','Source2521/2522 identifies the siren site;existing current draft candidate.'),
 (2523,5,2037,84,'Containment Shard','봉인 조각','Source2521/2522/2524 identifies artifact recovered from Alyssia for acolyte attunement.'),
 (3198,2,193,112,'Alyssia the Hateful','증오의 알리시아','Exact source2521/2522 named siren and title;not an invented generic enemy label.')
]
KEYS=[r[0] for r in DRAFTS]
SPANS=[('Map_name_owner',0x2ce20,0x2ceb4),('Map_name_lookup',0x708b4,0x70900),('Map_name_pointer',0x130ee0,0x130f00),
 ('item_title_producer',0x6ff94,0x70180),('item_title_consumer',0x274d0,0x275e0),('actor_hash_lookup',0x5c520,0x5c590),
 ('actor_row_install',0x3b49c,0x3b500),('actor_name_load',0x20d30,0x20d78),('target_name_draw',0x3834c,0x383cc)]

def source(key):
    rows=[s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='static' and s['key']==key];assert len(rows)==1
    return rows[0]

def validate(r,book,encoder=encode_unicode,decoder=decode_unicode):
    assert set(r)=={'key','source_text','text'} and r['key'] in KEYS
    key,table,row,stride,english,_,_=next(s for s in DRAFTS if s[0]==r['key'])
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,table*8);assert row<n and struct.unpack_from('<H',db,off+row*stride)[0]==key
    if table==2:assert db[off+row*stride+2:off+row*stride+4]==bytes.fromhex('cccc')
    s=source(key);raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert s['source_text']==r['source_text']==english and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    enc=encoder(text,book).encode('utf8');assert decoder(enc.decode('utf8'),book)==text and len(enc)+1<=250
    return enc # conservative shared input limit;not an assertion all consumers own250 bytes.

def context():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_472_checkpoint/entries.jsonl').read_bytes()
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    latest=(ROOT/'workspace/runtime/repair_gates_465/disc/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes();out=ROOT/'workspace/analysis/repair_names474';out.mkdir(parents=True,exist_ok=True);windows=[]
    for name,a,z in SPANS:
        data=boot[128+a:128+z];assert data==latest[128+a:128+z];rs=Profile().verify_roundtrip(data,a,out,name)
        (out/(name+'.listing.txt')).write_text(''.join(f'{r["pc"]:08X} {r["assembly"]}\n' for r in rs),encoding='utf8')
        windows.append(dict(name=name,start=a,end=z,sha256=digest(data),instructions=len(rs),exact465_equal=True))
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();rows=[];book={'mapping':{c:None for c in range(0xac00,0xd7a4)}}
    for key,table,row,stride,english,text,why in DRAFTS:
        s=source(key);assert es[s['id']]['state']=='untranslated';validate(dict(key=key,source_text=english,text=text),book)
        off,n=struct.unpack_from('<II',db,table*8);raw=db[off+row*stride:off+(row+1)*stride];matches=[]
        for x in lines(BASE/'baseline/source_entries.jsonl'):
            if english.casefold() not in x['source_text'].casefold():continue
            e=es[x['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision')
            matches.append(dict(source=x,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
        rows.append(dict(source=s,table=table,row=row,stride=stride,field=0,width=2,complete_row_hex=raw.hex(),sha256=digest(raw),
            actor_hash=f'{struct.unpack_from("<I",raw,4)[0]:08x}' if table==2 else None,actor_HUD_guard=raw[0x5d] if table==2 else None,matches=matches))
    dest=BASE/'packets/repair_names474';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'contexts.json',json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    protected_write(dest/'REVIEW.md','''# 관문 수리 관련 이름8개 — 474

지도6개는 원본table16행15/26/27/29/33/46의 u16 이름 참조61/74/75/76/77/83이다.봉인 조각2523은table5행2037의 u16필드0,증오의 알리시아3198은table2행193의 u16필드0이다.인물 이름 뒤CCCC패딩을 u32 참조로 오인하지 않는다.전체 행과 원문span을 보존했다.

현재2521/2522/2524 원고에 쓰인 각 이름을 동일 원문 참조와 개별 대조한다.지도 지명·아이템·배우 이름은 다른 소비 경로다.Map은2CE20→708B4→130EE0의table16[index]→lhu→705DC→708E4→Map 제목이다.아이템은6FF94→DA634→DA478의$i 소유UTF8 버퍼→원래 조합,배우는정의table2→38360/705DC→383AC/C9850으로 연결된다.원본9코드구간을 왕복하고465 동일성을 확인한다.

새 실행에서는 Map 이름 폭/닫기/재열기,아이템 이름 정상 getter/소유버퍼 조합,배우 HUD 이름의 전체NUL/재조회/표시를 각각 확인해야 한다.다른 물체의 이름 참조 실험은 원래 섀터코브 방문·지형·알리시아 전투·봉인 조각 획득/조율/퀘스트 완료 증거가 아니다.이미 검증한427/439의 구성요소 방법은 재사용하되다른artifact 상태는 가져오지 않는다.새 이름은 인간 미승인 개발 후보로 남는다.
''')
    save_json(ROOT/'qa/reports/repair_names_stage474_context.json',dict(status='PASS_474_EIGHT_TYPED_U16_REPAIR_GATE_NAMES',keys=KEYS,rows=[dict(key=r['source']['key'],table=r['table'],row=r['row'],width=2) for r in rows],windows=windows,source_game_SSOT_changes=0,new_runtime=False,release_eligible=False))
    print('PASS474 exact8 names/9 original consumer windows')

def draft():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_472_checkpoint/entries.jsonl').read_bytes() and len(decisions())==587
    assert json.loads((ROOT/'qa/reports/repair_names_stage474_context.json').read_text(encoding='utf8'))['keys']==KEYS
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};terms=json.loads((BASE/'terminology.json').read_text(encoding='utf8'));approved=copy.deepcopy(terms['approved_decisions'])
    snap=ROOT/'qa/ssot/20261019_475_before_repair_names';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',ROOT/'config/development_gates464.json']:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};rows=[]
    for key,table,row,stride,english,text,why in DRAFTS:
        validate(dict(key=key,source_text=english,text=text),book);s=source(key)
        rows.append(dict(source_id=s['id'],source_sha256=s['source_sha256'],source_text=english,text=text,rationale=why,human_reviewed=False,release_eligible=False))
    dest=BASE/'authored/repair_names475.json';protected_write(dest,json.dumps(dict(policy='individual_manual_development_candidates',drafts=rows),ensure_ascii=False,indent=2)+'\n');out=[]
    for i,(spec,r) in enumerate(zip(DRAFTS,rows)):
        key=spec[0];e=next(e for e in es if e['id']==r['source_id']);assert e['state']=='untranslated' and not e['decision_ids'];did=f'working475:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=dest.relative_to(ROOT).as_posix(),sha256=digest(dest.read_bytes()),json_pointer=f'/drafts/{i}/text'),
            applicability=dict(revision='ULKS46015-v1.01',context='repair_names474',write_scope=f'Exact static{key} only;no global prose replacements'),rationale=r['rationale'],
            semantic_impact='Provisional place/item/person spelling and interpretation;human review and source-context approvals remain open.',state='in_progress',approval=None,distribution_eligible=False,independent_semantic_review=None,mechanical_evidence=['qa/reports/repair_names_stage474_context.json']))
        e.update(state='in_progress',context_id='repair_names474',current_working_decision=did);e['decision_ids'].append(did)
        terms['candidate_decisions'].append(dict(id=f'term-repair-name-{key}-475',source_referent=spec[4],candidate_wording_decision_ref=did,applicability=f'Exact static{key};not human-approved',state='unresolved',approval=None,evidence=['qa/reports/repair_names_stage474_context.json']))
    ids={r['source_id'] for r in rows};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in ids)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3633,needs_human_review=329,in_progress=11) and terms['approved_decisions']==approved
    protected_write(BASE/'decisions_475.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8');save_json(BASE/'terminology.json',terms)
    save_json(ROOT/'qa/reports/repair_names_stage475_drafts.json',dict(status='PASS_475_EIGHT_INDIVIDUAL_NAME_DRAFTS',authored=340,selected=329,unselected=11,decisions=595,previous332_wordings_unchanged=True,release_eligible=False))
    print('PASS475 authored340/selected329/pending11')

def preflight():
    rows=json.loads((BASE/'authored/repair_names475.json').read_text(encoding='utf8'))['drafts'];assert len(rows)==8
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};neg=[]
    for spec,row in zip(DRAFTS,rows):
        r=dict(key=spec[0],source_text=row['source_text'],text=row['text']);validate(r,book)
        for name,change in [('wrong_source',dict(source_text=r['source_text']+'!')),('NUL',dict(text=r['text']+'\0')),('newline',dict(text=r['text']+'\n')),('resource_tag',dict(text=r['text']+'[p]')),('conservative_input_overflow',dict(text='x'*250))]:
            try:validate(dict(r,**change),book)
            except (AssertionError,ValueError):neg.append(dict(key=r['key'],rejected=name))
            else:raise AssertionError('Invalid name accepted')
    save_json(ROOT/'qa/reports/repair_names_stage476_preflight.json',dict(status='PASS_476_EIGHT_SOURCE_BOUND_NAMES_CODEC_CAPACITY',keys=KEYS,rejected_cases=neg,release_eligible=False))
    print('PASS476 eight positives/40 negative cases')

def select():
    assert json.loads((ROOT/'qa/reports/repair_names_stage476_preflight.json').read_text(encoding='utf8'))['keys']==KEYS;ds=decisions();assert len(ds)==595
    prior=ROOT/'config/development_gates464.json';assert digest(prior.read_bytes())=='deeae9970fcf94291540214cf012cae56c6b3900d5bddee92cd77054c22973fb'
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};cfg=copy.deepcopy(json.loads(prior.read_text(encoding='utf8')));out=[]
    snap=ROOT/'qa/ssot/20261019_477_before_repair_names_selection';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',prior]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    for spec in DRAFTS:
        key=spec[0];s=source(key);e=next(e for e in es if e['id']==s['id']);old=ds[f'working475:static:{key}'];assert e['state']=='in_progress' and e['decision_ids']==[old['id']]
        cfg['static_overrides'].append(dict(key=key,source_text=spec[4],text=resolve(old)));did=f'development477:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=old['wording_ref'],broader_decision_id=old['id'],applicability=old['applicability'],
            rationale='Manual475/source474/preflight476;unchanged technical development selection;runtime pending.',semantic_impact=old['semantic_impact'],state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None,
            mechanical_evidence=['qa/reports/repair_names_stage474_context.json','qa/reports/repair_names_stage475_drafts.json','qa/reports/repair_names_stage476_preflight.json']))
        e['decision_ids'].append(did);e.update(state='needs_human_review',development_diagnostic_selection=did)
    ids={r['source_id'] for r in out};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in ids)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3633,needs_human_review=337,in_progress=3)
    dest=ROOT/'config/development_repair_names477.json';protected_write(dest,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/'decisions_477.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8')
    save_json(ROOT/'qa/reports/repair_names_stage477_selection.json',dict(status='PASS_477_EIGHT_UNCHANGED_NAME_DEVELOPMENT_SELECTIONS',authored=340,selected=337,unselected=3,decisions=603,config_sha256=digest(dest.read_bytes()),release_eligible=False))
    print('PASS477 authored340/selected337/pending3')

if __name__=='__main__':
    import sys
    dict(context=context,draft=draft,preflight=preflight,select=select)[sys.argv[1]]()

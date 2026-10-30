"""Four source-linked names;book item2543 remains a separate unresolved consumer."""
import copy,json,struct,unicodedata
from collections import Counter
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from allegrex_profile import Profile
from map_places421 import decisions
from repair_names474 import SPANS
BASE=ROOT/'workspace/translation'
DRAFTS=[
 (69,16,35,2,'Necrosis Citadel Level 1','네크로시스 성채 1층','Current2542/2545 place spelling;retain original level1 and established Wallowpit floor format.'),
 (68,16,36,2,'Necrosis Citadel Level 2','네크로시스 성채 2층','Same source place,distinct level2/table16 row.'),
 (67,16,37,2,'Necrosis Citadel Level 3','네크로시스 성채 3층','Same source place,distinct level3/table16 row.'),
 (3041,2,156,112,'The Nethereye','네더아이','Exact source2550/2542/2544/2545/2546 name;retain established current provisional spelling,source HUD guard1.')
]
KEYS=[r[0] for r in DRAFTS]

def source(key):
    rs=[s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='static' and s['key']==key];assert len(rs)==1;return rs[0]

def validate(r,book,encoder=encode_unicode,decoder=decode_unicode):
    assert set(r)=={'key','source_text','text'} and r['key'] in KEYS
    key,table,row,stride,english,_,_=next(s for s in DRAFTS if s[0]==r['key'])
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,table*8);assert row<n and struct.unpack_from('<H',db,off+row*stride)[0]==key
    if table==2:assert db[off+row*stride+2:off+row*stride+4]==bytes.fromhex('cccc') and db[off+row*stride+0x5d]==1
    s=source(key);raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert s['source_text']==r['source_text']==english and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    enc=encoder(text,book).encode('utf8');assert decoder(enc.decode('utf8'),book)==text and len(enc)+1<=250
    return enc

def context():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_515_checkpoint/entries.jsonl').read_bytes()
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    latest=(ROOT/'workspace/runtime/threat_quests_508/disc/PSP_GAME/SYSDIR/EBOOT.BIN').read_bytes();out=ROOT/'workspace/analysis/threat_names517';out.mkdir(parents=True,exist_ok=True);windows=[]
    spans=[r for r in SPANS if not r[0].startswith('item_')]
    for name,a,z in spans:
        data=boot[128+a:128+z];assert data==latest[128+a:128+z];rs=Profile().verify_roundtrip(data,a,out,name)
        (out/(name+'.listing.txt')).write_text(''.join(f'{r["pc"]:08X} {r["assembly"]}\n' for r in rs),encoding='utf8');windows.append(dict(name=name,start=a,end=z,sha256=digest(data),instructions=len(rs),exact508_equal=True))
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();rows=[];book={'mapping':{c:None for c in range(0xac00,0xd7a4)}}
    for key,table,row,stride,english,text,why in DRAFTS:
        s=source(key);assert es[s['id']]['state']=='untranslated';validate(dict(key=key,source_text=english,text=text),book)
        off,n=struct.unpack_from('<II',db,table*8);raw=db[off+row*stride:off+(row+1)*stride];matches=[]
        query='Necrosis Citadel' if table==16 else 'Nethereye'
        for x in lines(BASE/'baseline/source_entries.jsonl'):
            if query.casefold() not in x['source_text'].casefold():continue
            e=es[x['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision');matches.append(dict(source=x,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
        rows.append(dict(source=s,table=table,row=row,stride=stride,field=0,width=2,complete_row_hex=raw.hex(),sha256=digest(raw),actor_hash=f'{struct.unpack_from("<I",raw,4)[0]:08x}' if table==2 else None,actor_HUD_guard=raw[0x5d] if table==2 else None,matches=matches))
    off,n=struct.unpack_from('<II',db,40);matches=[i for i in range(n) if struct.unpack_from('<H',db,off+i*84)[0]==2543];assert matches==[]
    dest=BASE/'packets/threat_names517';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'contexts.json',json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    protected_write(dest/'separate_tome2543.json',json.dumps(dict(source=source(2543),typed_scan=dict(table=5,stride=84,field=0,width=2,rows=n,matches=matches),disposition='Consumer unresolved;not unused proof;not in four-name cohort.'),ensure_ascii=False,indent=2)+'\n')
    save_json(ROOT/'qa/reports/threat_names_stage517_context.json',dict(status='PASS_517_FOUR_TYPED_U16_THREAT_NAMES',keys=KEYS,rows=[dict(key=r['source']['key'],table=r['table'],row=r['row'],width=2) for r in rows],windows=windows,source_game_SSOT_changes=0,unresolved_item2543_not_unused_claim=True,new_runtime=False,release_eligible=False));print('PASS517 four names/seven original consumer windows')

def draft():
    assert (BASE/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_515_checkpoint/entries.jsonl').read_bytes() and len(decisions())==637
    assert json.loads((ROOT/'qa/reports/threat_names_stage517_context.json').read_text(encoding='utf8'))['keys']==KEYS
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};terms=json.loads((BASE/'terminology.json').read_text(encoding='utf8'));approved=copy.deepcopy(terms['approved_decisions'])
    snap=ROOT/'qa/ssot/20261019_518_before_threat_names';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',ROOT/'config/development_threat507.json']:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};rows=[]
    for key,table,row,stride,english,text,why in DRAFTS:
        validate(dict(key=key,source_text=english,text=text),book);s=source(key);rows.append(dict(source_id=s['id'],source_sha256=s['source_sha256'],source_text=english,text=text,rationale=why,human_reviewed=False,release_eligible=False))
    ds=decisions();prior_chars=set()
    for e in es:
        if e['state']=='untranslated':continue
        did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1];prior_chars.update(c for c in resolve(ds[did]) if 0xac00<=ord(c)<=0xd7a3)
    assert len(prior_chars)==756 and len(prior_chars|{c for r in rows for c in r['text'] if 0xac00<=ord(c)<=0xd7a3})==756
    dest=BASE/'authored/threat_names518.json';protected_write(dest,json.dumps(dict(policy='individual_manual_development_candidates',drafts=rows),ensure_ascii=False,indent=2)+'\n');out=[]
    for i,(spec,r) in enumerate(zip(DRAFTS,rows)):
        key=spec[0];e=next(e for e in es if e['id']==r['source_id']);assert e['state']=='untranslated' and not e['decision_ids'];did=f'working518:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=dest.relative_to(ROOT).as_posix(),sha256=digest(dest.read_bytes()),json_pointer=f'/drafts/{i}/text'),applicability=dict(revision='ULKS46015-v1.01',context='threat_names517',write_scope=f'Exact static{key} only;no global prose replacements'),rationale=r['rationale'],semantic_impact='Provisional names retain currently selected quest wording;human terminology/voice approval pending.',state='in_progress',approval=None,distribution_eligible=False,independent_semantic_review=None,mechanical_evidence=['qa/reports/threat_names_stage517_context.json']))
        e.update(state='in_progress',context_id='threat_names517',current_working_decision=did);e['decision_ids'].append(did)
        terms['candidate_decisions'].append(dict(id=f'term-threat-name-{key}-518',source_referent=spec[4],candidate_wording_decision_ref=did,applicability=f'Exact static{key};not human-approved',state='unresolved',approval=None,evidence=['qa/reports/threat_names_stage517_context.json']))
    ids={r['source_id'] for r in rows};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in ids)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3612,needs_human_review=354,in_progress=7) and terms['approved_decisions']==approved
    protected_write(BASE/'decisions_518.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8');save_json(BASE/'terminology.json',terms)
    save_json(ROOT/'qa/reports/threat_names_stage518_drafts.json',dict(status='PASS_518_FOUR_INDIVIDUAL_NAME_DRAFTS',authored=361,selected=354,unselected=7,decisions=641,previous357_wordings_unchanged=True,modern_Hangul_unique_demand=756,release_eligible=False));print('PASS518 authored361/selected354/pending7')

def preflight():
    rows=json.loads((BASE/'authored/threat_names518.json').read_text(encoding='utf8'))['drafts'];assert len(rows)==4
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};neg=[]
    for spec,row in zip(DRAFTS,rows):
        r=dict(key=spec[0],source_text=row['source_text'],text=row['text']);validate(r,book)
        for name,change in [('wrong_source',dict(source_text=r['source_text']+'!')),('NUL',dict(text=r['text']+'\0')),('newline',dict(text=r['text']+'\n')),('resource_tag',dict(text=r['text']+'[p]')),('conservative_input_overflow',dict(text='x'*250))]:
            try:validate(dict(r,**change),book)
            except (AssertionError,ValueError):neg.append(dict(key=r['key'],rejected=name))
            else:raise AssertionError('Invalid name accepted')
    save_json(ROOT/'qa/reports/threat_names_stage519_preflight.json',dict(status='PASS_519_FOUR_SOURCE_BOUND_NAMES_CODEC_CAPACITY',keys=KEYS,rejected_cases=neg,release_eligible=False));print('PASS519 four positives/20 rejections')

def select():
    assert json.loads((ROOT/'qa/reports/threat_names_stage519_preflight.json').read_text(encoding='utf8'))['keys']==KEYS;ds=decisions();assert len(ds)==641
    prior=ROOT/'config/development_threat507.json';assert digest(prior.read_bytes())=='4bad6a747b4759f11f280abea2d3d4c0ca6dd79b3d20dfd2aac469665a5489a9'
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};cfg=copy.deepcopy(json.loads(prior.read_text(encoding='utf8')));out=[]
    snap=ROOT/'qa/ssot/20261019_520_before_threat_names_selection';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',prior]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    for spec in DRAFTS:
        key=spec[0];s=source(key);e=next(e for e in es if e['id']==s['id']);old=ds[f'working518:static:{key}'];assert e['state']=='in_progress' and e['decision_ids']==[old['id']]
        cfg['static_overrides'].append(dict(key=key,source_text=spec[4],text=resolve(old)));did=f'development520:static:{key}'
        out.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=old['wording_ref'],broader_decision_id=old['id'],applicability=old['applicability'],rationale='Manual518/source517/preflight519;unchanged technical development selection;runtime pending.',semantic_impact=old['semantic_impact'],state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None,mechanical_evidence=['qa/reports/threat_names_stage517_context.json','qa/reports/threat_names_stage518_drafts.json','qa/reports/threat_names_stage519_preflight.json']))
        e['decision_ids'].append(did);e.update(state='needs_human_review',development_diagnostic_selection=did)
    ids={r['source_id'] for r in out};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in ids)
    assert dict(Counter(e['state'] for e in es))==dict(untranslated=3612,needs_human_review=358,in_progress=3)
    dest=ROOT/'config/development_threat_names520.json';protected_write(dest,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/'decisions_520.jsonl',serialized(out));(BASE/'entries.jsonl').write_text(serialized(es),encoding='utf8')
    save_json(ROOT/'qa/reports/threat_names_stage520_selection.json',dict(status='PASS_520_FOUR_UNCHANGED_NAME_DEVELOPMENT_SELECTIONS',authored=361,selected=358,unselected=3,decisions=645,config_sha256=digest(dest.read_bytes()),release_eligible=False));print('PASS520 authored361/selected358/pending3')

if __name__=='__main__':
    import sys
    dict(context=context,draft=draft,preflight=preflight,select=select)[sys.argv[1]]()

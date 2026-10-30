"""Two source units split into NPC speech and separately authored Korean Book roles."""
import argparse,copy,json,re,struct,unicodedata
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from npc_book_aliases_20261024 import PINS,NAME as PARENT
from npc_exception_drafts_20261020 import DRAFTS
from unicode_codec042 import encode_unicode,decode_unicode

NAME='book_role_split_20261024';BASE=ROOT/'workspace/translation';PREFIX='PSP_GAME/USRDIR/locale/'
CONFIG=f'development_{NAME}.json'
TITLE='영웅을 향한 불신'
BODY='나한테 말할 때는 웃어라, 꼬맹아! 앨리스가 보고 있잖아. 내가 좋은 인상을 주도록 도와주면 멀쩡히 걸어 나가게 해 주지, 알아들었냐?'

def original_cases():
    report=json.loads((ROOT/'qa/reports/npc_book_aliases_20261024_static.json').read_text(encoding='utf-8'))
    return {x['key']:x for x in report['records']}

def roles():
    cases=original_cases()
    return [dict(source_key=k,key=k,role='npc_dialogue',text=DRAFTS[k],source_text=cases[k]['source']['source_text'],
                 references=[r for r in cases[k]['references'] if r['table']==13]) for k in [2334,2335]]+[
        dict(source_key=2334,key=4009,role='quest_title',text=TITLE,source_text=cases[2334]['source']['source_text'],references=[dict(table=15,row=81,field=40,width=4)]),
        dict(source_key=2335,key=4010,role='Book_body',text=BODY,source_text=cases[2335]['source']['source_text'],references=[dict(table=15,row=81,field=24,width=4)])]

def validate_role(r):
    wanted=next(x for x in roles() if x['key']==r['key']);assert r==wanted
    text=r['text'];assert text==unicodedata.normalize('NFC',text) and '\0' not in text
    book={'mapping':{c:None for c in range(0xac00,0xd7a4)}}
    assert decode_unicode(encode_unicode(text,book),book)==text
    assert len(text.encode('utf-8'))<65536 and len(text.encode('utf-16le'))//2<2048
    if r['role']=='npc_dialogue':
        assert text.startswith('[i_PI_BronMorris]') and text.endswith('\r\n*BUG THIS*')
        assert text.count('*B')==r['source_text'].count('*B')==1
    else:
        assert not any(c in text for c in '[]*$\r\n')
        assert len(text)<=12 if r['role']=='quest_title' else True

def derive_split(cfg):
    assert set(cfg)=={'schema_version','policy','parent_config','parent_config_sha256','roles','choice_path','choice_sha256'}
    assert cfg['schema_version']==9 and cfg['policy']=='development_poc_non_distributable' and cfg['roles']==roles()
    for r in cfg['roles']:validate_role(r)
    choice=ROOT/cfg['choice_path'];assert digest(choice.read_bytes())==cfg['choice_sha256']
    human=json.loads(choice.read_text(encoding='utf-8'));assert human['user_answer']=='그럼 분리해서 번역하자' and human['both_NPC_and_Book_Korean']
    parentpath=ROOT/'config'/cfg['parent_config'];assert cfg['parent_config']==f'development_{PARENT}.json'
    assert digest(parentpath.read_bytes())==cfg['parent_config_sha256']==PINS['config_sha256']
    parent=json.loads(parentpath.read_text(encoding='utf-8'))
    from build_font_folder import derive
    plan,outputs=derive('unicode_hangul_alias_fallback',parent)
    plan=copy.deepcopy(plan);outputs=dict(outputs)
    def prior(path):return outputs.get(path,(ROOT/'extracted/disc'/path).read_bytes())
    directory=prior(PREFIX+'en_us_dir.dat');eng=prior(PREFIX+'en_us_eng.dat');trans=prior(PREFIX+'en_us_trans.dat')
    rows=[struct.unpack_from('<IIIHHHH',directory,i) for i in range(0,len(directory),20)]
    assert len(rows)==858 and [r[0] for r in rows]==sorted(r[0] for r in rows)
    ss=lines(BASE/'baseline/source_entries.jsonl');assert {4009,4010}.isdisjoint(x['key'] for x in ss if x['bank'] in ['static','trans'])
    changes={r['key']:r for r in cfg['roles']};newtrans=bytearray();newrows=[]
    cases=original_cases()
    for row in rows:
        key,ep,tp,el,tl,flag,res=row;raw=trans[tp:tp+tl]
        if key in [2334,2335]:
            assert raw.hex()==cases[key]['source']['source_hex'];raw=changes[key]['text'].encode('utf-8')
        newrows.append((key,ep,len(newtrans),el,len(raw),flag,res));newtrans.extend(raw)
    for sourcekey,newkey in [(2334,4009),(2335,4010)]:
        old=next(r for r in rows if r[0]==sourcekey);source=eng[old[1]:old[1]+old[3]]
        assert source.hex()==cases[sourcekey]['source']['source_hex']
        raw=changes[newkey]['text'].encode('utf-8')
        newrows.append((newkey,len(eng),len(newtrans),len(source),len(raw),old[5],old[6]));eng+=source;newtrans.extend(raw)
    newdir=b''.join(struct.pack('<IIIHHHH',*r) for r in newrows)
    dbpath='PSP_GAME/USRDIR/res/gam_db_T4';db=bytearray(prior(dbpath));beforedb=bytes(db);patches=[]
    for sourcekey,key,field in [(2334,4009,40),(2335,4010,24)]:
        off=342680+81*56+field;assert struct.unpack_from('<I',db,off)[0]==sourcekey
        struct.pack_into('<I',db,off,key);patches.append(dict(offset=off,before_key=sourcekey,after_key=key,size=4))
    expected=bytearray(beforedb)
    for p in patches:struct.pack_into('<I',expected,p['offset'],p['after_key'])
    assert db==expected
    mutations={PREFIX+'en_us_dir.dat':newdir,PREFIX+'en_us_eng.dat':eng,PREFIX+'en_us_trans.dat':bytes(newtrans),dbpath:bytes(db)}
    # Compose each final file from immutable source, replacing prior whole-file writers.
    plan['writes']=[w for w in plan['writes'] if w['path'] not in mutations]
    for path,final in mutations.items():
        source=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=final
        plan['writes'].append(dict(owner='Source-bound NPC/Book role split',path=path,offset=0,size=len(final),
            expected_sha256=digest(source),final_sha256=digest(final),source_size=len(source),
            derivation='Compose original parent translation recipe, two unchanged NPC drafts, two explicit Korean Book roles and exact row81 references.'))
    plan['writes'].sort(key=lambda x:(x['path'],x['offset']))
    plan['diagnostic_input']=cfg;plan['book_role_split']=dict(roles=cfg['roles'],directory_rows=860,DB_reference_patches=patches,
        inherited_original_selected=3538,new_original_selected=2,new_derived_Book_roles=2,
        Book_title_adaptation=True,Book_only_portrait_and_diagnostic_suffix_omitted=True,NPC_original_marker_effect_preserved=True,
        English_reference_payloads_preserved=True,all_other_original_trans_payloads_preserved=True)
    plan['font']['scope']='Development3538 inherited selections plus2 NPC source units and2 derived Korean Book roles. No release or full wording approval.'
    plan['allowed_changed_files']=sorted(outputs)
    # Final re-extraction verifies all four payloads and every inherited non-target payload.
    for row in newrows:
        k,ep,tp,el,tl,flag,res=row
        if k in changes:assert newtrans[tp:tp+tl]==changes[k]['text'].encode('utf-8')
        else:
            old=next(r for r in rows if r[0]==k);assert newtrans[tp:tp+tl]==trans[old[2]:old[2]+old[4]]
    return plan,outputs

def select():
    from npc_book_aliases_20261024 import fixed
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    fixed();es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4349
    for r in roles():validate_role(r)
    snapshot=ROOT/'qa/ssot/20261024_before_book_role_split';snapshot.mkdir(parents=True,exist_ok=True)
    parentpath=ROOT/f'config/development_{PARENT}.json'
    for path in [BASE/'entries.jsonl',BASE/'terminology.json',parentpath]:protected_write(snapshot/path.name,path.read_text(encoding='utf-8'))
    choice=dict(authority='user',date_local='2026-10-24',user_answer='그럼 분리해서 번역하자',both_NPC_and_Book_Korean=True,
        rejected_English_Book_preservation_proposal=True,scope='2334/2335 original NPC and row81 title/body only',
        agent_development_title_adaptation=TITLE,Book_only_portrait_metadata_omitted=True,Book_only_nonstory_diagnostic_suffix_omitted=True,
        source_English_and_prior_drafts_preserved=True,NPC_diagnostic_suffix_and_actor_effects_preserved=True,
        exact_wording_or_presentation_human_approval=False,full_translation_release_approval=False)
    cp=ROOT/'qa/reports/book_role_split_user_choice_20261024.json';protected_write(cp,json.dumps(choice,ensure_ascii=False,indent=2)+'\n')
    authored=BASE/f'authored/{NAME}.json';protected_write(authored,json.dumps(dict(policy='individual_manual_role_specific_development_drafts',roles=roles(),user_choice=choice),ensure_ascii=False,indent=2)+'\n')
    cfg=dict(schema_version=9,policy='development_poc_non_distributable',parent_config=parentpath.name,parent_config_sha256=PINS['config_sha256'],
        roles=roles(),choice_path=cp.relative_to(ROOT).as_posix(),choice_sha256=digest(cp.read_bytes()))
    before={e['id']:serialized([e]) for e in es};records=[]
    for i,r in enumerate(roles()):
        e=next(e for e in es if e['id']==original_cases()[r['source_key']]['source']['id'])
        did=f'development_{NAME}:{r["role"]}:{r["key"]}'
        if r['role']=='npc_dialogue':
            assert not e['development_diagnostic_selection'] and resolve(ds[e['current_working_decision']])==r['text']
            e['development_diagnostic_selection']=did;e['state']='needs_human_review';e['context_id']=NAME
        e['decision_ids'].append(did)
        records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
            wording_ref=dict(path=authored.relative_to(ROOT).as_posix(),sha256=digest(authored.read_bytes()),json_pointer=f'/roles/{i}/text'),
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,key=r['key'],role=r['role'],references=r['references']),
            rationale='User selected separate Korean speech and Book roles. Manual per-role prose; source and prior decisions retained.',
            semantic_impact='Book title adapted from first dialogue; Book-only portrait metadata and nonstory debug suffix omitted. NPC exact original tag and macro retained.',
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
    changed={original_cases()[k]['source']['id'] for k in [2334,2335]}
    assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in changed)
    protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf-8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4353 and (BASE/'terminology.json').read_bytes()==(snapshot/'terminology.json').read_bytes()
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',dict(status='DEVELOPMENT_SELECTED_TWO_NPC_AND_TWO_DERIVED_KOREAN_BOOK_ROLES',
        authored_original_source_units=3973,selected_original_source_units=3540,held_original_source_units=433,derived_Book_roles=2,decision_history=4353,
        previous_drafts_preserved=True,exact_wording_human_approval=False,runtime_verified=False,release_eligible=False))
    print('Selected3540 original source units; held433; derivedBook2; decisions4353. Build/runtime pending.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);a=p.parse_args();select()

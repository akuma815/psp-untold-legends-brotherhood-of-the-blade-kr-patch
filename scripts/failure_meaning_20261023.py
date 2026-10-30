"""Only3544, original English failure retained per explicit user editorial choice."""
import argparse,json,re,struct
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
import quest_batch_pipeline as pipeline
from late_dialogue_policy_20261020 import validate_draft

KEY=3544;NAME='failure_meaning_20261023';POLICY='NPC3544_source_failure_user_retained_plain_portrait_CRLF_v1'
BASE=ROOT/'workspace/translation';FIELDS={3544:[(13,17,132)]}
REVIEW=ROOT/'qa/reports/review3544_20261023.json';CHOICE=ROOT/'qa/reports/review3544_human_choice_20261023.json'
proposal=json.loads(REVIEW.read_text(encoding='utf8'));DRAFTS={3544:proposal['before']}
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='book_literal_20261023',prior_config='development_book_literal_20261023.json',
          prior_config_sha256='d57bd881876c00f2905b8d1dd6f63a3d77fe86e594979a9225bc11ef4e22a931',
          prior_artifact_sha256='baa58cc97afbb1a0a1754c9cab987525ce7044968dec1c84a20c7d07f18e0eb0',new_authored_count=0)

@lru_cache(maxsize=1)
def sources():
    s=next(s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==KEY)
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    assert raw[s['offset']:s['offset']+s['byte_length']].hex()==s['source_hex'] and s['source_sha256']==proposal['source_sha256']
    return {KEY:s}

def context():
    from translation_scope import collect
    rows,_=collect();refs=next(r['typed_references'] for r in rows if r['bank']=='trans' and r['key']==KEY)
    assert [(r['table'],r['row'],r['field']) for r in refs]==FIELDS[KEY]
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    at,n=struct.unpack_from('<II',db,104);assert n==18 and struct.unpack_from('<I',db,at+17*260+132)[0]==KEY
    choice=json.loads(CHOICE.read_text(encoding='utf8'));assert choice['user_answer']=='영문의 실패 의미를 유지' and not choice['proposal_success_applied']
    return dict(fields=FIELDS,table13_row17_hex=db[at+17*260:at+18*260].hex(),source_has_failure_word=' fail,' in sources()[KEY]['source_text'],
                semantic_choice=choice,semantic_choice_sha256=digest(CHOICE.read_bytes()),original_English_inconsistency_retained=True,
                success_proposal_applied=False,full_translation_or_release_approval=False)

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==KEY and r['control_policy']==POLICY
    assert r['source_text']==sources()[KEY]['source_text'] and r['text']==DRAFTS[KEY]
    assert '실패하리라는' in r['text'] and '성공하리라는' not in r['text']
    context()
    return validate_draft(KEY,r['text'],book,encoder,decoder)

def select():
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256']
    cfg=json.loads(cfgpath.read_text(encoding='utf8'));es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4334
    s=sources()[KEY];e=next(e for e in es if e['id']==s['id']);old=e['current_working_decision']
    assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==DRAFTS[KEY]
    row=dict(key=KEY,source_text=s['source_text'],text=DRAFTS[KEY],control_policy=POLICY);validate(row,pipeline.BOOK,encode_unicode,decode_unicode)
    negative=[]
    for label,change in [('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3548)),('unapproved_success',dict(text=proposal['proposed'])),
        ('portrait_lost',dict(text=DRAFTS[KEY].replace('[i_PI_MadamDiana]',''))),('NUL',dict(text=DRAFTS[KEY]+'\0')),
        ('new_variable',dict(text=DRAFTS[KEY]+'$a')),('new_paragraph',dict(text=DRAFTS[KEY]+'\r\n')),('overflow',dict(text=DRAFTS[KEY]+'가'*2048))]:
        try:validate(dict(row,**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261023_before_failure_meaning';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    before={x['id']:serialized([x]) for x in es};did=f'development_{NAME}:trans:{KEY}'
    d=dict(id=did,source_id=s['id'],source_sha256=s['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,
           applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact NPC3544 source reference; preserve original failure meaning per user'),
           rationale='User explicitly chose English failure meaning after reviewing other four source localizations. Existing authored wording/ref and source portrait retained, success proposal rejected.',
           semantic_impact='Original contradiction is intentionally retained. This is a scoped human editorial choice, not whole translation/release approval.',
           human_editorial_choice_ref=dict(path=CHOICE.relative_to(ROOT).as_posix(),sha256=digest(CHOICE.read_bytes())),
           state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None)
    cfg['trans_overrides'].append(row);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    assert all(serialized([x])==before[x['id']] for x in es if x['id']!=s['id'])
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized([d]))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4335 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    r=dict(status='PASS_UNCHANGED_FAILURE_MEANING3544_SELECTED_PER_USER_CHOICE',authored=3973,selected=3537,working_unselected=436,decision_history=4335,
           new_authored=0,new_selected=1,negative_cases=negative,previous_wording_and_refs_unchanged=True,user_semantic_choice='retain English failure',
           full_translation_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',r);print(json.dumps(r))

def cold_prepare(q):
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    art=ROOT/f'workspace/runtime/{NAME}/artifact.json';a=json.loads(art.read_text(encoding='utf8'));assert len(a['files'])==80
    for rel,m in a['files'].items():
        b=(art.parent/'disc'/rel).read_bytes();assert len(b)==m['size'] and digest(b)==m['sha256']
    print(json.dumps(dict(artifact_sha256=digest(art.read_bytes()))))

def cold_preflight(q):
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf8'))
    cpu=read('before_cpu')['state'];ranges=read('before_ranges')['reads'];assert cpu['cpu.pc']==0x08804000+0x4f358
    t=DRAFTS[KEY];v=t.replace('\r',' ');clean=re.sub(r'\[i_[^]]+\]','',v)
    p=dict(artifact_name=NAME,artifact_sha256=digest((ROOT/f'workspace/runtime/{NAME}/artifact.json').read_bytes()),kind='korean',cold_boot=True,
           other_artifact_state_imports=0,cpu=cpu,ranges=ranges,cases=[dict(key=KEY,text=t,expected=v,input_units=len(v)+1,
           clean_units=len(clean)+1,clean_hex=(clean+'\0').encode('utf-16le').hex(),images=1,p_markers=0)])
    protected_write(q/'preflight.json',json.dumps(p,ensure_ascii=False,indent=2)+'\n');print(json.dumps(p,ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit','cold-prepare','cold-preflight']);p.add_argument('--q');a=p.parse_args()
    if a.action=='select':select()
    elif a.action=='audit':pipeline.audit(SPEC,__import__('failure_meaning_20261023'),DRAFTS,{})
    elif a.action=='cold-prepare':cold_prepare(ROOT/a.q)
    else:cold_preflight(ROOT/a.q)

"""Exact Book3065 literal advisory, prior authored wording; no implicit eligibility."""
import argparse,json,struct,re
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,protected_write,serialized
from pending_story_drafts_20261020 import DRAFTS
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from text_limits import check_template
import quest_batch_pipeline as pipeline

KEY=3065
NAME='book_literal_20261023';POLICY='Book3065_exact_literal_advisory_final_paragraph_CRLF_2048_v1'
FIELDS={3065:[(15,76,24)]};DRAFTS={3065:DRAFTS[3065]};BASE=ROOT/'workspace/translation'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='story_controls_20261023',prior_config='development_story_controls_20261023.json',
          prior_config_sha256='5a64f03a4494d9d1cf6642860705ee9b946a56e7b5ba180d03b7aa2d75402461',
          prior_artifact_sha256='823fedae57fb170316d0c45cf9681109ad4b43b637a8814e30c138c226fe7be2',new_authored_count=0)
@lru_cache(maxsize=1)
def source():
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==KEY)
    data=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes();assert data[s['offset']:s['offset']+s['byte_length']].hex()==s['source_hex']
    return s

def sources():return {KEY:source()}

def validate(r,book,encoder,decoder):
    import unicodedata
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==KEY and r['control_policy']==POLICY
    s=source()['source_text'];t=r['text'];assert r['source_text']==s and t==unicodedata.normalize('NFC',t)
    assert len(re.findall(r'\[[^\[\]]+\]',s))==len(re.findall(r'\[[^\[\]]+\]',t))==1
    assert t.count('[')==t.count(']')==1 and t.endswith(']') and s.endswith(']')
    assert re.findall(r'\r\n+',t)==re.findall(r'\r\n+',s)==['\r\n','\r\n']
    assert t.split('\r\n\r\n')[1].startswith('[') and '[' not in t.split('\r\n\r\n')[0]
    assert not any(c in t for c in '\0\t{}$#%&*+:<=>\\^~') and '[i_' not in t and '[p]' not in t
    assert '\r' not in t.replace('\r\n','') and '\n' not in t.replace('\r\n','')
    b=encoder(t,book).encode('utf8');assert decoder(b.decode('utf8'),book)==t and len(b)<=5000
    check_template(t,'Exact Book3065 literal square advice, source CR preserved; actual original event separate')
    return b

def prepare(q):
    from environment_batch378 import configure,static,observe
    src=ROOT/'qa/runtime/20261023_story_controls_korean_batch01_attempt01'
    pre=json.loads((src/'preflight.json').read_text(encoding='utf8'));state=src/'exact_before_prefetch.ppst'
    assert pre['artifact_name']=='story_controls_20261023'
    art=ROOT/'workspace/runtime/story_controls_20261023/artifact.json';a=json.loads(art.read_text(encoding='utf8'));assert digest(art.read_bytes())==pre['artifact_sha256']
    for rel,m in a['files'].items():
        b=(art.parent/'disc'/rel).read_bytes();assert len(b)==m['size'] and digest(b)==m['sha256']
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    at,n=struct.unpack_from('<II',db,120);assert n==134
    assert struct.unpack_from('<I',db,at+76*56+24)[0]==KEY
    assert struct.unpack_from('<I',db,at+73*56+24)[0]==2502 and struct.unpack_from('<I',db,at+73*56+40)[0]==2266
    configure(47800,q);static();observe('before')
    s=source();pre=dict(pre,cases=[dict(key=KEY,source_text=s['source_text'],draft=DRAFTS[KEY])],
        source_state=state.relative_to(ROOT).as_posix(),source_state_sha256=digest(state.read_bytes()),cold_boot=False,kind='source',
        actual_reference=dict(table=15,row=76,field=24,body=3065,title=3066),
        intervention_reference=dict(table=15,row=73,field=24,previous_body=2502,untouched_title=2266),
        limitation='Actual Book body consumer but first quest row73 QA reference; no original quest acquisition/event trigger.')
    protected_write(q/'preflight.json',json.dumps(pre,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(pre,ensure_ascii=True))

def audit(q):
    from PIL import Image
    from environment_owned_scope_20261022 import environment
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf8'))
    p=read('preflight');kind=p['kind'];text=source()['source_text'] if kind=='source' else DRAFTS[KEY]
    expected=(text.replace('\r',' ')+'\0').encode('utf-16le').hex()
    assert read('body_full')['hex']==read('reentry_body_full')['hex']==expected
    assert read('final_cpu')['state']==p['cpu']
    ranges=read('before_full_ranges')['reads'];assert [r['length'] for r in ranges]==[1980,136,7504]
    assert read('final_ranges')['reads']==ranges
    before=bytearray.fromhex(ranges[2]['hex']);assert struct.unpack_from('<I',before,73*56+24)[0]==2502 and struct.unpack_from('<I',before,73*56+40)[0]==2266
    struct.pack_into('<I',before,73*56+24,3065)
    assert read('edited_T15')['hex']==before.hex() and read('body_reference')['written']==4
    a=read('body_async_cpu')['state'];assert (a['cpu.pc'],a['cpu.a1'],a['cpu.a2'],a['cpu.a3'])==(0x08804000+0x707cc,3065,0,p['cpu']['cpu.s0']+0x2c)
    a=read('title_async_cpu')['state'];assert (a['cpu.pc'],a['cpu.a1'],a['cpu.a3'])==(0x08804000+0x707cc,2266,p['cpu']['cpu.s0']+0x6c)
    shots=[]
    def mask(label):
        f=q/f'Book3065_{label}.png';meta=read('Book3065_'+label);assert digest(f.read_bytes())==meta['provenance']['sha256']
        im=Image.open(f).convert('RGB').crop((212,70,478,235));b=im.tobytes();m=bytes(int(min(b[i:i+3])>160) for i in range(0,len(b),3))
        shots.append(dict(path=f.relative_to(ROOT).as_posix(),sha256=digest(f.read_bytes())));return m
    visible=mask('visible');assert visible==mask('right')==mask('reopen') and visible!=mask('close')
    art=ROOT/f"workspace/runtime/{p['artifact_name']}/artifact.json";a=json.loads(art.read_text(encoding='utf8'));assert digest(art.read_bytes())==p['artifact_sha256']
    for rel,m in a['files'].items():
        b=(art.parent/'disc'/rel).read_bytes();assert len(b)==m['size'] and digest(b)==m['sha256']
    report=dict(status='OBSERVED_BOOK3065_LITERAL_CR_TO_SPACE_BODY_REENTRY_NOT_ORIGINAL_QUEST_ACQUISITION',kind=kind,
                key=3065,artifact_name=p['artifact_name'],artifact_sha256=p['artifact_sha256'],body_UTF16_NUL=len(text)+1,
                entire_input_and_reentry_cache_equal=True,body_panel_mask_equal_tab_and_reopen=True,closed_panel_mask_differs=True,
                source_CR_to_space_preserved=True,original_title2266_not_changed=True,full_body_and_literal_advisory_visually_reviewed=True,
                CPU_and9620_restored=True,all80_verified_after=True,environment=environment(q),screenshots=shots,
                original_quest_trigger_tested=False,human_approval=False,release_eligible=False)
    save_json(q/'completed.json',report);save_json(ROOT/f'qa/reports/Book3065_{kind}_20261023_runtime.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='screenshots'}))

def select():
    evidence=json.loads((ROOT/'qa/reports/Book3065_source_20261023_runtime.json').read_text(encoding='utf8'))
    assert evidence['entire_input_and_reentry_cache_equal'] and evidence['body_panel_mask_equal_tab_and_reopen']
    prior=ROOT/'config'/SPEC['prior_config'];assert digest(prior.read_bytes())==SPEC['prior_config_sha256']
    cfg=json.loads(prior.read_text(encoding='utf8'));es=lines(BASE/'entries.jsonl');ds=decisions();assert len(ds)==4333
    s=source();e=next(e for e in es if e['id']==s['id']);old=e['current_working_decision'];text=DRAFTS[KEY]
    assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==text
    row=dict(key=KEY,source_text=s['source_text'],text=text,control_policy=POLICY);validate(row,pipeline.BOOK,encode_unicode,decode_unicode)
    negative=[]
    for label,change in [('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3066)),('lost_bracket',dict(text=text.replace('[','',1))),
        ('paragraph_lost',dict(text=text.replace('\r\n\r\n',' '))),('new_control',dict(text=text+'[p]')),('new_variable',dict(text=text+'$a')),
        ('NUL',dict(text=text+'\0')),('overflow',dict(text=text+'가'*2048))]:
        try:validate(dict(row,**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261023_before_Book3065';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',prior]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    did=f'development_{NAME}:trans:{KEY}';before={x['id']:serialized([x]) for x in es}
    d=dict(id=did,source_id=s['id'],source_sha256=s['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,
           applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact Book3065 table15row76field24; no DB/code changes'),
           rationale='Original bracket advice renders literally in actual Book body, CR becomes space in cache, exact full body/reentry confirmed. Prior authored wording retained.',
           semantic_impact='No synthetic control token or image/forced-page interpretation. Row73 QA reference is not original quest acquisition.',
           state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None)
    cfg['trans_overrides'].append(row);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    assert all(serialized([x])==before[x['id']] for x in es if x['id']!=s['id'])
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized([d]))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf8');temp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4334 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    r=dict(status='PASS_UNCHANGED_BOOK3065_LITERAL_DRAFT_SELECTED',authored=3973,selected=3536,working_unselected=437,decision_history=4334,
           new_authored=0,new_selected=1,negative_cases=negative,previous_wording_and_refs_unchanged=True,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',r);print(json.dumps(r))

def cold_prepare(q):
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    art=ROOT/f'workspace/runtime/{NAME}/artifact.json';a=json.loads(art.read_text(encoding='utf8'))
    assert len(a['files'])==80
    for rel,m in a['files'].items():
        b=(art.parent/'disc'/rel).read_bytes();assert len(b)==m['size'] and digest(b)==m['sha256']
    taps=(ROOT/'qa/runtime/20261023_story_portraits_korean_batch01_attempt01/boot_commands.json').read_text(encoding='utf8')
    protected_write(q/'boot_commands.json',taps);print(json.dumps(dict(artifact_sha256=digest(art.read_bytes()))))

def cold_preflight(q):
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf8'))
    c=read('before_cpu')['state'];rr=read('before_full_ranges')['reads'];assert c['cpu.pc']==0x08804000+0x4f358
    r=dict(artifact_name=NAME,artifact_sha256=digest((ROOT/f'workspace/runtime/{NAME}/artifact.json').read_bytes()),kind='korean',cold_boot=True,
           other_artifact_state_imports=0,cpu=c,ranges=rr,cases=[dict(key=KEY,source_text=source()['source_text'],draft=DRAFTS[KEY])])
    protected_write(q/'preflight.json',json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',nargs='?',default='prepare',choices=['prepare','audit','select','build-audit','cold-prepare','cold-preflight']);p.add_argument('--q');a=p.parse_args()
    if a.action=='select':select()
    elif a.action=='build-audit':pipeline.audit(SPEC,__import__('book_literal_20261023'),DRAFTS,{})
    elif a.action=='audit':audit(ROOT/a.q)
    elif a.action=='cold-prepare':cold_prepare(ROOT/a.q)
    elif a.action=='cold-preflight':cold_preflight(ROOT/a.q)
    else:prepare(ROOT/a.q)

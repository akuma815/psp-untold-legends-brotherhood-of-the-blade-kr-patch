"""Exact2678 narrator/portrait and3115 ordered portrait/page controls, authored earlier."""
import argparse,json,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,protected_write,serialized
from pending_story_drafts_20261020 import DRAFTS as PRIOR_DRAFTS
from unicode_codec042 import encode_unicode,decode_unicode
from text_limits import check_template
import quest_batch_pipeline as pipeline
from map_corpus_20261020 import decisions
from audit_translation138 import resolve

KEYS={2678,3115};DRAFTS={k:PRIOR_DRAFTS[k] for k in sorted(KEYS)}
NAME='story_controls_20261023';POLICY='story2_exact_narrator_or_portrait_page_interleaving_CRLF_2048_v1'
BASE=ROOT/'workspace/translation'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='story_portraits_20261022',prior_config='development_story_portraits_20261022.json',
          prior_config_sha256='9dccde250f79b1e1acdadc527bedfd4750a44cff0f05c8a2c2f91c110acde888',
          prior_artifact_sha256='1f986c8cf48358e5370578607b08199172856621927f7d6a06dd058abcfe32c6',new_authored_count=0)

@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans' and s['key'] in KEYS}
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    assert set(ss)==KEYS
    for s in ss.values():
        b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    return ss

FIELDS={2678:[(15,61,36)],3115:[(15,79,32)]}
def context():
    from translation_scope import collect
    rows,_=collect();refs={r['key']:[(v['table'],v['row'],v['field']) for v in r['typed_references']] for r in rows if r['bank']=='trans' and r['key'] in KEYS}
    assert refs==FIELDS
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    t,n=struct.unpack_from('<II',db,120);rr={}
    for k,fields in FIELDS.items():
        _,row,field=fields[0];assert row<n and struct.unpack_from('<I',db,t+row*56+field)[0]==k
        rr[k]=db[t+row*56:t+(row+1)*56].hex()
    wi=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'))
    wad=(ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').read_bytes();assert digest(wad)=='696b7618de5fc7c2610666b7b9f543ec2be5e91bcd0bcdd86c20d0d5db47870d'
    assets={}
    for name in ['PI_MadamDiana','PI_MalevolentQueen1','PI_MalevolentQueen2','PI_MalevolentQueen3']:
        found=[e for e in wi['entries'] if e['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+name];assert len(found)==1
        x=found[0];assert digest(wad[x['offset']:x['offset']+x['size_candidate']])==x['sha256'];assets[name]=x
    return dict(fields=FIELDS,table15_rows=rr,assets=assets,narrator_prefix2678_not_speech=True,
                original_3115_two_p_markers_preserved_not_forced_page_semantics=True,
                natural_original_event_geometry_or_trigger_not_tested=True,release_eligible=False)

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    k=r['key'];s=sources()[k]['source_text'];t=r['text'];assert r['source_text']==s and t==unicodedata.normalize('NFC',t)
    controls=lambda v:re.findall(r'\[[^]]+\]',v)
    assert controls(t)==controls(s)
    assert all(v=='[p]' or re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',v) for v in controls(s))
    assert re.findall(r'\r\n+',t)==re.findall(r'\r\n+',s)
    assert [re.findall(r'\r\n+',v) for v in re.split(r'\[i_[^]]+\]|\[p\]',t)]==[re.findall(r'\r\n+',v) for v in re.split(r'\[i_[^]]+\]|\[p\]',s)]
    if k==2678:
        assert controls(s)==['[i_PI_MadamDiana]'] and t.count('"')==s.count('"')==3
        for v in [s,t]:
            prefix,spoken=v.split('[i_PI_MadamDiana]');assert prefix.strip() and '"' not in prefix and spoken.startswith('"')
    else:
        assert controls(s)==['[i_PI_MalevolentQueen1]','[p]','[i_PI_MalevolentQueen2]','[p]','[i_PI_MalevolentQueen3]']
        assert t.startswith('[i_PI_MalevolentQueen1]')
    body=re.sub(r'\[i_[^]]+\]|\[p\]','',t);assert body.strip() and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    b=encoder(t,book).encode('utf8');assert decoder(b.decode('utf8'),book)==t and len(b)<=5000
    check_template(t,'Exact2 source controls/narrator/interleaving, common2048wide only; original mode event separate')
    return b

def prepare(q,kind,artifact,sourceq):
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    src=ROOT/sourceq;old=json.loads((src/'preflight.json').read_text(encoding='utf8'));state=src/'exact_before_prefetch.ppst'
    art=ROOT/f'workspace/runtime/{artifact}/artifact.json';a=json.loads(art.read_text(encoding='utf8'));assert len(a['files'])==80
    for rel,m in a['files'].items():
        b=(art.parent/'disc'/rel).read_bytes();assert len(b)==m['size'] and digest(b)==m['sha256']
    assert old['artifact_name']==artifact and old['artifact_sha256']==digest(art.read_bytes())
    cases=[]
    for k in sorted(KEYS):
        t=sources()[k]['source_text'] if kind=='source' else DRAFTS[k];v=t.replace('\r',' ');clean=re.sub(r'\[i_[^]]+\]|\[p\]','',v)
        cases.append(dict(key=k,text=t,expected=v,input_units=len(v)+1,clean_units=len(clean)+1,clean_hex=(clean+'\0').encode('utf-16le').hex(),images=len(re.findall(r'\[i_[^]]+\]',t)),p_markers=t.count('[p]')))
    pre=dict(artifact_name=artifact,artifact_sha256=digest(art.read_bytes()),kind=kind,cold_boot=False,other_artifact_state_imports=0,
             same_artifact_state_imports=1,source_state=state.relative_to(ROOT).as_posix(),source_state_sha256=digest(state.read_bytes()),
             cpu=old['cpu'],ranges=old['ranges'],cases=cases)
    protected_write(q/'preflight.json',json.dumps(pre,ensure_ascii=False,indent=2)+'\n')
    save_json(q/'source_context.json',context())
    print(json.dumps(pre,ensure_ascii=True))

def select():
    evidence=json.loads((ROOT/f'qa/reports/{NAME.replace("story_controls_","story_controls_source_")}_runtime.json').read_text(encoding='utf8'))
    assert evidence['keys']==[2678,3115] and evidence['exact_all_tag_positions']
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256']
    cfg=json.loads(cfgpath.read_text(encoding='utf8'));es=lines(BASE/'entries.jsonl');byid={e['id']:e for e in es}
    oldrows={e['id']:serialized([e]) for e in es};ds=decisions();assert len(ds)==4331
    src=sources();rows={k:dict(key=k,source_text=src[k]['source_text'],text=t,control_policy=POLICY) for k,t in DRAFTS.items()}
    for r in rows.values():validate(r,pipeline.BOOK,encode_unicode,decode_unicode)
    negative=[]
    for k,label,change in [
        (2678,'wrong_source',dict(source_text='wrong')),(2678,'outside_scope',dict(key=2706)),
        (2678,'narrator_made_speech',dict(text='"'+DRAFTS[2678])),
        (2678,'portrait_moved_front',dict(text='[i_PI_MadamDiana]'+DRAFTS[2678].replace('[i_PI_MadamDiana]',''))),
        (3115,'lost_page',dict(text=DRAFTS[3115].replace('[p]','',1))),
        (3115,'wrong_image_order',dict(text=DRAFTS[3115].replace('Queen1','Queen2',1))),
        (3115,'lost_CRLF_segment',dict(text=DRAFTS[3115].replace('\r\n','',1))),
        (2678,'NUL',dict(text=DRAFTS[2678]+'\0')),(2678,'new_variable',dict(text=DRAFTS[2678]+'$a')),
        (3115,'overflow',dict(text=DRAFTS[3115]+'가'*2048))]:
        try:validate(dict(rows[k],**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261023_before_story_controls';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True)
    protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for k,r in rows.items():
        e=byid[src[k]['id']];old=e['current_working_decision']
        assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==DRAFTS[k]
        did=f'development_{NAME}:trans:{k}'
        records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact source table15 references; no DB/code/WAD change'),
            rationale='Source2678 narrator prefix precedes portrait and source3115 preserves exact three portraits/two page records. Old authored wording and controls unchanged.',
            semantic_impact='Narrator stays third person. Original page positions/order retained; no forced-page or natural event claim.',
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    changed={src[k]['id'] for k in KEYS};assert all(serialized([e])==oldrows[e['id']] for e in es if e['id'] not in changed)
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4333 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_TWO_UNCHANGED_STORY_CONTROL_DRAFTS_DEVELOPMENT_SELECTED',authored=3973,selected=3535,working_unselected=438,decision_history=4333,
                new_authored=0,new_selected=2,negative_cases=negative,previous_wording_and_refs_unchanged=True,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

def cold_prepare(q):
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    art=ROOT/f'workspace/runtime/{NAME}/artifact.json';a=json.loads(art.read_text(encoding='utf8'));assert len(a['files'])==80
    for rel,m in a['files'].items():
        b=(art.parent/'disc'/rel).read_bytes();assert len(b)==m['size'] and digest(b)==m['sha256']
    taps=json.loads((ROOT/'qa/runtime/20261023_story_portraits_korean_batch01_attempt01/boot_commands.json').read_text(encoding='utf8'))
    protected_write(q/'boot_commands.json',json.dumps(taps,indent=2)+'\n')
    print(json.dumps(dict(artifact_sha256=digest(art.read_bytes()),boot_commands=len(taps))))

def cold_preflight(q):
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf8'))
    c=read('before_cpu')['state'];rr=read('before_ranges')['reads'];assert c['cpu.pc']==0x08804000+0x4f358
    assert [r['length'] for r in rr]==[1980,136] and rr[1]['address']==c['cpu.s0']-0x08800000
    assert int.from_bytes(bytes.fromhex(rr[0]['hex'])[1760:1764],'little')==2499
    cases=[]
    for k,t in DRAFTS.items():
        v=t.replace('\r',' ');clean=re.sub(r'\[i_[^]]+\]|\[p\]','',v)
        cases.append(dict(key=k,text=t,expected=v,input_units=len(v)+1,clean_units=len(clean)+1,clean_hex=(clean+'\0').encode('utf-16le').hex(),
                          images=len(re.findall(r'\[i_[^]]+\]',v)),p_markers=v.count('[p]')))
    art=ROOT/f'workspace/runtime/{NAME}/artifact.json'
    r=dict(artifact_name=NAME,artifact_sha256=digest(art.read_bytes()),kind='korean',cold_boot=True,
           other_artifact_state_imports=0,cpu=c,ranges=rr,cases=cases)
    protected_write(q/'preflight.json',json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(r,ensure_ascii=True))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['context','prepare','select','audit','cold-prepare','cold-preflight']);p.add_argument('--q');p.add_argument('--kind',choices=['source','korean']);p.add_argument('--artifact');p.add_argument('--sourceq');a=p.parse_args()
    if a.action=='context':
        r=context();save_json(ROOT/f'qa/reports/{NAME}_context.json',r);print(json.dumps(r))
    elif a.action=='select':select()
    elif a.action=='audit':pipeline.audit(SPEC,__import__('story_controls_20261023'),DRAFTS,{})
    elif a.action=='cold-prepare':cold_prepare(ROOT/a.q)
    elif a.action=='cold-preflight':cold_preflight(ROOT/a.q)
    else:prepare(ROOT/a.q,a.kind,a.artifact,a.sourceq)

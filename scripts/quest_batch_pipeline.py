"""Reusable source-bound quest batch serialization, selection and final-byte checks.

The writer supplies every complete sentence. This module never generates or
rewrites prose; explicit single-entry corrections carry before/after wording.
"""
import copy,json,re,struct
from collections import Counter
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
from map_corpus_20261020 import decisions
from unicode_codec042 import encode_unicode,decode_unicode

BASE=ROOT/'workspace/translation'
BOOK={'mapping':{c:None for c in range(0xac00,0xd7a4)}}

def preflight(spec,policy,drafts,corrections,notes):
    assert set(drafts)==set(policy.FIELDS)
    held=spec.get('held_drafts',{});reasons=spec.get('held_reasons',{})
    assert not set(held)&set(drafts) and set(held)==set(reasons)
    cfgpath=ROOT/'config'/spec['prior_config'];assert digest(cfgpath.read_bytes())==spec['prior_config_sha256']
    es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();assert len(ds)==spec['prior_decisions']
    src=policy.sources();ward=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));portraits={}
    for k,text in drafts.items():
        assert es[src[k]['id']]['state']=='untranslated' and not es[src[k]['id']]['decision_ids']
        policy.validate(dict(key=k,source_text=src[k]['source_text'],text=text,control_policy=policy.POLICY),BOOK,encode_unicode,decode_unicode)
        for name in re.findall(r'\[i_([^\]]+)\]',src[k]['source_text']):
            rr=[r for r in ward['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+name];assert len(rr)==1;portraits[name]=rr[0]
    for k,text in held.items():
        assert es[src[k]['id']]['state']=='untranslated' and not es[src[k]['id']]['decision_ids'] and reasons[k]
        policy.validate_draft(k,text,BOOK,encode_unicode,decode_unicode)
    allsrc={s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    for k,c in corrections.items():
        e=es[allsrc[k]['id']];assert resolve(ds[e['development_diagnostic_selection']])==c['previous']
        row=next(r for r in json.loads(cfgpath.read_text(encoding='utf8'))['trans_overrides'] if r['key']==k)
        assert row['text']==c['previous']
        spec['validate_correction'](dict(row,text=c['text']),BOOK,encode_unicode,decode_unicode)
    negative=[]
    if hasattr(policy,'negative_cases'):r,cases=policy.negative_cases(drafts)
    else:
        key=next(k for k in drafts if src[k]['source_text'].startswith('[i_'))
        r=dict(key=key,source_text=src[key]['source_text'],text=drafts[key],control_policy=policy.POLICY)
        cases=[('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=2705)),('portrait',dict(text=r['text'].replace('[i_','[i_Unknown',1))),
                      ('NUL',dict(text=r['text']+'\0')),('invented_variable',dict(text=r['text']+'$a')),('new_page_control',dict(text=r['text']+'[p]')),
                      ('lost_paragraph',dict(text=r['text'].replace('\r\n\r\n','',1))),('overflow',dict(text=r['text']+'가'*2048))]
    for label,mut in cases:
        try:policy.validate(dict(r,**mut),BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError('Unsafe batch input accepted: '+label)
    packet=BASE/'packets'/spec['name'];packet.mkdir(parents=True,exist_ok=True)
    protected_write(packet/'context.json',json.dumps(dict(**policy.context(),sources=list(src.values()),portrait_assets=portraits,
                    source_db_sha256='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2',semantic_notes=notes),ensure_ascii=False,indent=2)+'\n')
    snap=ROOT/'qa/ssot'/(spec.get('date','20261020')+'_before_'+spec['name']);snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    protected_write(snap/'manifest.json',json.dumps(dict(entries_sha256=digest((snap/'entries.jsonl').read_bytes()),
        terminology_sha256=digest((snap/'terminology.json').read_bytes()),config=spec['prior_config'],config_sha256=spec['prior_config_sha256'],
        artifact_sha256=spec['prior_artifact_sha256']),ensure_ascii=False,indent=2)+'\n')
    report=dict(status='PASS_QUEST_BATCH_SOURCE_CONTROL_CODEC',name=spec['name'],new_entries=len(drafts),corrections=list(corrections),
                held_entries=len(held),held_reasons=reasons,
                source_utf16_units=sum(s['source_utf16_units'] for s in src.values()),draft_utf16_units=sum(len(t.encode('utf-16le'))//2 for t in drafts.values()),
                maximum_draft_utf16_units=max(len(t.encode('utf-16le'))//2 for t in drafts.values()),negative_cases=negative,
                entries_before_sha256=digest((BASE/'entries.jsonl').read_bytes()),terminology_before_sha256=digest((BASE/'terminology.json').read_bytes()),
                previous_decisions=len(ds),semantic_notes=notes,independent_semantic_review=None,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{spec["name"]}_preflight.json',report);print(json.dumps(report))

def apply(spec,policy,drafts,corrections,terms,termkeys):
    name=spec['name'];pre=json.loads((ROOT/f'qa/reports/{name}_preflight.json').read_text(encoding='utf8'))
    assert digest((BASE/'entries.jsonl').read_bytes())==pre['entries_before_sha256'] and digest((BASE/'terminology.json').read_bytes())==pre['terminology_before_sha256']
    prior=ROOT/'config'/spec['prior_config'];assert digest(prior.read_bytes())==spec['prior_config_sha256'];cfg=json.loads(prior.read_text(encoding='utf8'))
    es=lines(BASE/'entries.jsonl');byid={e['id']:e for e in es};before={e['id']:serialized([e]) for e in es};old=decisions()
    assert len(old)==spec['prior_decisions'];src=policy.sources();all_src={s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    rows=[dict(key=k,source_id=src[k]['id'],source_sha256=src[k]['source_sha256'],source_text=src[k]['source_text'],text=drafts[k],references=policy.FIELDS[k],human_reviewed=False,independent_review=None,distribution_eligible=False) for k in policy.FIELDS]
    held=[dict(key=k,source_id=src[k]['id'],source_sha256=src[k]['source_sha256'],source_text=src[k]['source_text'],text=text,
               references=policy.ALL_FIELDS[k],rationale=spec['held_reasons'][k],human_reviewed=False,independent_review=None,distribution_eligible=False)
          for k,text in spec.get('held_drafts',{}).items()]
    changes=[dict(key=k,source_id=all_src[k]['id'],source_sha256=all_src[k]['source_sha256'],**c,
                  prior_decision=byid[all_src[k]['id']]['development_diagnostic_selection']) for k,c in corrections.items()]
    path=BASE/'authored'/f'{name}.json';protected_write(path,json.dumps(dict(policy='individual_manual_development_proposals',drafts=rows,held_drafts=held,corrections=changes,term_proposals=terms),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for kind,items in [('drafts',rows),('held_drafts',held),('corrections',changes)]:
        for i,r in enumerate(items):
            e=byid[r['source_id']]
            if kind in ('drafts','held_drafts'):
                assert e['state']=='untranslated' and not e['decision_ids']
                item=dict(key=r['key'],source_text=r['source_text'],text=r['text'],control_policy=policy.POLICY)
                if kind=='drafts':
                    policy.validate(item,BOOK,encode_unicode,decode_unicode);cfg['trans_overrides'].append(item)
                else:policy.validate_draft(r['key'],r['text'],BOOK,encode_unicode,decode_unicode)
            else:
                assert resolve(old[r['prior_decision']])==r['previous']
                item=next(v for v in cfg['trans_overrides'] if v['key']==r['key']);assert item['text']==r['previous'];item['text']=r['text']
                spec['validate_correction'](item,BOOK,encode_unicode,decode_unicode)
            isheld=kind=='held_drafts';state='in_progress' if isheld else 'needs_human_review'
            did=f'{"working" if isheld else "development"}_{name}:trans:{r["key"]}'
            records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
                wording_ref=dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()),json_pointer=f'/{kind}/{i}/text'),
                broader_decision_id=r.get('prior_decision'),applicability=dict(revision='ULKS46015-v1.01',context=name,write_scope=f'Exact trans{r["key"]}; no global text replacement'),
                rationale=r.get('rationale','Individually composed, full quest-state context and source tags preserved.'),
                semantic_impact='Provisional names, lore, voice and interpretation need human review; technical development only.',
                state=state,approval=None,distribution_eligible=False,independent_semantic_review=None,
                mechanical_evidence=[f'qa/reports/{name}_preflight.json']))
            e['decision_ids'].append(did);e.update(state=state,context_id=name)
            if isheld:e.update(current_working_decision=did)
            else:e.update(development_diagnostic_selection=did)
    targets={r['source_id'] for r in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in targets)
    assert Counter(e['state'] for e in es)==spec['expected_states']
    vocabulary=json.loads((BASE/'terminology.json').read_text(encoding='utf8'));approved=copy.deepcopy(vocabulary['approved_decisions'])
    for i,(english,korean) in enumerate(terms.items()):
        candidate=dict(id=f'term-{name}-{i}',source_referent=english,candidate_wording=korean,
            candidate_wording_decision_ref=f'development_{name}:trans:{termkeys[i]}',state='unresolved',approval=None,
            applicability='This source-bound cohort; naming/voice not human approved; no global replacement',evidence=[f'qa/reports/{name}_preflight.json'])
        prior_candidate=spec.get('term_supersessions',{}).get(english)
        if prior_candidate:
            previous=next(t for t in vocabulary['candidate_decisions'] if t['id']==prior_candidate)
            assert previous['approval'] is None
            previous['superseded_in_development_by']=candidate['id'];candidate['previous_candidate_ref']=prior_candidate
        vocabulary['candidate_decisions'].append(candidate)
    assert vocabulary['approved_decisions']==approved
    protected_write(ROOT/'config'/spec['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{name}.jsonl',serialized(records))
    tmp=BASE/f'entries.{name}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl');save_json(BASE/'terminology.json',vocabulary)
    assert len(decisions())==spec['expected_decisions']
    report=dict(status='PASS_QUEST_BATCH_DEVELOPMENT_SELECTIONS',name=name,authored=sum(e['state']!='untranslated' for e in es),selected=sum(bool(e['development_diagnostic_selection']) for e in es),
                working_unselected=sum(e['state']=='in_progress' for e in es),decision_history=len(decisions()),new_authored=len(rows)+len(held),new_selected=len(rows),new_held=len(held),corrected_keys=list(corrections),
                previous_wordings_unchanged_except_explicit_corrections=True,config_sha256=digest((ROOT/'config'/spec['config']).read_bytes()),human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{name}_selection.json',report);print(json.dumps(report))

def audit(spec,policy,drafts,corrections):
    from reference_candidate import rederive,reference_bytes
    from audit_appearance028 import candidate_audit
    from audit_selection044 import audit_selection
    name=spec['name'];old=rederive(spec['prior_name'],spec['prior_config'],spec['prior_artifact_sha256'],spec['prior_config_sha256'])
    root,plan,art,cfg,book=candidate_audit(name,spec['config'],unicode_hangul=True);newcount=len(drafts)
    assert cfg['static_overrides']==old[3]['static_overrides'];oldrows=copy.deepcopy(old[3]['trans_overrides'])
    for k,c in corrections.items():
        row=next(v for v in oldrows if v['key']==k);assert row['text']==c['previous'];row['text']=c['text']
    assert cfg['trans_overrides'][:-newcount]==oldrows and {r['key'] for r in cfg['trans_overrides'][-newcount:]}==set(drafts)
    expected=dict(drafts)
    for k,c in corrections.items():expected[k]=c['text']
    prefix='PSP_GAME/USRDIR/locale/';changed=[p for p,m in art['files'].items() if m!=old[2]['files'][p]];assert changed==[prefix+'en_us_dir.dat',prefix+'en_us_trans.dat']
    ad=reference_bytes(old,prefix+'en_us_dir.dat');at=reference_bytes(old,prefix+'en_us_trans.dat');bd=(root/'disc'/prefix/'en_us_dir.dat').read_bytes();bt=(root/'disc'/prefix/'en_us_trans.dat').read_bytes();logical=[]
    assert len(ad)==len(bd)
    for off in range(0,len(bd),20):
        x=struct.unpack_from('<IIIHHHH',ad,off);y=struct.unpack_from('<IIIHHHH',bd,off);assert x[:2]==y[:2] and x[3]==y[3] and x[5:]==y[5:]
        if at[x[2]:x[2]+x[4]]!=bt[y[2]:y[2]+y[4]]:
            logical.append(y[0]);assert bt[y[2]:y[2]+y[4]]==expected[y[0]].encode('utf8')
    assert set(logical)==set(expected) and len(logical)==len(expected) and y[2]+y[4]==len(bt)
    heldkeys=set(spec.get('held_drafts',{}));unchanged_held=[]
    original=policy.sources()
    for off in range(0,len(bd),20):
        row=struct.unpack_from('<IIIHHHH',bd,off)
        if row[0] in heldkeys:
            assert bt[row[2]:row[2]+row[4]]==original[row[0]]['source_text'].encode('utf8');unchanged_held.append(row[0])
    assert set(unchanged_held)==heldkeys
    for r in cfg['trans_overrides'][-newcount:]:policy.validate(r,book,encode_unicode,decode_unicode)
    count=sum(bool(e['development_diagnostic_selection']) for e in lines(BASE/'entries.jsonl'));assert count==plan['selected_development_draft_count']
    audit_selection(name,spec['config'],count,f'qa/reports/{name}_selection_audit.json')
    ds=decisions();es=lines(BASE/'entries.jsonl');chars=set()
    for e in es:
        if e['state']=='untranslated':continue
        did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1]
        chars.update(c for c in resolve(ds[did]) if 0xac00<=ord(c)<=0xd7a3)
    report=dict(status='PASS_QUEST_BATCH_FINAL_80_FILES',name=name,authored=sum(e['state']!='untranslated' for e in es),selected=count,
                working_unselected=sum(e['state']=='in_progress' for e in es),decision_history=len(ds),new_authored=spec.get('new_authored_count',len(drafts)+len(heldkeys)),new_selected=len(drafts),held_keys_original_bytes=sorted(unchanged_held),corrected_keys=list(corrections),
                changed_logical_keys=logical,changed_files=changed,other78_files_byte_equal=True,all113_map_wordings_unchanged=True,
                modern_Hangul_unique_demand=len(chars),trans_growth_bytes=len(bt)-len(at),config_sha256=digest((ROOT/'config'/spec['config']).read_bytes()),
                artifact_sha256=digest((root/'artifact.json').read_bytes()),exact_new_build_runtime_not_attempted=True,new_ISO=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{name}_build.json',report);print(json.dumps(report))

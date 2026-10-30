"""Exact approved-footer layer. Selection/build fail until rule approval exists."""
import argparse,copy,json,struct
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from retained_numeric_formats_20261024 import CONFIG as PARENT_CONFIG,derive_retained

NAME='marker_footer_20261024';CONFIG=f'development_{NAME}.json';BASE=ROOT/'workspace/translation'
PACKET='workspace/translation/review/20261024_marker_footer_proposal/packet.json'
APPROVAL='workspace/translation/review/20261024_marker_footer_proposal/approval.json'


def approved_rows():
    path=ROOT/APPROVAL
    assert path.is_file(),'Rule approval is absent;do not select or build this layer.'
    a=json.loads(path.read_text(encoding='utf-8'));packet=ROOT/PACKET
    assert a['status']=='approved_exact_footer_rule' and a['packet_sha256']==digest(packet.read_bytes())
    p=json.loads(packet.read_text(encoding='utf-8'));allrows=p['records']
    selected=[r['key'] for r in allrows if r['selected']]
    assert a['scope_keys'] in [p['rule']['scope_keys'],selected]
    assert a['full_translation_or_release_approval'] is False
    rows=[r for r in allrows if r['key'] in a['scope_keys']]
    assert len(rows) in [16,20] and sum(r['selected'] for r in rows)==16
    sources={s['id']:s for s in lines(BASE/'baseline/source_entries.jsonl')}
    for r in rows:
        s=sources[r['id']];raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert s['source_sha256']==r['source_sha256']==digest(raw) and raw.hex()==s['source_hex']
        assert r['before']==r['after']+r['removed_exact_suffix']
        assert digest(r['before'].encode('utf-8'))==r['before_UTF8_sha256']
        assert digest(r['after'].encode('utf-8'))==r['after_UTF8_sha256']
        assert r['removed_exact_suffix'] in ['\r\n*BUG THIS*','\r\r\n*BUG THIS*','\r\n*BUG ME*','\r\r\n*BUG ME*']
    return a,p,rows


def config():
    a,p,rows=approved_rows();parent=ROOT/'config'/PARENT_CONFIG
    return dict(schema_version=14,policy='development_poc_non_distributable',parent_config=PARENT_CONFIG,parent_config_sha256=digest(parent.read_bytes()),
        proposal_path=PACKET,proposal_sha256=digest((ROOT/PACKET).read_bytes()),rule_approval_path=APPROVAL,rule_approval_sha256=digest((ROOT/APPROVAL).read_bytes()),
        trans_overrides=[dict(key=r['key'],before=r['before'],text=r['after'],removed_exact_suffix=r['removed_exact_suffix']) for r in rows if r['selected']],
        approved_working_only_held_keys=[r['key'] for r in rows if not r['selected']])


def derive_markers(cfg):
    assert cfg==config()
    parent=json.loads((ROOT/'config'/PARENT_CONFIG).read_text(encoding='utf-8'));plan,outputs=derive_retained(parent)
    plan=copy.deepcopy(plan);outputs=dict(outputs);prefix='PSP_GAME/USRDIR/locale/'
    directory=outputs[prefix+'en_us_dir.dat'];trans=outputs[prefix+'en_us_trans.dat']
    oldrows=[struct.unpack_from('<IIIHHHH',directory,i) for i in range(0,len(directory),20)];assert len(oldrows)==860
    replacements={r['key']:r for r in cfg['trans_overrides']};assert len(replacements)==16
    new=bytearray();rows=[];hit=set()
    for old in oldrows:
        key,ep,tp,el,tl,flag,res=old;payload=trans[tp:tp+tl]
        if key in replacements:
            r=replacements[key];assert payload==r['before'].encode('utf-8')
            payload=r['text'].encode('utf-8');hit.add(key)
        rows.append((key,ep,len(new),el,len(payload),flag,res));new.extend(payload)
    assert hit==set(replacements)
    for old,row in zip(oldrows,rows):
        k,ep,tp,el,tl,flag,res=row
        assert (k,ep,el,flag,res)==(old[0],old[1],old[3],old[5],old[6])
        wanted=replacements[k]['text'].encode('utf-8') if k in replacements else trans[old[2]:old[2]+old[4]]
        assert new[tp:tp+tl]==wanted
    changes={prefix+'en_us_dir.dat':b''.join(struct.pack('<IIIHHHH',*r) for r in rows),prefix+'en_us_trans.dat':bytes(new)}
    old_outputs=dict(outputs);plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw
        plan['writes'].append(dict(owner='Human-approved exact terminal debug-footer removal',path=path,offset=0,size=len(raw),source_size=len(original),
            expected_sha256=digest(original),final_sha256=digest(raw),derivation='Source-derived schema13 plus exact16 approved suffix removals. Other844 payloads and English fields preserved. No NPC/quest reference or EBOOT change.'))
    assert all(outputs[p]==raw for p,raw in old_outputs.items() if p not in changes)
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['approved_terminal_footer_cleanup']=dict(selected_payloads=16,held_working_only_keys=cfg['approved_working_only_held_keys'],
        original_selected_total=3569,held_total=404,derived_Book_roles=2,new_glyphs=0,original_refs_and_portraits_preserved=True,
        native_new_payload_validation_pending=True,rule_approval=APPROVAL,full_translation_or_release_approval=False)
    plan['font']['scope']='Same3569 selected original units and2 derived Book roles. Exact approved terminal footer cleanup;remaining review and target-runtime QA pending.'
    return plan,outputs


def select():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    a,p,rows=approved_rows();m=p['baseline'];entries=BASE/'entries.jsonl'
    assert digest(entries.read_bytes())==m['entries_sha256']
    es=lines(entries);ds=decisions();assert len(ds)==4382
    snapshot=ROOT/'qa/ssot/20261024_before_marker_footer';snapshot.mkdir(parents=True,exist_ok=True)
    for path in [entries,BASE/'terminology.json',ROOT/'config'/PARENT_CONFIG,ROOT/'docs/HANDOFF.md']:
        protected_write(snapshot/path.name,path.read_text(encoding='utf-8'))
    before={e['id']:serialized([e]) for e in es};byid={e['id']:e for e in es};added=[]
    fullpacket=json.loads((ROOT/PACKET).read_text(encoding='utf-8'))['records']
    for r in rows:
        e=byid[r['id']];old=e['current_working_decision'];assert old==r['working_decision'] and resolve(ds[old])==r['before']
        assert e['development_diagnostic_selection']==r['development_selection']
        did=f'{NAME}:trans:{r["key"]}';index=next(i for i,x in enumerate(fullpacket) if x['id']==r['id'])
        added.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
            wording_ref=dict(path=PACKET,sha256=digest((ROOT/PACKET).read_bytes()),json_pointer=f'/records/{index}/after'),
            broader_decision_id=old,applicability=dict(revision='ULKS46015-v1.01',context=NAME,scope='Exact one approved terminal footer;preceding wording and portraits unchanged'),
            rationale='Apply exact human-approved footer rule to pinned pre/post wording. Held entries remain unselected.',
            semantic_impact='Developer footer and its *B formatting operation removed;not a full wording/release approval.',
            rule_approval=dict(path=APPROVAL,sha256=digest((ROOT/APPROVAL).read_bytes())),
            state=e['state'],approval=None,distribution_eligible=False,independent_semantic_review=None))
        e['current_working_decision']=did;e['decision_ids'].append(did)
        if r['selected']:e['development_diagnostic_selection']=did
    assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in {r['id'] for r in rows})
    assert sum(bool(e['development_diagnostic_selection']) for e in es)==3569
    cfg=config();protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(added))
    temp=BASE/f'entries.{NAME}.pending';temp.write_text(serialized(es),encoding='utf-8');temp.replace(entries)
    assert len(decisions())==4382+len(rows) and (BASE/'terminology.json').read_bytes()==(snapshot/'terminology.json').read_bytes()
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',dict(status='EXACT_RULE_APPLIED_NEW16_PAYLOAD_RUNTIME_PENDING',
        authored=3973,selected=3569,held=404,wordings_updated=len(rows),selected_payloads_changed=16,held_working_only_updated=len(rows)-16,
        decisions=4382+len(rows),new_glyphs=0,newly_selected=0,rule_approval=APPROVAL,release_eligible=False))
    print('Approved footer rule applied;16 selected payloads queued;held eligibility andallprecedingwording unchanged.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);p.parse_args();select()

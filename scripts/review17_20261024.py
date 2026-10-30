"""Exact seventeen individually reviewed changes; human choice bound to frozen v7."""
import argparse, copy, json, re, shutil, struct, unicodedata
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized, protected_write
from property_grouping_build_20261024 import CONFIG as PARENT, derive_grouping

NAME = 'review17_20261024'
CONFIG = 'development_' + NAME + '.json'
BASE = ROOT / 'workspace/translation'
PACKET = 'workspace/translation/review/20261024_schema20_inventory_v7/packet.json'
APPROVAL = 'workspace/translation/review/20261024_schema20_inventory_v7/approval_exact17.json'
AUTHOR = 'workspace/translation/authored/review17_20261024.json'
STATIC = {468, 569, 772, 3865, 3866}
HP = {2903, 3098, 3101, 3118, 3143, 3732}
FOOTER = {2280, 2281, 2284, 2285}
TRANS = HP | FOOTER | {2597, 2678}
PREFIX = 'PSP_GAME/USRDIR/locale/en_us_'
PACKET_SHA = 'fd3653be6b740f6bc5bae1792cb92d88f620aefc55bed4483c08da0b786a4e79'
ENTRIES_SHA = 'caf7ca71f5228718ddcc83027f3b0480251374b3497aab0951f393dacfe9b615'
TERMS_SHA = 'f01592af2339abc882a7b20436b62eb28de1c6ff51f7fa36371be1b63cbeba6a'


def frozen_rows():
    raw = (ROOT / PACKET).read_bytes(); assert digest(raw) == PACKET_SHA
    packet = json.loads(raw)
    rows = [r for r in packet['records'] if (r['bank'] == 'static' and r['key'] in STATIC) or (r['bank'] == 'trans' and r['key'] in TRANS)]
    assert len(rows) == 17 and packet['entries_sha256'] == ENTRIES_SHA
    for r in rows:
        p = r['wording_proposal']; before, after = p['before'], p['proposed']
        assert r['status'] == 'selected' and r['wording'] == r['payload_text'] == before
        assert p['source_sha256'] == r['source_sha256'] and p['current_decision'] == r['decision']
        assert before != after and '\0' not in after and unicodedata.normalize('NFC', after) == after
        assert len(after.encode('utf8')) + 1 <= (250 if r['bank'] == 'static' else 5000)
        assert len(after.encode('utf-16le')) // 2 + 1 <= 2048
        if r['key'] in FOOTER:
            assert before == after + '\r\n*Bug This if You See It*'
        else:
            assert re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\*[A-Z]|\r\n', before) == re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\*[A-Z]|\r\n', after)
        if r['key'] in HP:
            assert before.count('체력') == 1 and after == before.replace('체력', '생명력')
        elif r['key'] == 2597:
            assert before.count(p['exact_before_fragment']) == 1
            assert after == before.replace(p['exact_before_fragment'], p['exact_proposed_fragment'])
        elif r['key'] == 2678:
            assert after == before.replace('파괴가 시작되는군요...', '파괴가 시작되는군...').replace('지금 가요, 수호자! 모든 것을 잃기 전에 그를 막아요!', '지금 가라, 수호자! 모든 것을 잃기 전에 그를 막아라!')
    return packet, rows


def approved_rows():
    packet, rows = frozen_rows(); a = json.loads((ROOT / APPROVAL).read_text(encoding='utf8'))
    assert a['answer'] == '17개 모두 제시한 범위로 반영' and a['packet_sha256'] == PACKET_SHA
    assert a['scope_ids'] == [r['id'] for r in rows] and not a['full_wording_or_release_approval']
    assert a['pairs'] == [dict(id=r['id'], bank=r['bank'], key=r['key'], before=r['wording'], after=r['wording_proposal']['proposed']) for r in rows]
    if (ROOT/AUTHOR).exists():
        author=json.loads((ROOT/AUTHOR).read_text(encoding='utf8'))
        assert author['records']==[dict(id=r['id'],bank=r['bank'],key=r['key'],source_sha256=r['source_sha256'],before=r['wording'],text=r['wording_proposal']['proposed'],previous_decision=r['decision']) for r in rows]
    return a, rows


def configuration():
    a, rows = approved_rows()
    return dict(schema_version=21, policy='development_poc_non_distributable', parent_config=PARENT,
                parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
                packet=PACKET, packet_sha256=PACKET_SHA, approval=APPROVAL,
                approval_sha256=digest((ROOT/APPROVAL).read_bytes()), author=AUTHOR,
                author_sha256=digest((ROOT/AUTHOR).read_bytes()), exact_keys=[r['key'] for r in rows], release_eligible=False)


def select():
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    packet, rows = frozen_rows(); entries = BASE/'entries.jsonl'; terms_path = BASE/'terminology.json'
    assert digest(entries.read_bytes()) == ENTRIES_SHA and digest(terms_path.read_bytes()) == TERMS_SHA
    ds = decisions(); assert len(ds) == 4402
    es = lines(entries); old_serial = {e['id']: serialized([e]) for e in es}; byid = {e['id']:e for e in es}
    snap = ROOT/'qa/ssot/20261024_before_review17'; assert not snap.exists(); snap.mkdir(parents=True)
    paths = [entries, terms_path, ROOT/'config'/PARENT, ROOT/'workspace/runtime/property_grouping_20261024/artifact.json', ROOT/'docs/HANDOFF.md', ROOT/'docs/HANDOFF_2026-10-24.md', ROOT/'scripts/build_font_folder.py', ROOT/'scripts/book_role_runtime_20261024.py', ROOT/'qa/reports/continuation_queue_20261024.json', ROOT/'AGENTS.md']
    manifest = []
    for f in paths:
        dest = snap/f.relative_to(ROOT); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(f,dest)
        assert dest.read_bytes() == f.read_bytes(); manifest.append(dict(path=f.relative_to(ROOT).as_posix(),sha256=digest(f.read_bytes())))
    save_json(snap/'manifest.json',dict(files=manifest,source_preserved=True))
    for r in rows:
        e=byid[r['id']]; assert e['source_sha256']==r['source_sha256']
        assert e['development_diagnostic_selection']==r['decision'] and resolve(ds[r['decision']])==r['wording']
    approval=dict(status='USER_APPROVED_EXACT17', authority='user', date_local='2026-10-24',
        question_item_id='["request_user_input_async","call_0d72e63412114a54b670e90dd6c52208",0]',
        answer='17개 모두 제시한 범위로 반영',packet=PACKET,packet_sha256=PACKET_SHA,
        entries_before_sha256=ENTRIES_SHA,terminology_before_sha256=TERMS_SHA,
        artifact_before_sha256=digest((ROOT/'workspace/runtime/property_grouping_20261024/artifact.json').read_bytes()),
        scope_ids=[r['id'] for r in rows],pairs=[dict(id=r['id'],bank=r['bank'],key=r['key'],before=r['wording'],after=r['wording_proposal']['proposed']) for r in rows],
        exclusions=['3548 exact wording','derived Book4009/4010 exact wording','all other source keys or occurrences','full wording and layout approval','distribution approval'],
        full_wording_or_release_approval=False)
    protected_write(ROOT/APPROVAL,json.dumps(approval,ensure_ascii=False,indent=2)+'\n')
    author=dict(policy='Exact frozen v7 full strings selected by user; no corpus rewrite',records=[dict(id=r['id'],bank=r['bank'],key=r['key'],source_sha256=r['source_sha256'],before=r['wording'],text=r['wording_proposal']['proposed'],previous_decision=r['decision']) for r in rows])
    protected_write(ROOT/AUTHOR,json.dumps(author,ensure_ascii=False,indent=2)+'\n')
    terms=json.loads(terms_path.read_text(encoding='utf8')); assert len(terms['approved_decisions'])==14
    added=[]
    for i,r in enumerate(rows):
        e=byid[r['id']]; did=f'{NAME}:{r["bank"]}:{r["key"]}'
        added.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],
            wording_ref=dict(path=AUTHOR,sha256=digest((ROOT/AUTHOR).read_bytes()),json_pointer=f'/records/{i}/text'),
            broader_decision_id=r['decision'],applicability=dict(revision='ULKS46015-v1.01',context=NAME,scope='Only this full frozen-v7 string and declared fragment change'),
            rationale='User explicitly selected all17 exact pre/post pairs.',semantic_impact='Scoped wording/terminal-footer choice; no whole translation, presentation or release approval.',
            human_wording_choice_ref=dict(path=APPROVAL,sha256=digest((ROOT/APPROVAL).read_bytes())),state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        e['development_diagnostic_selection']=did; e['current_working_decision']=did; e['context_id']=NAME; e['decision_ids'].append(did)
        if r['bank']=='static':
            terms['approved_decisions'].append(dict(id=f'approved-review17-{r["key"]}-20261024',source_id=e['id'],source_sha256=e['source_sha256'],source_referent=r['source'],approved_wording=r['wording_proposal']['proposed'],applicability='Only this exact static label; no other-key/prose normalization',exclusions=['Other keys, prose and spelling variants'],state='approved',approval=dict(authority='user',date_local='2026-10-24',chosen_answer=approval['answer'],choice_ref=APPROVAL,scope='Exact label wording only'),normalization_policy='Exact full replacement only'))
    targets={r['id'] for r in rows}; assert all(serialized([e])==old_serial[e['id']] for e in es if e['id'] not in targets)
    assert sum(bool(e['development_diagnostic_selection']) for e in es)==3569
    protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(added))
    protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    for path,text in [(entries,serialized(es)),(terms_path,json.dumps(terms,ensure_ascii=False,indent=2)+'\n')]:
        temp=path.with_name(path.name+'.review17.pending');temp.write_text(text,encoding='utf8');temp.replace(path)
    assert len(decisions())==4419 and len(terms['approved_decisions'])==19
    queue_path=ROOT/'qa/reports/continuation_queue_20261024.json';queue=json.loads(queue_path.read_text(encoding='utf8'))
    queue['pending_exact_wording_decision'].update(answer_received=True,answer=approval['answer'],approval=APPROVAL,proposals_remain_unselected_until_answer=False,selection_completed=True,new_build_runtime_pending=True)
    queue['next_action']='Build schema21 from immutable source, verify only17 logical payload differences, then targeted native QA before launcher adoption.'
    save_json(queue_path,queue)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',dict(status='PASS_EXACT17_SELECTED_BUILD_RUNTIME_PENDING',selected=3569,held=404,decisions=4419,approved_label_decisions=19,modified_entries=17,other_entries_byte_equal=3956,entries_sha256=digest(entries.read_bytes()),terminology_sha256=digest(terms_path.read_bytes()),release_eligible=False))
    print('Selected exact17;3569selected/404held;4419decisions;runtime pending.')


def static_rows(raw):
    result=[]; cursor=4
    while cursor<len(raw):
        key,n=struct.unpack_from('<IH',raw,cursor);cursor+=6;result.append((key,raw[cursor:cursor+n]));cursor+=n
    assert cursor==len(raw) and len(result)==2852
    return result


def derive_review17(cfg):
    assert cfg==configuration();a,rs=approved_rows()
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    byid={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions()
    for r in rs:
        e=byid[r['id']];did=f'{NAME}:{r["bank"]}:{r["key"]}'
        assert e['development_diagnostic_selection']==did and did in e['decision_ids']
        assert e['source_sha256']==r['source_sha256'] and e['release_selection'] is None and not e['distribution_eligible']
        assert resolve(ds[did])==r['wording_proposal']['proposed'] and ds[did]['approval'] is None and not ds[did]['distribution_eligible']
    plan,outputs=derive_grouping(json.loads((ROOT/'config'/PARENT).read_text(encoding='utf8')))
    plan=copy.deepcopy(plan);outputs=dict(outputs);parent=dict(outputs)
    overrides={(r['bank'],r['key']):r['wording_proposal'] for r in rs}
    oldstatic=outputs[PREFIX+'static.dat'];static=bytearray(oldstatic[:4]);static_changed=[]
    for key,payload in static_rows(oldstatic):
        if ('static',key) in overrides:
            r=overrides['static',key];assert payload==r['before'].encode('utf8');payload=r['proposed'].encode('utf8');static_changed.append(key)
        static.extend(struct.pack('<IH',key,len(payload)));static.extend(payload)
    assert set(static_changed)==STATIC
    olddir=outputs[PREFIX+'dir.dat'];oldtrans=outputs[PREFIX+'trans.dat'];trans=bytearray();directory=bytearray();changed=[]
    assert len(olddir)==860*20
    for at in range(0,len(olddir),20):
        key,ep,tp,el,tl,flag,res=struct.unpack_from('<IIIHHHH',olddir,at);payload=oldtrans[tp:tp+tl]
        if ('trans',key) in overrides:
            r=overrides['trans',key];assert payload==r['before'].encode('utf8');payload=r['proposed'].encode('utf8');changed.append(key)
        assert len(payload)<65536
        directory.extend(struct.pack('<IIIHHHH',key,ep,len(trans),el,len(payload),flag,res));trans.extend(payload)
    assert set(changed)==TRANS
    changes={PREFIX+'static.dat':bytes(static),PREFIX+'dir.dat':bytes(directory),PREFIX+'trans.dat':bytes(trans)}
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw
        plan['writes'].append(dict(owner='Human-approved exact17 frozen-v7 wording changes',path=path,offset=0,size=len(raw),source_size=len(original),expected_sha256=digest(original),final_sha256=digest(raw),derivation='Immutable source through schema20;5 static labels/12 trans payloads only;retain all remaining payloads/order/English fields/flags;recalculate trans offsets/lengths.'))
    assert all(outputs[path]==raw for path,raw in parent.items() if path not in changes)
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg
    plan['approved_review17']=dict(approval=APPROVAL,static_keys=sorted(STATIC),trans_keys=sorted(TRANS),new_selected=0,selected=3569,held=404,native_new_payload_validation_pending=True,release_eligible=False)
    plan['font']['scope']='Same selected3569 plus2 derived Book roles;only exact17 human-selected wording changes;full wording/layout/release review pending.'
    return plan,outputs


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);p.parse_args();select()

"""User's exact alternative shortening in3541, retaining the final rhetorical question."""
import argparse,copy,json,re,shutil,struct
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve

NAME='dialogue3541_20261026';CONFIG='development_'+NAME+'.json';BASE=ROOT/'workspace/translation'
PACKET='workspace/translation/review/20261025_schema23_inventory_v16/packet.json'
APPROVAL='workspace/translation/approvals/20261026_dialogue3541.json';AUTHOR='workspace/translation/authored/dialogue3541_20261026.json'
PARENT='development_optional6_20261025.json';PARENT_SHA='7df1aca5d467902301ab8a575aae7e523944d6b2639250bc2b1c2566f67a52e7'
BEFORE='그리고 말이야. 저기 프라이스와';AFTER='그리고, 프라이스와';PREFIX='PSP_GAME/USRDIR/locale/en_us_'
ANSWER="'그리고 말이야. 저기 프라이스와' 부분을 '그리고, 프라이스와'로 줄이면 될거 같은데"

def pair():
    packet=json.loads((ROOT/PACKET).read_text(encoding='utf8'));assert packet['artifact_sha256']==PARENT_SHA
    row=next(r for r in packet['records'] if r['bank']=='trans' and r['key']==3541 and r['status']=='selected')
    old=row['wording'];assert old.count(BEFORE)==1 and old.endswith('하지만 날 탓할 수 있겠나?')
    new=old.replace(BEFORE,AFTER,1);assert new.startswith('[i_PI_DorianWalker]') and new.endswith('하지만 날 탓할 수 있겠나?')
    assert re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\d+|\r\n',old)==re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\d+|\r\n',new)
    assert len(new.encode())+1<=5000 and len(new.encode('utf-16le'))//2+1<=2048
    assert {c for c in new if 0xac00<=ord(c)<=0xd7a3}<={c for c in old if 0xac00<=ord(c)<=0xd7a3}
    return row,old,new

def approved():
    row,old,new=pair();a=json.loads((ROOT/APPROVAL).read_text(encoding='utf8'));author=json.loads((ROOT/AUTHOR).read_text(encoding='utf8'))
    assert a['user_answer']==ANSWER and a['exact_before_fragment']==BEFORE and a['exact_after_fragment']==AFTER
    assert a['before']==old and a['after']==new and a['source_sha256']==row['source_sha256']
    assert a['last_sentence_preserved'] and a['earlier_last_sentence_proposal_not_applied'] and not a['full_wording_layout_or_release_approval']
    assert author['records'][0]['text']==new and author['records'][0]['before']==old
    return row,old,new

def configuration():
    return dict(schema_version=24,policy='development_poc_non_distributable',parent_config=PARENT,parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),parent_artifact='workspace/runtime/optional6_20261025/artifact.json',parent_artifact_sha256=PARENT_SHA,packet=PACKET,packet_sha256=digest((ROOT/PACKET).read_bytes()),approval=APPROVAL,approval_sha256=digest((ROOT/APPROVAL).read_bytes()),author=AUTHOR,author_sha256=digest((ROOT/AUTHOR).read_bytes()),exact_trans_keys=[3541],scope='Only user-chosen preceding fragment in3541;preserveinitial아comma,finalrhetoricalquestion,allotherbody/portrait/numbers/controls/refs. Full wording/layout/release approval remains separate.',release_eligible=False)

def select():
    cp=ROOT/'qa/ssot/20261026_before_dialogue3541';assert not cp.exists() and not (ROOT/APPROVAL).exists() and not (ROOT/AUTHOR).exists()
    row,old,new=pair();entries=BASE/'entries.jsonl';raw=entries.read_bytes();oldlines=raw.splitlines(keepends=True);es=lines(entries);ds=decisions();assert len(es)==3973 and len(ds)==4425
    assert digest(raw)=='dc5724f7770eeb9b18daa4add1a8ba95698ba80df09780dc505f56329e11236d'
    e=next(e for e in es if e['id']==row['id']);previous=e['development_diagnostic_selection'];assert previous==row['decision'] and resolve(ds[previous])==old
    assert e['source_sha256']==row['source_sha256'] and e['release_selection'] is None and not e['distribution_eligible']
    for name in ['workspace/translation/entries.jsonl','workspace/translation/terminology.json','scripts/build_font_folder.py','scripts/book_role_runtime_20261024.py','scripts/manual_play_20261024.py','docs/HANDOFF.md','docs/HANDOFF_2026-10-26.md','qa/reports/continuation_queue_20261024.json','workspace/runtime/optional6_20261025/artifact.json','workspace/runtime/optional6_20261025/expected_writes.json']:
        p=cp/'previous'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
    terms_sha=digest((BASE/'terminology.json').read_bytes())
    a=dict(status='USER_ALTERNATIVE_EXACT_FRAGMENT_3541',authority='user',date_local='2026-10-26',user_answer=ANSWER,source_id=row['id'],source_sha256=row['source_sha256'],packet=PACKET,packet_sha256=digest((ROOT/PACKET).read_bytes()),exact_before_fragment=BEFORE,exact_after_fragment=AFTER,before=old,after=new,old_wording_sha256=digest(old.encode()),new_wording_sha256=digest(new.encode()),last_sentence_preserved=True,initial_아_comma_preserved=True,earlier_last_sentence_proposal_not_applied=True,preserved=['All other prose','100gold','Portrait','CRLF and control tags','DBrefs','Other keys and terms'],full_wording_layout_or_release_approval=False)
    protected_write(ROOT/APPROVAL,json.dumps(a,ensure_ascii=False,indent=2)+'\n')
    protected_write(ROOT/AUTHOR,json.dumps(dict(policy='Only this user-specified substring in3541;not lastsentence proposal or corpus normalization',records=[dict(id=row['id'],bank='trans',key=3541,source_sha256=row['source_sha256'],before=old,text=new,previous_decision=previous)]),ensure_ascii=False,indent=2)+'\n')
    did=NAME+':trans:3541';d=dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=AUTHOR,sha256=digest((ROOT/AUTHOR).read_bytes()),json_pointer='/records/0/text'),broader_decision_id=previous,applicability=dict(revision='ULKS46015-v1.01',context=NAME,scope='Exact user-selected preceding fragment3541only'),rationale='User chose precedingfragmentshortening instead of changing the finalrhetoricalquestion. Retainallothertext/100gold/portrait/refs.',semantic_impact='Removes spoken filleranddeictic저기;preservesbet/blamequestion. Actualnewpagination pending;no fullwording/layout/release approval.',human_wording_choice_ref=dict(path=APPROVAL,sha256=digest((ROOT/APPROVAL).read_bytes())),state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None)
    e.update(development_diagnostic_selection=did,current_working_decision=did,context_id=NAME);e['decision_ids'].append(did)
    protected_write(BASE/('decisions_'+NAME+'.jsonl'),serialized([d]));protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    newlines=[serialized([x]).encode('utf8') if x['id']==e['id'] else line for line,x in zip(oldlines,es)]
    assert sum(a!=b for a,b in zip(oldlines,newlines))==1 and sum(bool(x['development_diagnostic_selection']) for x in es)==3569
    tmp=entries.with_name('entries.dialogue3541.pending');assert not tmp.exists();tmp.write_bytes(b''.join(newlines));tmp.replace(entries)
    assert len(decisions())==4426 and digest((BASE/'terminology.json').read_bytes())==terms_sha
    result=dict(status='PASS_USER_ALTERNATIVE_FRAGMENT3541_SELECTED_SCHEMA24_BUILD_PENDING',authored=3973,selected=3569,held=404,derived=2,decisions=4426,only_one_entry_changed_other3972raw_lines_equal=True,terms_unchanged=True,entries_sha256=digest(entries.read_bytes()),approval=APPROVAL,earlier_last_sentence_proposal_not_applied=True,launcher_remains_verified23=True,new_runtime_or_release_approval=False)
    save_json(ROOT/'qa/reports/dialogue3541_20261026_selection.json',result);save_json(cp/'manifest.json',dict(status=result['status'],before_entries_sha256=digest(raw),after_entries_sha256=result['entries_sha256'],terms_sha256=terms_sha,old23_artifact_sha256=PARENT_SHA))
    p=ROOT/'qa/reports/continuation_queue_20261024.json';q=json.loads(p.read_text(encoding='utf8'));q.update(status='USER_ALTERNATIVE3541_FRAGMENT_SELECTED_SCHEMA24_BUILD_PENDING',owned63_closed=True,all_owned_through63_closed=True,latest_runtime_report='qa/reports/long_item_document63_20261026_runtime.json',decisions=4426,decision_history=4426,entries_sha256=result['entries_sha256'],pending_3541_wording=dict(answer_received=True,user_answer=ANSWER,approval=APPROVAL,exact_before_fragment=BEFORE,exact_after_fragment=AFTER,last_sentence_preserved=True,earlier_last_sentence_proposal_applied=False,selection_completed=True,new_build_runtime_pending=True),candidate_config='config/'+CONFIG,candidate_build='workspace/runtime/'+NAME+'/disc',current_launcher_still23=True,next_action='Buildsource24/readback only3541payload/78parentfilesunchanged. Fresh24coldoriginalprefetchnoold23states,full3541pages+lastquestion. Thenadoptlauncher/privatepackage/review;no ISO.');save_json(p,q)
    note='# 2026-10-26 사용자 대안3541 반영 / schema24 빌드 전\n\n사용자는마지막반문단축대신“그리고 말이야. 저기 프라이스와”→“그리고, 프라이스와”를선택했다.지정부분만바꿨으며앞의“아, ”와마지막“하지만 날 탓할 수 있겠나?”를유지한다.다른3972원고행·용어·수치100개·초상화·참조·제어문은그대로다.선택3569/보류404/파생2유지·결정4426이다.원고만반영됐고현재실행기/현재검증폴더는23이다.후속source24빌드와실제쪽넘김후채택한다.이전“날 탓하겠나?”제안은적용하지않았다.\n\n독립작업native63에서긴문서3674/3677을실제Info reader로각11쪽=22쪽과같은메뉴재열기2회확인·종료했다.참조2쓰기8바이트/CPU·정의84·T14·canonical1024·관리12/외부/사용자보존이며획득/전체52본문검증이아니다.62는빈선택포인터읽기의실행전거부로중단·정리했으며성공으로올리지않는다.문서목록은52개본문/57참조다.\n'
    (ROOT/'docs/DIALOGUE3541_2026-10-26.md').write_text(note,encoding='utf8',newline='\n');oldhandoff=(ROOT/'docs/HANDOFF.md').read_text(encoding='utf8')
    for n in ['docs/HANDOFF.md','docs/HANDOFF_2026-10-26.md']:(ROOT/n).write_text(note+'\n---\n\n'+oldhandoff,encoding='utf8',newline='\n')
    print(json.dumps(result,ensure_ascii=False))

def derive_dialogue3541(cfg):
    assert cfg==configuration();row,old,new=approved();did=NAME+':trans:3541';es={e['id']:e for e in lines(BASE/'entries.jsonl')};ds=decisions();e=es[row['id']]
    assert e['development_diagnostic_selection']==did and resolve(ds[did])==new and e['release_selection'] is None and not e['distribution_eligible']
    from optional6_20261025 import derive_optional6
    plan,outputs=derive_optional6(json.loads((ROOT/'config'/PARENT).read_text(encoding='utf8')))
    parent_art=ROOT/'workspace/runtime/optional6_20261025/artifact.json';assert digest(parent_art.read_bytes())==PARENT_SHA;parent=json.loads(parent_art.read_text(encoding='utf8'))
    for path,pin in plan['all_source_files'].items():
        raw=outputs.get(path);got=dict(size=len(raw),sha256=digest(raw)) if raw is not None else dict(size=pin['size'],sha256=pin['sha256']);assert got==parent['files'][path],('Parent23 source reconstruction drift',path)
    plan=copy.deepcopy(plan);outputs=dict(outputs);previous=dict(outputs);directory=bytearray();trans=bytearray();changed=[]
    olddir=outputs[PREFIX+'dir.dat'];oldtrans=outputs[PREFIX+'trans.dat'];assert len(olddir)==860*20
    for at in range(0,len(olddir),20):
        key,ep,tp,el,tl,flag,res=struct.unpack_from('<IIIHHHH',olddir,at);payload=oldtrans[tp:tp+tl]
        if key==3541:assert payload==old.encode();payload=new.encode();changed.append(key)
        assert len(payload)<65536;directory.extend(struct.pack('<IIIHHHH',key,ep,len(trans),el,len(payload),flag,res));trans.extend(payload)
    assert changed==[3541];changes={PREFIX+'dir.dat':bytes(directory),PREFIX+'trans.dat':bytes(trans)}
    plan['writes']=[w for w in plan['writes'] if w['path'] not in changes]
    for path,raw in changes.items():
        original=(ROOT/'extracted/disc'/path).read_bytes();outputs[path]=raw;plan['writes'].append(dict(owner='User exact preceding fragment3541',path=path,offset=0,size=len(raw),source_size=len(original),expected_sha256=digest(original),final_sha256=digest(raw),derivation='Immutable source through verifiedschema23;only3541UTF8payloadchanges. Retainallotherpayloads/English/order/flags;recalculateoffsets/lengths.'))
    assert {p for p in outputs if outputs[p]!=previous[p]}==set(changes)
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['diagnostic_input']=cfg;plan['approved_dialogue3541']=dict(approval=APPROVAL,trans_keys=[3541],last_sentence_preserved=True,earlier_short_last_sentence_proposal_not_applied=True,parent23_all80_source_derived_match=True,parent_other78_files_unchanged=True,native_validation_pending=True,release_eligible=False);plan['font']['scope']='Same font/code/WAD and selected3569+derived2. One exact user-chosen preceding fragment3541;fullwording/layout/release reviewpending.'
    return plan,outputs

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select']);p.parse_args();select()

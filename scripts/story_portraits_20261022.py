"""Exact source2705 repeated image order and2706 narrator-prefix development policy."""
import argparse,re,struct,json,unicodedata
from functools import lru_cache
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode,decode_unicode
from text_limits import check_template
import quest_batch_pipeline as pipeline
from main_story_drafts_20261020 import DRAFTS as OLD_DRAFTS
KEYS={2705,2706};DRAFTS={k:OLD_DRAFTS[k] for k in sorted(KEYS)}
NAME='story_portraits_20261022';POLICY='story2_original_repeated_portraits_narrator_prefix_segment_CRLF_2048_v1';BASE=ROOT/'workspace/translation'
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='button_hints_20261022',prior_config='development_button_hints_20261022.json',prior_config_sha256='08cd0391ed2822d5a6ff5f606b68498b9cf336824843a273d00153dbbe81c92b',prior_artifact_sha256='6a37a899d064aafd132e7e58b300bc7bce8c30f6748186bc6a058812cb6ea7a6',new_authored_count=0)

@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key'] in KEYS};assert set(ss)==KEYS
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for s in ss.values():
        b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    return ss

def context():
    from translation_scope import collect
    scope,_=collect();refs={r['key']:r['typed_references'] for r in scope if r['bank']=='trans' and r['key'] in KEYS};expected={2705:[(15,65,32)],2706:[(15,65,36)]}
    fields={k:[(r['table'],r['row'],r['field']) for r in rr] for k,rr in refs.items()};assert fields==expected
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    a,na=struct.unpack_from('<II',db,112);b,nb=struct.unpack_from('<II',db,120);q=db[a+29*44:a+30*44];r=db[b+65*56:b+66*56]
    assert struct.unpack_from('<2h',q,18)==(65,66) and struct.unpack_from('<I',r,32)[0]==2705 and struct.unpack_from('<I',r,36)[0]==2706
    wad=(ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad').read_bytes();assert digest(wad)=='696b7618de5fc7c2610666b7b9f543ec2be5e91bcd0bcdd86c20d0d5db47870d'
    wi=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));assets={}
    for name in ['PI_KayleeEvil1','PI_KayleeEvil2','PI_KayleeEvil3','PI_GoodKaylee']:
        matches=[e for e in wi['entries'] if e['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+name];assert len(matches)==1
        x=matches[0];assert digest(wad[x['offset']:x['offset']+x['size_candidate']])==x['sha256'];assets[name]=x
    tags={k:re.findall(r'\[i_[^]]+\]',s['source_text']) for k,s in sources().items()};assert tags[2705]==['[i_PI_KayleeEvil1]','[i_PI_KayleeEvil2]','[i_PI_KayleeEvil2]','[i_PI_KayleeEvil3]'] and tags[2706]==['[i_PI_GoodKaylee]']
    return dict(fields=fields,complete_table14_row29=q.hex(),complete_table15_row65=r.hex(),source_quest_command_kind=r[52],actor_format_hash_table14_field12=struct.unpack_from('<I',q,12)[0],assets=assets,
        source_control_boundary='2705 preserves repeated Evil2 tag as a separate consumption-order event.2706 retains third-person narration before the first GoodKaylee tag and quoted speech afterwards.',
        formatter_scope='Original table15+32/+36 paths and actors are distinct from common table14row40 fixture. No original mode6/7 natural trigger or geometry assumed.',
        build_policy_adopted=True,source_runtime='qa/reports/story_portraits_source_20261022_runtime.json',release_eligible=False)

FIELDS=context()['fields']

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    k=r['key'];s=sources()[k]['source_text'];t=r['text'];assert r['source_text']==s and t and t==unicodedata.normalize('NFC',t)
    tags=re.findall(r'\[[^\]]+\]',s);assert all(re.fullmatch(r'\[i_[A-Za-z0-9_]+\]',tag) for tag in tags) and re.findall(r'\[[^\]]+\]',t)==tags
    if k==2705:
        assert tags==['[i_PI_KayleeEvil1]','[i_PI_KayleeEvil2]','[i_PI_KayleeEvil2]','[i_PI_KayleeEvil3]'] and s.startswith(tags[0]) and t.startswith(tags[0])
    else:
        assert tags==['[i_PI_GoodKaylee]']
        for text in [s,t]:
            prefix,spoken=text.split(tags[0]);assert prefix.strip() and '"' not in prefix and spoken.startswith('"')
        assert t.count('"')==s.count('"')==8
    for a,b in zip(re.split(r'\[i_[^]]+\]',s),re.split(r'\[i_[^]]+\]',t)):assert re.findall(r'\r\n+',a)==re.findall(r'\r\n+',b)
    body=re.sub(r'\[i_[^]]+\]','',t);assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    data=encoder(t,book).encode('utf8');assert decoder(data.decode('utf8'),book)==t and len(data)<=5000
    check_template(t,'Exact story2 2048wide input; ordered duplicate tags/narrator retained, original event geometry separate')
    return data

def select():
    evidence=json.loads((ROOT/'qa/reports/story_portraits_source_20261022_runtime.json').read_text(encoding='utf8'));assert evidence['keys']==[2705,2706] and evidence['exact_all_tag_positions']
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256'];cfg=json.loads(cfgpath.read_text(encoding='utf8'))
    es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};byid={e['id']:e for e in es};ds=decisions();assert len(ds)==4329
    src=sources();rows={k:dict(key=k,source_text=src[k]['source_text'],text=t,control_policy=POLICY) for k,t in DRAFTS.items()}
    for r in rows.values():validate(r,pipeline.BOOK,encode_unicode,decode_unicode)
    negative=[]
    tests=[(2705,'wrong_source',dict(source_text='wrong')),(2705,'outside_scope',dict(key=3115)),(2705,'duplicate_deduped',dict(text=DRAFTS[2705].replace('[i_PI_KayleeEvil2]','',1))),
        (2705,'wrong_portrait_order',dict(text=DRAFTS[2705].replace('[i_PI_KayleeEvil1]','[i_PI_KayleeEvil3]',1))),
        (2706,'portrait_moved_to_front',dict(text='[i_PI_GoodKaylee]'+DRAFTS[2706].replace('[i_PI_GoodKaylee]',''))),
        (2706,'narration_assigned_as_quote',dict(text='"'+DRAFTS[2706])),(2705,'segment_break_lost',dict(text=DRAFTS[2705].replace('\r\n\r\n','',1))),
        (2706,'new_page_control',dict(text=DRAFTS[2706]+'[p]')),(2705,'NUL',dict(text=DRAFTS[2705]+'\0')),(2705,'overflow',dict(text=DRAFTS[2705]+'가'*2048))]
    for k,label,change in tests:
        try:validate(dict(rows[k],**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261022_before_story_portraits';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for k,r in rows.items():
        e=byid[src[k]['id']];old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==DRAFTS[k]
        did=f'development_{NAME}:trans:{k}';records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=ds[old]['wording_ref'],broader_decision_id=old,
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact table15row65 fields32/36; no DB/code/portrait asset changes'),
            rationale='Source image records match all four ordered2705 tags including repeated Evil2 and337-unit narrator prefix before2706 image. Preserve old wording, segment CRLF and quotations.',
            semantic_impact='Narrator text remains narration, never assigned wholesale to Kaylee. Existing late-story voice/names human review pending; common fixture is not natural mode6/7 event proof.',state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    target={r['source_id'] for r in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in target)
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4331 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_TWO_UNCHANGED_STORY_PORTRAIT_DRAFTS_DEVELOPMENT_SELECTED',authored=3973,selected=3533,working_unselected=440,decision_history=4331,new_authored=0,new_selected=2,negative_cases=negative,
        previous_wording_and_refs_unchanged=True,duplicate_image_tag_preserved=True,narrator_prefix_and_quote_boundary_preserved=True,actual_original_mode6_or7_runtime_pending=True,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='select':select()
    else:pipeline.audit(SPEC,__import__('story_portraits_20261022'),DRAFTS,{})

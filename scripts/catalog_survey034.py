"""Protected source catalog and limited-context draft references; no bulk prose."""
import json,re,struct
from collections import Counter,defaultdict
from survey import ROOT,digest,save_json
from psp_folder import sha

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
def serialized(rows):return ''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows)
def protected_write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_text(encoding='utf-8')==text,'Protected baseline changed: '+str(path)
    else:path.write_text(text,encoding='utf-8')

def main():
    inventory=load(ROOT/'manifests/iso_inventory.json');items={r['path']:r for r in inventory['files']}
    source_paths={'static':'PSP_GAME/USRDIR/locale/en_us_static.dat','trans':'PSP_GAME/USRDIR/locale/en_us_trans.dat','rsc':'PSP_GAME/USRDIR/res/strings.rsc','dir':'PSP_GAME/USRDIR/locale/en_us_dir.dat'}
    source={}
    for bank,path in source_paths.items():
        raw=(ROOT/'extracted/disc'/path).read_bytes();assert len(raw)==items[path]['size'] and digest(raw)==items[path]['sha256'];source[bank]=raw
    candidates={'static':'en_us_static_candidates.jsonl','trans':'en_us_trans_candidates.jsonl','rsc':'ui_rsc_candidates.jsonl'}
    parsed={bank:lines(ROOT/'extracted/text'/filename) for bank,filename in candidates.items()}
    assert {b:len(r) for b,r in parsed.items()}=={'static':2852,'trans':858,'rsc':263}
    # Independent source walks validate every boundary against the old extraction.
    pos=4
    for r in parsed['static']:
        key,size=struct.unpack_from('<IH',source['static'],pos)
        assert (key,pos,pos+6,size)==(r['key'],r['record_offset'],r['offset'],r['byte_length']);pos+=6+size
    assert pos==len(source['static'])
    end=0
    for i,r in enumerate(parsed['trans']):
        rec=struct.unpack_from('<IIIHHHH',source['dir'],i*20)
        assert list(rec)==r['directory_fields'] and (rec[0],rec[2],rec[4])==(r['key'],r['offset'],r['byte_length']) and rec[2]==end
        end+=rec[4]
    assert end==len(source['trans']) and len(source['dir'])==len(parsed['trans'])*20
    offsets=struct.unpack_from('<263I',source['rsc'],4);assert struct.unpack_from('<I',source['rsc'])[0]==263 and offsets[0]==1056
    for i,r in enumerate(parsed['rsc']):
        start=offsets[i];size=struct.unpack_from('<I',source['rsc'],start)[0];end=offsets[i+1] if i+1<263 else len(source['rsc'])
        assert (r['key'],r['record_offset'],r['offset'],r['length_field'])==(i,start,start+4,size)
        assert source['rsc'][start+4+size-2:start+4+size]==b'\0\0' and source['rsc'][start+4+size:end].hex()==r['padding_hex']
    cfg_path=ROOT/'config/diagnostic_name031.json';cfg=load(cfg_path);drafts={r['key']:(i,r) for i,r in enumerate(cfg['static_overrides'])};assert len(drafts)==35
    scope_groups=[('main_menu',[3841,2769,2750,2833],'20261017_025_emucap_menu/menu_kr_default.png'),
                  ('class_selection',[2668,2670,2687,2688,2689,2690,2693,2694,2696,2697],'20261017_027_emucap_class/alchemist_kr.png'),
                  ('appearance',[2674,2673,2886,2672],'20261017_028_emucap_appearance/appearance_kr.png'),
                  ('attributes',[2120,2121,2122,2123,2124,2125,2126,2127,2682,2683,2554],'20261017_029_emucap_attributes/strength_kr.png'),
                  ('remaining_points_notice',[2951,2144],'20261017_030_emucap_notice/notice_kr.png'),
                  ('name_keyboard',[3992,3072,3506,2685],'20261017_031_emucap_name/name_kr.png')]
    context_for={key:name for name,keys,p in scope_groups for key in keys};assert set(context_for)==set(drafts)
    base=ROOT/'workspace/translation';baseline=[];work=[];decisions=[];duplicates=defaultdict(list);stats={}
    for bank,rows in parsed.items():
        lengths=[];tokens=Counter();chars=Counter();words=0;spans=set()
        for ordinal,r in enumerate(rows):
            raw=bytes.fromhex(r['source_hex']);text=r['source_text'];offset=r['offset'];encoding=r['encoding_candidate']
            assert source[bank][offset:offset+len(raw)]==raw and digest(raw)==r['source_sha256'] and text.encode(encoding)==raw
            stable='ULKS46015-v1.01:'+r['id'];spans.add((offset,len(raw)));units=len(text.encode('utf-16le'))//2
            record={'id':stable,'bank':bank,'ordinal':ordinal,'source_path':source_paths[bank],'source_file_sha256':items[source_paths[bank]]['sha256'],
                    'source_candidate_id':r['id'],'key':r['key'],'offset':offset,'byte_length':len(raw),'source_hex':raw.hex(),'source_sha256':digest(raw),
                    'source_text':text,'encoding':encoding,'source_utf16_units':units,'token_candidates':r['token_candidates'],
                    'structural_fields':{k:r[k] for k in ['record_offset','key_occurrence','directory_record_offset','directory_fields','length_field','padding_hex','english_hex','english_text','english_encoding_candidate'] if k in r}}
            baseline.append(record);decision=None
            if bank=='static' and r['key'] in drafts:
                index,d=drafts[r['key']];assert text==d['source_text'];decision='diagnostic031:'+str(r['key'])
                decisions.append({'id':decision,'source_id':stable,'applicability':{'revision':'ULKS46015-v1.01','context':context_for[r['key']]},
                                  'wording_ref':{'path':'config/diagnostic_name031.json','sha256':sha(cfg_path),'json_pointer':f'/static_overrides/{index}/text'},
                                  'broader_decision_id':None,'rationale':'Contextual development diagnostic observed in emulator; no approved release wording exists',
                                  'semantic_impact':'Draft wording; terminology and style pending human review','approval':None,'state':'needs_human_review','distribution_eligible':False})
            work.append({'id':stable,'source_ref':stable,'source_sha256':digest(raw),'context_id':context_for.get(r['key']) if bank=='static' else None,
                         'state':'needs_human_review' if decision else 'untranslated','decision_ids':[decision] if decision else [],
                         'development_diagnostic_selection':decision,'release_selection':None,'distribution_eligible':False})
            duplicates[digest(text.encode('utf-8'))].append(stable);lengths.append(units);chars.update(text);tokens.update(r['token_candidates']);words+=len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text))
        stats[bank]={'structurally_enumerated_records':len(rows),'distinct_storage_spans':len(spans),'unique_decoded_texts':len({r['source_text'] for r in rows}),
                     'empty_records':sum(r['byte_length']==0 for r in rows),'source_payload_bytes':sum(r['byte_length'] for r in rows),'source_utf16_units':sum(lengths),
                     'source_latin_word_tokens':words,'max_source_utf16_units':max(lengths),'entries_over_2047_units':sum(n>2047 for n in lengths),
                     'over_2047_interpretation':'investigation candidates only; observed2047 decoder bound is not established for all consumer paths',
                     'unique_codepoints':len(chars),'token_candidate_entries':sum(bool(r['token_candidates']) for r in rows),'token_candidates':dict(tokens)}
    assert len(baseline)==len(work)==3973 and len({r['id'] for r in baseline})==3973 and len(decisions)==35
    protected_write(base/'baseline/source_entries.jsonl',serialized(baseline));baseline_sha=sha(base/'baseline/source_entries.jsonl')
    header={'schema_version':1,'supported_source_sha256':inventory['source_sha256'],'source_revision':'ULKS46015-v1.01','source_paths':{p:items[p]['sha256'] for p in source_paths.values()},
            'entry_count':3973,'baseline_sha256':baseline_sha,'protected_fields':'Every baseline field; regenerate from immutable extraction for a structural change',
            'scope':'Three enumerated English text banks, not complete game extraction or confirmed translation completion denominator',
            'diagnostic_config_sha256':sha(cfg_path),'default_distribution_eligible':False}
    protected_write(base/'baseline/manifest.json',json.dumps(header,ensure_ascii=False,indent=2)+'\n')
    protected_write(base/'diagnostic_decisions.jsonl',serialized(decisions))
    workpath=base/'entries.jsonl'
    if not workpath.exists():workpath.write_text(serialized(work),encoding='utf-8')
    current=lines(workpath);assert [r['id'] for r in current]==[r['id'] for r in work]
    for a,b in zip(current,work):assert (a['id'],a['source_ref'],a['source_sha256'])==(b['id'],b['source_ref'],b['source_sha256'])
    all_decisions={}
    for p in [base/'diagnostic_decisions.jsonl',*sorted(base.glob('decisions_*.jsonl'))]:
        for d in lines(p):
            assert d['id'] not in all_decisions and d['source_id'] in {r['id'] for r in baseline}
            ref=d['wording_ref'];config_file=ROOT/ref['path'];assert sha(config_file)==ref['sha256']
            value=load(config_file)
            for part in ref['json_pointer'].strip('/').split('/'):value=value[int(part)] if isinstance(value,list) else value[part]
            assert isinstance(value,str) and value
            assert d['state'] in ['in_progress','needs_review','needs_human_review','distribution_eligible']
            if d['distribution_eligible']:assert d['approval'] and d['state']=='distribution_eligible'
            all_decisions[d['id']]=d
    for r in current:
        assert r['state'] in ['untranslated','in_progress','needs_review','needs_human_review','distribution_eligible']
        assert all(i in all_decisions and all_decisions[i]['source_id']==r['id'] for i in r['decision_ids'])
        if r['development_diagnostic_selection']:assert r['development_diagnostic_selection'] in r['decision_ids']
        if r['release_selection']:assert r['release_selection'] in r['decision_ids'] and all_decisions[r['release_selection']]['distribution_eligible']
        if r['distribution_eligible']:assert r['release_selection'] and r['state']=='distribution_eligible'
    contexts=[{'id':name,'source_ids':['ULKS46015-v1.01:en_us/static:'+str(k)+':occurrence1' for k in keys],
               'evidence':'qa/runtime/'+p,'source_consumer':'705DC/DA634 formatted lookup; observed2048capacity output buffer reserves NUL',
               'interpretation_limits':'Local UI context established; global term/style approval and complete playthrough remain pending'} for name,keys,p in scope_groups]
    for r in contexts:assert (ROOT/r['evidence']).is_file()
    protected_write(base/'contexts.json',json.dumps(contexts,ensure_ascii=False,indent=2)+'\n')
    specs={'schema_version':1,'consumer_scope':'Only the35 observed static UI entries referenced by diagnostic031; other entries are not implicitly covered',
           'policy':'Preserve token order and arguments; no literal escaping convention is adopted for unobserved syntax',
           'buttons':{s:{'source_hex':s.encode().hex(),'source_bytes':2,'output_u16':n} for s,n in {'$u':134,'$d':135,'$e':133,'$w':132,'$x':131,'$c':128,'$t':129,'$r':137}.items()},
           'variables':[{'token':'$a','source_bytes':2,'scope_key':2682,'observed_values':['10','9','10'],'policy':'preserve','interpretation':'available attribute points'}],
           'unresolved':'Square/curly forms,other dollar letters and cross-bank use remain regex candidates, not adopted control specifications'}
    protected_write(base/'control_specs_observed.json',json.dumps(specs,ensure_ascii=False,indent=2)+'\n')
    dup=[{'text_sha256':h,'source_ids':ids,'merge_authorized':False} for h,ids in duplicates.items() if len(ids)>1]
    protected_write(base/'baseline/duplicate_text_groups.json',json.dumps(dup,ensure_ascii=False,indent=2)+'\n')
    report={'status':'PASS_SOURCE_CATALOG_VOLUME_SURVEY','release_eligible':False,'banks':stats,'structurally_enumerated_entries':3973,
            'unique_decoded_texts_across_banks':len(duplicates),'duplicate_decoded_text_groups':len(dup),'diagnostic031_references':35,'current_wording_decisions':len(all_decisions),
            'work_states':dict(Counter(r['state'] for r in current)),'approved_translations':sum(bool(d['approval']) for d in all_decisions.values()),
            'approved_terminology_decisions':len(load(base/'terminology.json')['approved_decisions']),'full_prose_generated':False,
            'full_game_translation_denominator_established':False,
            'unresolved_containers':['WAD non-font payloads/graphics text','BOOT and module inline strings','Possible video/audio subtitle paths in unenumerated assets; no standalone PMF in ISO inventory','other execution paths and locale extra/core applicability'],
            'next_evidence':'Trace remaining text consumers and script/control syntax; classify enumerated entries by functional context before scaling prose',
            'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'size':p.stat().st_size} for p in sorted(base.rglob('*')) if p.is_file()]}
    save_json(ROOT/'qa/reports/catalog_stage034_survey.json',report)
    print({k:v for k,v in report.items() if k not in ['banks','files']})
    print({bank:{k:v for k,v in s.items() if k!='token_candidates'} for bank,s in stats.items()})

if __name__=='__main__':main()

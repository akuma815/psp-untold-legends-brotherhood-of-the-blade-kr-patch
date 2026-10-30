"""Current workload inside three parsed banks; never a whole-game denominator."""
import json, re, struct
from collections import Counter, defaultdict
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized

BASE = ROOT / 'workspace/translation'
DB_SHA = 'd852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'

def collect():
    sources = lines(BASE / 'baseline/source_entries.jsonl')
    entries = {e['id']: e for e in lines(BASE / 'entries.jsonl')}
    assert len(sources) == len(entries) == 3973
    assert digest((BASE/'baseline/source_entries.jsonl').read_bytes()) == 'c7fe5566710004c2d44ae37d91e78c8cb44069dbb42456a10697b37a2407b872'
    lookup = defaultdict(list)
    for s in sources:
        lookup[s['bank'], s['key']].append(s)
    db = (ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db) == DB_SHA
    refs, unresolved = defaultdict(list), []
    from fallback_names_20261021 import EXPECTED, population
    population()  # Pins all conditional trans-name references to complete source rows.
    # Widths are consumer-derived, not arbitrary integer searches.
    specs = [(16, 2, 0, 2, 'static', 'map_title'),
             (5, 84, 0, 2, 'static', 'item_name'),
             (6,28,0,2,'static','item_quality_prefix'),
             (7,64,0,2,'static','item_effect_suffix'),
             (5,84,72,4,'trans','category13_item_document'),
             (2, 112, 0, 2, 'static', 'actor_name'),
             (12,92,64,4,'trans','ability_numeric_description'),
             (12,92,60,4,'static','ability_title'),
             (7,64,44,4,'trans','equipment_effect_description'),
             *[(13,260,f,4,'trans','npc_dialogue') for f in range(4,260,4)],
             *[(14,44,f,4,'trans',role) for f,role in [(0,'quest_start_dialogue'),(4,'quest_completion_message'),(8,'entry_thought_separate')]],
             *[(15,56,f,4,'trans',role) for f,role in [(24,'Book_body'),(28,'mode5_separate'),(32,'quest_dialogue'),(36,'completion_event_message'),(40,'quest_title')]]]
    tables = {}
    for table, stride, field, width, bank, role in specs:
        offset, count = struct.unpack_from('<II', db, table*8)
        assert offset + count*stride <= len(db)
        tables[table] = dict(offset=offset, rows=count, stride=stride)
        for row in range(count):
            if role=='category13_item_document' and db[offset+row*stride+59]!=13:continue
            at = offset + row*stride + field
            key = int.from_bytes(db[at:at+width], 'little')
            if role=='item_effect_suffix' and key==0:continue # Original6FF94 explicitly skips nonpositive suffix keys.
            if key == (1 << (width*8))-1:
                continue
            ref = dict(table=table,row=row,field=field,width=width,offset=at,expected_hex=db[at:at+width].hex(),role=role,key=key)
            found = lookup[bank,key]
            if not found and bank=='static' and key in EXPECTED and EXPECTED[key]==(table,row,field,width):
                found=lookup['trans',key]
                ref.update(lookup_route='conditional common-key cache miss -> trans directory',consumer_evidence='scripts/fallback_names_20261021.py',natural_bank_choice_verified=False)
            if len(found) == 1:
                refs[found[0]['id']].append(ref)
            else:
                unresolved.append(dict(bank=bank,reference=ref,matching_catalog_records=len(found)))
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    from stat_help_20261021 import population as stat_population
    for key,item in stat_population().items():
        found=lookup['static',key];assert len(found)==1
        for ref in item['references']:
            refs[found[0]['id']].append(dict(ref,table=None,row=None,field=None,key=key,consumer_evidence='scripts/stat_help_20261021.py'))
    from ui_direct_20261021 import population as ui_direct_population
    for key,item in ui_direct_population().items():
        found=lookup['static',key];assert len(found)==1
        for ref in item['references']:refs[found[0]['id']].append(dict(ref,table=None,row=None,field=None,consumer_evidence='scripts/ui_direct_20261021.py'))
    from hud_errors_20261021 import population as hud_population
    from item_events_20261021 import population as event_population
    from ui_wrappers_20261021 import population as wrapper_population
    from ui_confirmations_20261021 import population as confirmation_population
    for policy,population in [('hud_errors_20261021',hud_population),('item_events_20261021',event_population),('ui_wrappers_20261021',wrapper_population),('ui_confirmations_20261021',confirmation_population)]:
        for key,item in population().items():
            found=lookup['static',key];assert len(found)==1
            for ref in item['references']:refs[found[0]['id']].append(dict(ref,table=None,row=None,field=None,consumer_evidence='scripts/'+policy+'.py'))
    for key,pc in [(2098,0x70110),(3080,0x70124),(2108,0x70134),(2099,0x70144)]:
        assert struct.unpack_from('<I',boot,pc+128)[0]==0x34060000|key
        found=lookup['static',key];assert len(found)==1
        refs[found[0]['id']].append(dict(table=None,row=None,field=None,width=4,offset=pc+128,expected_hex=boot[pc+128:pc+132].hex(),
            source_path='PSP_GAME/SYSDIR/BOOT.BIN',role='item_name_format_control',key=key,consumer_evidence='scripts/item_affixes_20261021.py'))
    for key,pc,selector in [(3882,0x709d4,1),(4004,0x709e8,2),(4005,0x709f8,3)]:
        word=struct.unpack_from('<I',boot,pc+128)[0];assert word==0x34060000|key
        found=lookup['trans',key];assert len(found)==1
        refs[found[0]['id']].append(dict(table=None,row=None,field=None,width=4,offset=pc+128,expected_hex=boot[pc+128:pc+132].hex(),
            source_path='PSP_GAME/SYSDIR/BOOT.BIN',role='epilogue_scroll',key=key,selector=selector,consumer_evidence='scripts/epilogue_policy_20261020.py'))
    # Direct-code consumers need their own typed records; DB-cell absence is
    # not absence of a consumer. Numeric count3087 has source-call proof only.
    for bank,key,pc,call_pc,target,reg,role,evidence in [
        ('trans',3991,0x4c504,0x4c500,0x705dc,5,'victory_journal_direct','scripts/victory_journal_20261024.py'),
        ('static',3085,0x6f9b8,0x6f9b4,0x6f390,5,'numeric_range_template','scripts/trace_numeric_owners_20261024.py'),
        ('static',3086,0x6f9dc,0x6f9d8,0x6f390,5,'numeric_ratio_template','scripts/trace_numeric_owners_20261024.py'),
        ('static',3087,0x6f9fc,0x6f9f8,0x6f168,6,'numeric_count_template','scripts/trace_numeric_owners_20261024.py')]:
        assert struct.unpack_from('<I',boot,pc+128)[0]==0x34000000|(reg<<16)|key
        assert struct.unpack_from('<I',boot,call_pc+128)[0]==0x0c000000|(target>>2)
        found=lookup[bank,key];assert len(found)==1
        refs[found[0]['id']].append(dict(table=None,row=None,field=None,width=4,offset=pc+128,
            expected_hex=boot[pc+128:pc+132].hex(),source_path='PSP_GAME/SYSDIR/BOOT.BIN',role=role,key=key,
            call_pc=call_pc,target=target,consumer_evidence=evidence,natural_runtime_claim='not inferred from static reference'))
    # Adopted finite source result,not a heuristic scan or runtime experiment.
    supplement_path=BASE/'scope/selected_consumer_spec_20261024.json'
    assert digest(supplement_path.read_bytes())=='0b22c0652bfdf2e077ebeac65a71f22fd5fd35be7b5c0837a76036a1ca4f7098'
    supplement=json.loads(supplement_path.read_text(encoding='utf-8'))
    assert supplement['supported_source_BOOT_sha256']==digest(boot) and supplement['supported_source_DB_sha256']==digest(db)
    source_by_id={s['id']:s for s in sources}
    for identity,additional in supplement['references_by_id'].items():
        source=source_by_id[identity];assert not refs[identity]
        for ref in additional:
            assert source['bank']==ref['bank'] and source['key']==ref['key']
            assert ref['source_path'] in ['PSP_GAME/SYSDIR/BOOT.BIN','PSP_GAME/USRDIR/res/gam_db_T4']
            raw=boot if ref['source_path'].endswith('BOOT.BIN') else db
            assert raw[ref['offset']:ref['offset']+ref['width']].hex()==ref['expected_hex']
            refs[identity].append(dict(ref,table=ref.get('table'),row=ref.get('row'),field=ref.get('field')))
    file_cache = {}
    rows, texts = [], defaultdict(list)
    for s in sources:
        rawfile = file_cache.setdefault(s['source_path'], (ROOT/'extracted/disc'/s['source_path']).read_bytes())
        raw = rawfile[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex() == s['source_hex'] and digest(raw) == s['source_sha256']
        assert s['source_text'].encode(s['encoding']) == raw
        e = entries[s['id']]
        assert e['source_ref'] == s['id'] and e['source_sha256'] == s['source_sha256']
        texts[s['source_text']].append(s['id'])
        rows.append(dict(id=s['id'],bank=s['bank'],key=s['key'],state=e['state'],authored=e['state']!='untranslated',
                         selected=bool(e['development_diagnostic_selection']),source_utf16_units=s['source_utf16_units'],
                         payload_bytes=s['byte_length'],latin_word_tokens=len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",s['source_text'])),
                         typed_references=refs[s['id']],consumer_classified=bool(refs[s['id']]),
                         translation_eligibility='per-unit context and token policy required; typed reference alone is insufficient'))
    banks = {}
    for bank in ['static','trans','rsc']:
        rr = [r for r in rows if r['bank']==bank]
        banks[bank] = dict(records=len(rr),physical_spans=len({(s['offset'],s['byte_length']) for s in sources if s['bank']==bank}),
                           unique_source_values=len({s['source_text'] for s in sources if s['bank']==bank}),
                           source_utf16_units=sum(r['source_utf16_units'] for r in rr),payload_bytes=sum(r['payload_bytes'] for r in rr),
                           latin_word_tokens=sum(r['latin_word_tokens'] for r in rr),authored=sum(r['authored'] for r in rr),selected=sum(r['selected'] for r in rr),
                           authored_source_utf16_units=sum(r['source_utf16_units'] for r in rr if r['authored']),
                           selected_source_utf16_units=sum(r['source_utf16_units'] for r in rr if r['selected']),
                           states=dict(Counter(r['state'] for r in rr)),typed_context_candidates=sum(r['consumer_classified'] for r in rr))
    scopes = {}
    for role in sorted({ref['role'] for rr in refs.values() for ref in rr}):
        rr=[r for r in rows if any(x['role']==role for x in r['typed_references'])]
        scopes[role]=dict(logical_entries=len(rr),reference_cells=sum(x['role']==role for r in rr for x in r['typed_references']),
                         authored=sum(r['authored'] for r in rr),selected=sum(r['selected'] for r in rr),
                         source_utf16_units=sum(r['source_utf16_units'] for r in rr))
    inventory=json.loads((ROOT/'manifests/iso_inventory.json').read_text(encoding='utf8'))
    empty_english=[f for f in inventory['files'] if re.search(r'/en_us_(core|extra)\.dat$',f['path'])]
    assert len(empty_english)==2 and all(f['size']==0 for f in empty_english)
    report=dict(status='PASS_ENUMERATED_BANK_WORKLOAD_NOT_WHOLE_GAME',source_sha256=inventory['source_sha256'],
                baseline_sha256=digest((BASE/'baseline/source_entries.jsonl').read_bytes()),entries_sha256=digest((BASE/'entries.jsonl').read_bytes()),
                structurally_enumerated_records=len(rows),unique_decoded_values=len(texts),duplicate_groups=sum(len(v)>1 for v in texts.values()),
                duplicate_record_excess=sum(len(v)-1 for v in texts.values()),duplicates_are_not_merge_authorization=True,
                authored=sum(r['authored'] for r in rows),selected=sum(r['selected'] for r in rows),banks=banks,consumer_scopes=scopes,tables=tables,
                reference_catalog_mismatches=unresolved,unclassified_records=sum(not r['consumer_classified'] for r in rows),
                role_counts_overlap=True,full_game_denominator_established=False,full_game_percentage=None,
                known_empty_english_containers=empty_english,
                unresolved_outside_catalog=[
                    dict(scope='WAD non-font payloads and graphic text',condition='Enumerate graphic assets and prove consumer/text classification; string searches cannot exclude them'),
                    dict(scope='BOOT/module inline literals',condition='Bind code references to user-visible consumers; ASCII hits alone are candidates'),
                    dict(scope='embedded cinematic/audio subtitle paths',condition='Resolve asset and consumer catalog; no standalone PMF in ISO is not absence proof'),
                    dict(scope='en_us_eng.dat and resource fallback/alternate execution paths',condition='Prove loader applicability and mapping; do not double-count mirrored strings or exclude fallback silently')],
                local_scaling_scope='Original table16 Map titles: exhaustively enumerable 113 cells/113 records; other scopes need their own context eligibility',
                established_source_consumer_supplement=dict(path=supplement_path.relative_to(ROOT).as_posix(),sha256=digest(supplement_path.read_bytes()),logical_records=80,references=127),
                approvals_and_release=0)
    return rows, report

def main():
    rows,report=collect()
    dest=BASE/'scope/current_entries.jsonl';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(serialized(rows),encoding='utf8')
    save_json(ROOT/'qa/reports/translation_scope_current.json',report)
    print(json.dumps({k:report[k] for k in ['status','structurally_enumerated_records','authored','selected','unclassified_records','full_game_percentage']}))
    print(json.dumps(report['banks']))
    print(json.dumps(report['consumer_scopes']))

if __name__=='__main__':main()

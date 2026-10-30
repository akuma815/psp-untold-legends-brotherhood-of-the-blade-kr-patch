"""Exact six item-document bodies with two original image tags, no page grammar."""
import argparse, json, re, struct, unicodedata
from functools import lru_cache
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized, protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode, decode_unicode
from text_limits import check_template
import quest_batch_pipeline as pipeline

KEYS = {2261, 2532, 2631, 2648, 2692, 3514}
POLICY = 'item_document_field72_two_original_portraits_no_pages_2048_v1'
NAME = 'document_portraits_20261022'
BASE = ROOT/'workspace/translation'
SPEC = dict(name=NAME, config=f'development_{NAME}.json', prior_name='ui_confirmations_20261021',
            prior_config='development_ui_confirmations_20261021.json',
            prior_config_sha256='157e37ab2e846c1587a85a54c257a6b7e4890ce743e574a35ff9256c9980526c',
            prior_artifact_sha256='df9386f13d5a41ac7fa3a64ec14190b9cbb8b7ee0a227ffca2cdf2e0283799d2', new_authored_count=0)

@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    import document_body_policy_20261020 as plain
    db = (ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    boot = (ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    assert digest(db) == 'd852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    assert digest(boot) == 'b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    off, n = struct.unpack_from('<II', db, 40); fields = {}; rows = []
    for row in range(n):
        raw = db[off+row*84:off+(row+1)*84]; key = struct.unpack_from('<I', raw, 72)[0]
        if key in KEYS:
            assert raw[59] == 13 and key not in fields
            fields[key] = [(5, row, 72)]
            rows.append(dict(key=key, table=5, row=row, stride=84, field=72, offset=off+row*84, complete_row_hex=raw.hex()))
    assert set(fields) == KEYS
    out = ROOT/'workspace/analysis/document_portraits_20261022'; windows = []
    for name, a, z in [('repeated_image_parser', 0xc3024, 0xc3608), ('initial_image_selection', 0xc3760, 0xc38d0)]:
        raw = boot[a+128:z+128]; decoded = Profile().verify_roundtrip(raw, a, out, name)
        (out/(name+'.listing.txt')).write_text(''.join(f'{r["pc"]:08X} {r["assembly"]}\n' for r in decoded), encoding='utf8')
        windows.append(dict(name=name, start=a, end=z, sha256=digest(raw), roundtrip_instructions=len(decoded)))
    # Assert source branch targets and record stores rather than merely searching for image literals.
    def word(pc): return struct.unpack_from('<I', boot, pc+128)[0]
    def branch(pc): return pc+4+struct.unpack('<h', struct.pack('<H', word(pc)&0xffff))[0]*4
    def call(pc): return (word(pc)&0x3ffffff)*4
    assert call(0xc3410) == 0xc7f64 and call(0xc3494) == 0x133eac
    assert call(0xc3530) == call(0xc354c) == 0xbd72c and branch(0xc3560) == 0xc31d0
    assert word(0xc33dc) == 0xafb00054 and word(0xc3444) == 0xaca40000
    assert call(0xc35d0) == 0xc3760 and word(0xc3824) == 0xae000300
    src = sources(); wad = json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'))
    assets = {}
    wadpath = ROOT/'extracted/disc/PSP_GAME/USRDIR/resource.wad'
    assert digest(wadpath.read_bytes()) == '696b7618de5fc7c2610666b7b9f543ec2be5e91bcd0bcdd86c20d0d5db47870d'
    with wadpath.open('rb') as f:
        for tag in sorted({t for s in src.values() for t in re.findall(r'\[i_([^\]]+)\]', s['source_text'])}):
            matches = [r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1] == 'tex_ui_'+tag]
            assert len(matches) == 1
            m = matches[0]; f.seek(m['offset']); b = f.read(m['size_candidate']); assert digest(b) == m['sha256']
            assets[tag] = m
    return dict(fields=fields, complete_rows=rows, consumer=plain.context(), parser_windows=windows, portrait_source_assets=assets,
                interpretation='Static source: exact same item field72→705DC cap2048→owned document→C3024. C33DC records cleaned UTF16 position, C3410 resolves image, C3424..C3498 appends 12-byte record, C3520..C3564 rescans and branches to C31D0 until both image/page searches miss. C3760 initializes image index0 when vector nonempty. No speaker identity inferred from portrait.',
                source_tag_sequence_preserved=True, paragraph_sequences_preserved_per_image_segment=True,
                actual_second_portrait_transition_or_layout_verified=False, explicit_page_policy_adopted=False,
                scope='Only six original two-image item documents; no event/dialogue lifecycle or literal bracket exception.')

@lru_cache(maxsize=1)
def sources():
    rows = {s['key']: s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank'] == 'trans' and s['key'] in KEYS}
    raw = (ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    assert set(rows) == KEYS
    for s in rows.values():
        b = raw[s['offset']:s['offset']+s['byte_length']]
        assert b.hex() == s['source_hex'] and digest(b) == s['source_sha256']
    return rows

FIELDS = context()['fields']

def validate(r, book, encoder, decoder):
    assert set(r) == {'key', 'source_text', 'text', 'control_policy'} and r['key'] in KEYS and r['control_policy'] == POLICY
    s = sources()[r['key']]['source_text']; t = r['text']
    assert r['source_text'] == s and t and t == unicodedata.normalize('NFC', t)
    tags = re.findall(r'\[[^\]]+\]', s)
    assert tags == ['[i_PI_AncientTome]', '[i_PI_Tael]' if r['key'] == 2692 else '[i_PI_Aldus]']
    assert re.findall(r'\[[^\]]+\]', t) == tags and s.startswith(tags[0]) and t.startswith(tags[0])
    split = r'\[i_[A-Za-z0-9_]+\]'
    a = re.split(split, s); b = re.split(split, t); assert len(a) == len(b) == 3 and a[0] == b[0] == ''
    for original, draft in zip(a[1:], b[1:]):
        assert draft.strip() and re.findall(r'\r\n+', original) == re.findall(r'\r\n+', draft)
        assert not any(c in draft for c in '\0\t[]{}$#%&*+:<=>\\^~')
        assert '\r' not in draft.replace('\r\n', '') and '\n' not in draft.replace('\r\n', '')
    encoded = encoder(t, book).encode('utf8'); assert decoder(encoded.decode('utf8'), book) == t
    assert len(encoded)+1 <= 5000
    check_template(t, '705DC original2048 wide decoder; exact two image records, no pages')
    return encoded

def drafts():
    es = {e['id']: e for e in lines(ROOT/'qa/ssot/20261022_resume_baseline/entries.jsonl')}; ds = decisions()
    return {k: resolve(ds[es[s['id']]['current_working_decision']]) for k, s in sources().items()}

def select():
    cfgpath = ROOT/'config'/SPEC['prior_config']; assert digest(cfgpath.read_bytes()) == SPEC['prior_config_sha256']
    cfg = json.loads(cfgpath.read_text(encoding='utf8')); es = lines(BASE/'entries.jsonl'); before = {e['id']: serialized([e]) for e in es}
    byid = {e['id']: e for e in es}; ds = decisions(); assert len(ds) == 3923
    assert (BASE/'entries.jsonl').read_bytes() == (ROOT/'qa/ssot/20261022_resume_baseline/entries.jsonl').read_bytes()
    src = sources(); texts = drafts(); records = []; metrics = []
    sample = dict(key=2261, source_text=src[2261]['source_text'], text=texts[2261], control_policy=POLICY)
    negatives = []
    for label, change in [('outside_scope', dict(key=3665)), ('wrong_source', dict(source_text='wrong')),
                          ('image_lost', dict(text=sample['text'].replace('[i_PI_Aldus]', ''))),
                          ('image_changed', dict(text=sample['text'].replace('[i_PI_Aldus]', '[i_PI_Tael]'))),
                          ('page_added', dict(text=sample['text']+'[p]')), ('literal_bracket_added', dict(text=sample['text']+'[literal]')),
                          ('paragraph_moved', dict(text=sample['text'].replace('\r\n\r\n[i_PI_Aldus]', '[i_PI_Aldus]\r\n\r\n'))),
                          ('overflow', dict(text=sample['text']+'\uac00'*2048))]:
        try: validate(dict(sample, **change), pipeline.BOOK, encode_unicode, decode_unicode)
        except (ValueError, AssertionError): negatives.append(label)
        else: raise AssertionError(label)
    packet = BASE/'packets'/NAME; packet.mkdir(parents=True, exist_ok=True)
    protected_write(packet/'context.json', json.dumps(context(), ensure_ascii=False, indent=2)+'\n')
    for k in sorted(KEYS):
        e = byid[src[k]['id']]; old = e['current_working_decision']
        assert e['state'] == 'in_progress' and not e['development_diagnostic_selection']
        row = dict(key=k, source_text=src[k]['source_text'], text=texts[k], control_policy=POLICY)
        encoded = validate(row, pipeline.BOOK, encode_unicode, decode_unicode)
        did = f'development_{NAME}:trans:{k}'; cfg['trans_overrides'].append(row)
        records.append(dict(id=did, source_id=e['id'], source_sha256=e['source_sha256'], wording_ref=ds[old]['wording_ref'], broader_decision_id=old,
                            applicability=dict(revision='ULKS46015-v1.01', context=NAME, write_scope='Exact original item field72 body, two original image tags; no DB or code mutation'),
                            rationale='Existing wording and refs unchanged; original document chain and repeating image parser statically closed. Actual display remains pending.',
                            semantic_impact='Existing individually authored lore and provisional names await human review; no portrait-based speaker assignment.',
                            state='needs_human_review', approval=None, distribution_eligible=False, independent_semantic_review=None))
        e.update(state='needs_human_review', context_id=NAME, development_diagnostic_selection=did); e['decision_ids'].append(did)
        metrics.append(dict(key=k, utf8_including_NUL=len(encoded)+1, utf16_including_NUL=len(texts[k].encode('utf-16le'))//2+1,
                            previous_decision=old, wording_ref_unchanged=True))
    targets = {r['source_id'] for r in records}; assert all(serialized([e]) == before[e['id']] for e in es if e['id'] not in targets)
    protected_write(ROOT/'config'/SPEC['config'], json.dumps(cfg, ensure_ascii=False, indent=2)+'\n')
    protected_write(BASE/f'decisions_{NAME}.jsonl', serialized(records))
    tmp = BASE/f'entries.{NAME}.pending'; tmp.write_text(serialized(es), encoding='utf8'); tmp.replace(BASE/'entries.jsonl')
    save_json(ROOT/f'qa/reports/{NAME}_selection.json', dict(status='PASS_SIX_EXISTING_WORDINGS_SELECTED_UNCHANGED', new_authored=0, new_selected=6,
              authored=3601, selected=3503, held=98, decision_history=3929, metrics=metrics, negative_cases=negatives,
              context_path=(packet/'context.json').relative_to(ROOT).as_posix(), runtime_verified=False, human_approval=False, release_eligible=False))
    print(json.dumps(dict(new_selected=6, new_authored=0, selected=3503, held=98)))

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=['inspect', 'select', 'audit']); a = p.parse_args()
    if a.action == 'inspect': print(json.dumps(context()))
    elif a.action == 'select': select()
    else: pipeline.audit(SPEC, __import__(__name__ if __name__ != '__main__' else 'document_portraits_20261022'), drafts(), {})

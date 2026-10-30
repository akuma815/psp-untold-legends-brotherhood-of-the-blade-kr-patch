"""Two exact item documents: four retained p markers and one translated literal note."""
import argparse, json, re, struct, unicodedata
from functools import lru_cache
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized, protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode, decode_unicode
from text_limits import check_template
from journal_drafts_20261020 import DRAFTS as OLD_DRAFTS
import quest_batch_pipeline as pipeline

NAME = 'document_markup_20261022'; KEYS = {3662,3665}
POLICY = 'item_document_3662_fixed_literal_3665_original_p4_CRLF_2048_v1'
ENGLISH_NOTE = '[water damage obscures the rest of the document]'
KOREAN_NOTE = '[물에 젖어 나머지 내용을 알아볼 수 없다]'
DOC3662 = '''[i_PI_AncientTome]일지 I

아벤을 휩쓰는 이 병은 지금껏 본 어떤 병과도 다르다.

감염을 옮기는 것은 하찮은 프레이톡스 거미가 아닐까 의심한다. 도시 아래 버려진 지하묘지에서 흔히 볼 수 있는 종이다.

본론으로 돌아가자. 지금까지 치료에 실패한 것은 병을 고치려 했기 때문이라고 생각한다. 실제로는 은밀하게 작용하는 독인데 말이다.

분명 해독제를 만들 수 있다. 그저 충분히 강력한 독을 얻을 원천이 필요할 뿐이다. 증... 과정을 거치면

[물에 젖어 나머지 내용을 알아볼 수 없다]'''.replace('\n','\r\n')
DRAFTS = {3662:DOC3662,3665:OLD_DRAFTS[3665]}
assert OLD_DRAFTS[3662].endswith(ENGLISH_NOTE) and DOC3662.endswith(KOREAN_NOTE)
assert OLD_DRAFTS[3662][:-len(ENGLISH_NOTE)] == DOC3662[:-len(KOREAN_NOTE)]
BASE = ROOT/'workspace/translation'
SPEC = dict(name=NAME,config=f'development_{NAME}.json',prior_name='document_portraits_20261022',
    prior_config='development_document_portraits_20261022.json',prior_config_sha256='3d59cfaf3f2e07a2aac93447f68dffdc365cce1cc259d71295776611f505c345',
    prior_artifact_sha256='6dc02696d7fc725f5085cae05cdf2c1cd7b909c9aa480d0a857dd10f2490297e',new_authored_count=0)

@lru_cache(maxsize=1)
def context():
    from document_body_policy_20261020 import context as plain_context
    db = (ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db) == 'd852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n = struct.unpack_from('<II',db,40); fields = {}; rows = []
    for row in [2046,2056]:
        raw = db[off+row*84:off+(row+1)*84]; k = struct.unpack_from('<I',raw,72)[0]
        assert row<n and k in KEYS and raw[59] == 13
        fields[k] = [(5,row,72)]; rows.append(dict(table=5,row=row,stride=84,key=k,field=72,complete_hex=raw.hex()))
    assert set(fields) == KEYS
    boot = (ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    assert digest(boot) == 'b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    assert boot[0x13c9a4:0x13c9ae] == b'[p]\0[i_\0]\0'
    return dict(fields=fields,complete_rows=rows,consumer=plain_context(),
        source_runtime='qa/reports/document_markup_source_20261022_runtime.json',
        applicable_runtime='Exact source item-reader:3665 input1026/clean1002 UTF16/NUL, p positions593/723/812/930;3662 literal square note survives parser and renders.',
        p_policy='Keep the original four3-unit[p] markers, order and per-segment CRLF. C3024 strips markers and records positions; no forced-page contract or other-mode semantics adopted.',
        literal_policy=dict(key=3662,source=ENGLISH_NOTE,draft=KOREAN_NOTE,scope='Only this fixed literal pair; not a generalized bracket grammar'),
        narrative='Existing Aldus diary voice and biased descriptions retained as character attitudes. No source-cutoff completion, new term approval or lore rewrite.',
        actual_Korean_new_two_documents_runtime_pending=True,release_eligible=False)

FIELDS = context()['fields']

@lru_cache(maxsize=1)
def sources():
    src = {s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans' and s['key'] in KEYS}
    raw = (ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for s in src.values():
        b = raw[s['offset']:s['offset']+s['byte_length']]
        assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    assert set(src)==KEYS
    return src

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in KEYS and r['control_policy']==POLICY
    k=r['key']; s=sources()[k]['source_text']; t=r['text']
    assert r['source_text']==s and t and t==unicodedata.normalize('NFC',t)
    source_tags=re.findall(r'\[[^\]]+\]',s); target_tags=re.findall(r'\[[^\]]+\]',t)
    if k==3662:
        assert source_tags==['[i_PI_AncientTome]',ENGLISH_NOTE]
        assert target_tags==['[i_PI_AncientTome]',KOREAN_NOTE] and s.endswith(ENGLISH_NOTE) and t.endswith(KOREAN_NOTE)
        assert t.startswith(source_tags[0])
        body=t[len(source_tags[0]):-len(KOREAN_NOTE)]
        assert re.findall(r'\r\n+',t)==re.findall(r'\r\n+',s)
    else:
        assert source_tags==['[i_PI_Aldus]']+['[p]']*4 and target_tags==source_tags and t.startswith(source_tags[0])
        for a,b in zip(re.split(r'\[i_[^]]+\]|\[p\]',s),re.split(r'\[i_[^]]+\]|\[p\]',t)):
            assert re.findall(r'\r\n+',a)==re.findall(r'\r\n+',b)
        body=re.sub(r'\[i_[^]]+\]|\[p\]','',t)
    assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(t,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==t and len(encoded)+1<=5000
    check_template(t,'Original item705DC2048wide, source-bound p4/fixed literal note only')
    return encoded

def select():
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256']
    cfg=json.loads(cfgpath.read_text(encoding='utf8'));es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es}
    byid={e['id']:e for e in es};ds=decisions();assert len(ds)==4301
    src=sources();samples={k:dict(key=k,source_text=src[k]['source_text'],text=DRAFTS[k],control_policy=POLICY) for k in sorted(KEYS)}
    for r in samples.values():validate(r,pipeline.BOOK,encode_unicode,decode_unicode)
    negatives=[]
    tests=[(3665,'wrong_source',dict(source_text='wrong')),(3665,'outside_scope',dict(key=2705)),
        (3665,'page_removed',dict(text=DRAFTS[3665].replace('[p]','',1))),(3665,'page_added',dict(text=DRAFTS[3665]+'[p]')),
        (3665,'portrait_removed',dict(text=DRAFTS[3665].replace('[i_PI_Aldus]',''))),
        (3665,'paragraph_removed',dict(text=DRAFTS[3665].replace('\r\n\r\n','',1))),
        (3662,'old_English_note',dict(text=OLD_DRAFTS[3662])),(3662,'literal_closer_lost',dict(text=DRAFTS[3662][:-1])),
        (3662,'new_control',dict(text=DRAFTS[3662]+'$a')),(3665,'overflow',dict(text=DRAFTS[3665]+'가'*2048))]
    for k,label,change in tests:
        try:validate(dict(samples[k],**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (ValueError,AssertionError):negatives.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261022_before_document_markup';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    protected_write(snap/'manifest.json',json.dumps(dict(entries_sha256=digest((BASE/'entries.jsonl').read_bytes()),terminology_sha256=digest((BASE/'terminology.json').read_bytes()),config_sha256=SPEC['prior_config_sha256'],artifact_sha256=SPEC['prior_artifact_sha256']),indent=2)+'\n')
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True)
    protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    e3662=byid[src[3662]['id']];old3662=e3662['current_working_decision'];assert resolve(ds[old3662])==OLD_DRAFTS[3662]
    path=BASE/'authored'/f'{NAME}.json'
    protected_write(path,json.dumps(dict(policy='one_individually_authored_literal_note_revision_no_prose_replacement_rule',revisions=[dict(key=3662,source_id=src[3662]['id'],source_sha256=src[3662]['source_sha256'],previous_decision=old3662,previous_note=ENGLISH_NOTE,new_note=KOREAN_NOTE,text=DRAFTS[3662],all_other_characters_unchanged=True,human_reviewed=False,distribution_eligible=False)]),ensure_ascii=False,indent=2)+'\n')
    records=[]
    for k,r in samples.items():
        e=byid[src[k]['id']];old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection']
        assert resolve(ds[old])==OLD_DRAFTS[k]
        did=f'development_{NAME}:trans:{k}';ref=ds[old]['wording_ref'] if k==3665 else dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()),json_pointer='/revisions/0/text')
        records.append(dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=ref,broader_decision_id=old,
            applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact original item table5 field72 document; no DB/code change'),
            rationale='Original item-reader source observation closes this specific control/literal boundary.3665 wording unchanged;3662 manually translates only its previously English square note.',
            semantic_impact='Original diary voice, prejudices and truncation retained; names/voice and new literal translation await human review. No forced-page meaning inferred.',
            state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None))
        cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    targets={d['source_id'] for d in records};assert all(serialized([e])==before[e['id']] for e in es if e['id'] not in targets)
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized(records))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4303 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_TWO_SOURCE_BOUND_DOCUMENTS_SELECTED_ONE_MANUAL_LITERAL_REVISION',authored=3973,selected=3505,working_unselected=468,decision_history=4303,
        new_authored=0,new_selected=2,unchanged_wording_key=3665,manual_literal_revision_key=3662,all_previous_wording_files_retained=True,
        negative_cases=negatives,p_markers_preserved=4,forced_page_contract_adopted=False,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='select':select()
    else:pipeline.audit(SPEC,__import__('document_markup_20261022'),DRAFTS,{})

"""Exact zero-portrait item2813, with one individually translated literal note."""
import argparse, json, re, struct, unicodedata
from functools import lru_cache
from survey import ROOT, digest, save_json
from catalog_survey034 import lines, serialized, protected_write
from map_corpus_20261020 import decisions
from audit_translation138 import resolve
from unicode_codec042 import encode_unicode, decode_unicode
from text_limits import check_template
import quest_batch_pipeline as pipeline

NAME='document_zero_20261022';KEYS={2813};POLICY='item_document_2813_zero_portrait_fixed_literal_CRLF_2048_v1'
ENGLISH_NOTE='[The rest of the tome is written in a language I do not understand.]'
KOREAN_NOTE='[책의 나머지는 내가 이해하지 못하는 언어로 쓰여 있다.]'
DOC2813='''서문.

이 책에는 아벤의 가장 어두웠던 역사가 상세히 담겨 있다. 폭군이 우리 땅을 다스리고, 광신적인 추종자들이 반대자를 찾아 거리와 술집, 집 안까지 뒤지던 시대의 기록이다.

많은 이들이 추방을 들먹이며 위협하는 광신자들을 두려워해 입을 다문다. 아벤의 성문이 가두어 주는 안전 너머의 세상이 무섭기 때문이다. 이것은 삶이라 할 수 없다. 그들은 자유와 깨우침을 두려움과 억압으로 바꾸었으며, 이 일은 잊혀서는 안 된다.

학살의 깊은 곳, 족쇄에 묶인 자유와 우리의 이상과 열정을 거의 말살하려던 참상 속에서 나그네들이 나타난다. 비록 성문에서 멀리 떠돌아야 하지만, 우리는 지금도 앞으로도 영원히 아벤의 역사와 열정과 아름다움을 지키는 이들이다.

이것이 우리의 증언이다. 이것이 우리의 유산이다. [책의 나머지는 내가 이해하지 못하는 언어로 쓰여 있다.]'''.replace('\n','\r\n')
DRAFTS={2813:DOC2813};BASE=ROOT/'workspace/translation'
OLD_DRAFT=json.loads((BASE/'authored/item_docs_20261020.json').read_text(encoding='utf8'))['held_drafts'][0]['text']
assert OLD_DRAFT.endswith(ENGLISH_NOTE) and OLD_DRAFT[:-len(ENGLISH_NOTE)]==DOC2813[:-len(KOREAN_NOTE)]
SPEC=dict(name=NAME,config=f'development_{NAME}.json',prior_name='document_markup_20261022',prior_config='development_document_markup_20261022.json',prior_config_sha256='f024b255b8063da1128d6526906432833c7be3756ac17fb28bee176806f731dc',prior_artifact_sha256='de61d6619fac2dd0437bc6eaec489f67f322d6b29d6d785f96f3bdbfc15fa6a1',new_authored_count=0)

@lru_cache(maxsize=1)
def sources():
    src={s['key']:s for s in lines(BASE/'baseline/source_entries.jsonl') if s['bank']=='trans' and s['key'] in KEYS}
    raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for s in src.values():
        b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
    assert set(src)==KEYS
    return src

@lru_cache(maxsize=1)
def context():
    from document_body_policy_20261020 import context as plain_context
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,40);row=2084;raw=db[off+row*84:off+(row+1)*84]
    assert row<n and struct.unpack_from('<I',raw,72)[0]==2813 and raw[59]==13
    return dict(fields={2813:[(5,row,72)]},complete_rows=[dict(table=5,row=row,field=72,complete_hex=raw.hex())],consumer=plain_context(),
        source_runtime='qa/reports/document_zero_source_20261022_runtime.json',
        literal_policy=dict(source=ENGLISH_NOTE,draft=KOREAN_NOTE,scope='Only this literal pair, not a generalized bracket grammar'),
        zero_portrait_policy='Original2813 has no image or p markers. Preserve exact CRLF segments; first-person note remains first-person without identifying its reader or language.',
        source_item_acquisition_tested=False,release_eligible=False)
FIELDS=context()['fields']

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==2813 and r['control_policy']==POLICY
    s=sources()[2813]['source_text'];t=r['text'];assert r['source_text']==s and t and t==unicodedata.normalize('NFC',t)
    assert re.findall(r'\[[^\]]+\]',s)==[ENGLISH_NOTE] and s.endswith(ENGLISH_NOTE)
    assert re.findall(r'\[[^\]]+\]',t)==[KOREAN_NOTE] and t.endswith(KOREAN_NOTE)
    assert re.findall(r'\r\n+',s)==re.findall(r'\r\n+',t)
    body=t[:-len(KOREAN_NOTE)]
    assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(t,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==t and len(encoded)+1<=5000
    check_template(t,'Exact zero-portrait item2813 source-bound literal note')
    return encoded

def select():
    evidence=json.loads((ROOT/'qa/reports/document_zero_source_20261022_runtime.json').read_text(encoding='utf8'));assert evidence['source_literal_visible'] and evidence['zero_image_and_p_vectors_verified']
    cfgpath=ROOT/'config'/SPEC['prior_config'];assert digest(cfgpath.read_bytes())==SPEC['prior_config_sha256']
    cfg=json.loads(cfgpath.read_text(encoding='utf8'));es=lines(BASE/'entries.jsonl');before={e['id']:serialized([e]) for e in es};ds=decisions();assert len(ds)==4303
    s=sources()[2813];r=dict(key=2813,source_text=s['source_text'],text=DOC2813,control_policy=POLICY)
    validate(r,pipeline.BOOK,encode_unicode,decode_unicode);negative=[]
    for label,change in [('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3662)),('old_note',dict(text=OLD_DRAFT)),('portrait',dict(text='[i_PI_Aldus]'+DOC2813)),('new_page',dict(text=DOC2813+'[p]')),('paragraph',dict(text=DOC2813.replace('\r\n\r\n','',1))),('NUL',dict(text=DOC2813+'\0')),('literal_closer',dict(text=DOC2813[:-1])),('overflow',dict(text='가'*2048+DOC2813))]:
        try:validate(dict(r,**change),pipeline.BOOK,encode_unicode,decode_unicode)
        except (AssertionError,ValueError):negative.append(label)
        else:raise AssertionError(label)
    snap=ROOT/'qa/ssot/20261022_before_document_zero';snap.mkdir(parents=True,exist_ok=True)
    for p in [BASE/'entries.jsonl',BASE/'terminology.json',cfgpath]:protected_write(snap/p.name,p.read_text(encoding='utf8'))
    packet=BASE/'packets'/NAME;packet.mkdir(parents=True,exist_ok=True);protected_write(packet/'context.json',json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
    e=next(e for e in es if e['id']==s['id']);old=e['current_working_decision'];assert e['state']=='in_progress' and not e['development_diagnostic_selection'] and resolve(ds[old])==OLD_DRAFT
    path=BASE/'authored'/f'{NAME}.json';protected_write(path,json.dumps(dict(policy='one_individually_authored_literal_note_revision_no_prose_replacement_rule',revisions=[dict(key=2813,source_id=s['id'],previous_decision=old,source_sha256=s['source_sha256'],previous_note=ENGLISH_NOTE,new_note=KOREAN_NOTE,text=DOC2813,all_other_characters_unchanged=True,human_reviewed=False,distribution_eligible=False)]),ensure_ascii=False,indent=2)+'\n')
    did=f'development_{NAME}:trans:2813';d=dict(id=did,source_id=e['id'],source_sha256=e['source_sha256'],wording_ref=dict(path=path.relative_to(ROOT).as_posix(),sha256=digest(path.read_bytes()),json_pointer='/revisions/0/text'),broader_decision_id=old,applicability=dict(revision='ULKS46015-v1.01',context=NAME,write_scope='Exact original table5 row2084 field72 body; no DB/code change'),rationale='Source actual item-reader shows fixed literal bracket note and zero portrait/p vectors, including prior portrait/p4 clearing. Manually translate only English note.',semantic_impact='Existing biased historic account retained. First-person note, language and author identity not embellished. Wording awaits human review.',state='needs_human_review',approval=None,distribution_eligible=False,independent_semantic_review=None)
    cfg['trans_overrides'].append(r);e.update(state='needs_human_review',context_id=NAME,development_diagnostic_selection=did);e['decision_ids'].append(did)
    assert all(serialized([x])==before[x['id']] for x in es if x['id']!=e['id'])
    protected_write(ROOT/'config'/SPEC['config'],json.dumps(cfg,ensure_ascii=False,indent=2)+'\n');protected_write(BASE/f'decisions_{NAME}.jsonl',serialized([d]))
    tmp=BASE/f'entries.{NAME}.pending';tmp.write_text(serialized(es),encoding='utf8');tmp.replace(BASE/'entries.jsonl')
    assert len(decisions())==4304 and (BASE/'terminology.json').read_bytes()==(snap/'terminology.json').read_bytes()
    report=dict(status='PASS_ZERO_PORTRAIT_ITEM2813_SELECTED_ONE_MANUAL_LITERAL_REVISION',authored=3973,selected=3506,working_unselected=467,decision_history=4304,new_authored=0,new_selected=1,negative_cases=negative,all_previous_wording_files_retained=True,human_approval=False,release_eligible=False)
    save_json(ROOT/f'qa/reports/{NAME}_selection.json',report);print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='select':select()
    else:pipeline.audit(SPEC,__import__('document_zero_20261022'),DRAFTS,{})

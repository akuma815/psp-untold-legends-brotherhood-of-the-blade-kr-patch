"""Current wording/source/strict codec preflight;not a reinsertion or runtime claim."""
import json,re
from collections import Counter
from survey import ROOT,save_json,digest
from psp_folder import sha
from catalog_survey034 import lines
from unicode_codec042 import encode_unicode,decode_unicode

def load(p):return json.loads(p.read_text(encoding='utf8'))
def resolve(d):
    ref=d['wording_ref'];p=ROOT/ref['path'];assert sha(p)==ref['sha256'];value=load(p)
    for k in ref['json_pointer'].strip('/').split('/'):value=value[int(k)] if isinstance(value,list) else value[k]
    return value
def main():
    base=ROOT/'workspace/translation';entries=lines(base/'entries.jsonl');sources={r['id']:r for r in lines(base/'baseline/source_entries.jsonl')}
    decisions={r['id']:r for p in [base/'diagnostic_decisions.jsonl',*sorted(base.glob('decisions_*.jsonl'))] for r in lines(p)}
    assert len(entries)==len(sources)==3973 and len(decisions)==133
    current={};book={'mapping':{c:None for c in range(0xac00,0xd7a4)}};cps=set();same_inn=[]
    for e in entries:
        s=sources[e['id']];assert e['source_sha256']==s['source_sha256']
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        if e['state']=='untranslated':continue
        did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1]
        d=decisions[did];assert did in e['decision_ids'] and d['source_id']==e['id']
        value=resolve(d);assert decode_unicode(encode_unicode(value,book),book)==value
        assert d['approval'] is None and e['release_selection'] is None and not e['distribution_eligible']
        current[e['id']]=value;cps.update(ord(c) for c in value if 0xac00<=ord(c)<=0xd7a3)
        assert '하울링 파인' not in value
        if '울부짖는 소나무 여관' in value:same_inn.append(e['id'])
    assert len(current)==127 and len(same_inn)==4
    assert set(same_inn)=={'ULKS46015-v1.01:en_us/static:34:occurrence1',*[f'ULKS46015-v1.01:en_us/trans:{k}' for k in [3881,2314,2326]]}
    checked=[]
    for row in load(base/'authored/inn_reactions136.json')['drafts']:
        s=sources[row['source_id']];value=current[s['id']]
        assert re.findall(r'\[i_[^\]\r\n]+\]',value)==re.findall(r'\[i_[^\]\r\n]+\]',s['source_text'])
        assert re.findall(r'\r\n+',value)==re.findall(r'\r\n+',s['source_text'])
        assert re.findall(r'\$[A-Za-z]',value)==re.findall(r'\$[A-Za-z]',s['source_text'])==[]
        checked.append(s['key'])
    assert len(checked)==27
    assert '워커들이' in current['ULKS46015-v1.01:en_us/trans:2303'] and '워커 형제' not in current['ULKS46015-v1.01:en_us/trans:2303']
    assert current['ULKS46015-v1.01:en_us/trans:2308'].startswith('[i_PR_NathanTondrelConcened]')
    states=dict(Counter(e['state'] for e in entries));assert states=={'untranslated':3846,'needs_human_review':86,'in_progress':41}
    # Keep exact source-bound build identities separate from the current working population.
    assert sha(ROOT/'config/development_terms131.json')=='f3c7e3a1e071d6fd5813bd73b28ba8844a7436abfe2cce82c0c409cb0c279334'
    assert sha(ROOT/'workspace/runtime/inn_term_132/artifact.json')=='f9150d7bfde0588c7dc63674c6851f8fe742cb290026f2fad972aac49ba5152a'
    assert load(ROOT/'qa/reports/save_stage135_bounded.json')['save_load_verified'] is False
    report={'status':'PASS_138_CURRENT_127_WORDING_SOURCE_CODEC_PREFLIGHT','authored_entry_total':127,'selected_drafts':86,'working_unselected':41,'decision_history_records':133,
      'work_states':states,'protected_source_records_checked':3973,'active_wording_refs_hash_bound_and_codec_roundtrip':127,
      'new27_source_tags_and_paragraphs_preserved':True,'modern_Hangul_unique_in_active_wording':len(cps),
      'modern_Hangul_supply_basis':'Existing132 complete11172 scalar map;codec preflight here does not establish each glyph runtime reachability or target consumer capacity',
      'approved_same_inn_current_source_ids':same_inn,'approved_terms':1,'approved_translations':0,
      'old136_revision_preserved':True,'current2303_revision':'working137:trans:2303','current_build':'inn_term_132',
      'new27_reinserted':False,'new27_runtime_verified':False,'normal_save_load_verified':False,'emulator_running':False,'new_ISO':False,'release_eligible':False,
      'next_action':'Static trace the known inn popup renderer and per-key scene references for the unselected NPC group;select the context-closed subset into the next development config without playing toward ending.'}
    save_json(ROOT/'qa/reports/translation_stage138_preflight.json',report);print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':main()

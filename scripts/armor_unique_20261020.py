"""All240 named armor records andfour AAA labels, same original name consumer."""
import argparse,copy
from armor_unique_drafts_20261020 import NAMED,AAA
from armor_name_common import ArmorNames
DRAFTS={**NAMED,**AAA};assert len(NAMED)==240 and len(AAA)==4 and len(DRAFTS)==244
NORMAL=ArmorNames(NAMED,1033,1273,'All240 named armor andshield records',[
    'Lysetta/Draven/Diana/Tael/Shaelunn inherit current 리세타/드레이븐/다이애나/타엘/셰일룬 proposals; none is a new approved term.',
    'Crown oftheCrown distinguishes physical 왕관 fromoffice 크라운. Item names do not establish item ownership, story acquisition or named character abilities.',
    'WarfangWraps is category5body, hence 감개 rather than inventing armwear fromWraps. Metaphorical Eye/Heart/Grasp/Stride names are retained as metaphors.',
    'Wolfbane andNightmarrow are provisional transliterations; no unsupported specificplant orsource spelling fix. Coven is 코븐 without assuming a witch-only organization.',
    'Unique names that resemble generic sets ortrans-bank names remain distinct physical entries andsourceIDs; no automatic merge orfallback namespace assertion.'])
TEST=ArmorNames(AAA,0,4,'Four original AAA Badass bodywear records',[
    'Original literalAAA prefix retained. Test-like labels are not declared unused; names are still same source-bound item title path.',
    '막강한 is provisional informalBadass title wording, not proof of actualstats oravailability.'])
def population():
    a=NORMAL.population();b=TEST.population();assert not set(a)&set(b)
    return {**a,**b}
def context():
    c=copy.deepcopy(NORMAL.context());c['additional_cohort']=TEST.context();c['cohort']='Originaltable5rows1033..1272 plusrows0..3:240named+4literalAAA,244physicalnames.'
    c['exclusions']='Earlier cohorts andexisting1388 retain priorwording. AAA names are now explicitly selected withliteralprefix; not dropped or declaredunused.'
    from survey import ROOT
    from catalog_survey034 import lines
    from audit_translation138 import resolve
    from map_corpus_20261020 import decisions
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};es={e['id']:e for e in lines(ROOT/'workspace/translation/entries.jsonl')};ds=decisions();related=[]
    for k in [2381,2676,2692,2700,2736,2740]:
        s=ss[k];e=es[s['id']];d=e['development_diagnostic_selection'] or e.get('current_working_decision');related.append(dict(source=s,current_decision=d,current_wording=resolve(ds[d]) if d else None))
    c['inherited_narrative_context']=related;return c
def validate(r,book,encoder,decoder):
    assert r['key'] in DRAFTS
    if r['key'] in AAA:
        assert r['source_text'].startswith('AAA ') and r['text'].startswith('AAA ') and r['text'].count('AAA')==1
        return TEST.validate(r,book,encoder,decoder)
    return NORMAL.validate(r,book,encoder,decoder)
def negative_cases():
    k=3685;r=dict(key=k,source_text=TEST.population()[k]['source']['source_text'],text=AAA[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=1388)),('lost_AAA',dict(text=r['text'][4:])),('control',dict(text=r['text']+'[p]')),
        ('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'\u2603')),('owned_slot_overflow',dict(text='AAA '+'가'*84))]
SPEC=dict(name='armor_unique_20261020',config='development_armor_unique_20261020.json',prior_name='armor_sw_20261020',prior_config='development_armor_sw_20261020.json',
    prior_config_sha256='e165844bf175c650477032db1ace34852ab123c264c788ce55458ac3f4303b0a',prior_artifact_sha256='bfc2a8fb87d57b9cf371c278c612986193b0a74ee6c8eb8300fa677d0fa72208',
    prior_decisions=2504,expected_states=dict(untranslated=1547,needs_human_review=2322,in_progress=104),write_scope='Exact244 static names inoriginal armorrows1033..1272 and0..3; preserveAAA, no DB/effect/prefix/suffix policy changes')
def audit():
    import static_name_batch_pipeline as pipeline
    import sys
    pipeline.audit(SPEC,sys.modules[__name__],DRAFTS)
    import struct,json
    from collections import Counter
    from survey import ROOT,digest,save_json
    from catalog_survey034 import lines
    from audit_translation138 import resolve
    from map_corpus_20261020 import decisions
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};es={e['id']:e for e in lines(ROOT/'workspace/translation/entries.jsonl')};ds=decisions()
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();off,n=struct.unpack_from('<II',db,40);cfg=json.loads((ROOT/'config'/SPEC['config']).read_text(encoding='utf8'));picked={r['key']:r for r in cfg['static_overrides']};rows=[]
    for row in range(n):
        b=db[off+row*84:off+(row+1)*84]
        if b[59] not in [4,5,6,7,8,9]:assert row>=1273;continue
        assert row<1273;k=struct.unpack_from('<H',b)[0];s=ss[k];e=es[s['id']];d=e['development_diagnostic_selection'];assert d and picked[k]['text']==resolve(ds[d])
        rows.append(dict(row=row,key=k,source_id=s['id'],category=b[59],selected_decision=d,source_sha256=s['source_sha256']))
    assert len(rows)==len({r['key'] for r in rows})==1273 and set(r['row'] for r in rows)==set(range(1273))
    assert picked[1388]['text']=='자루천 바지' and all(picked[k]['text'].startswith('AAA ') for k in AAA)
    save_json(ROOT/'qa/reports/armor_population_20261020.json',dict(status='PASS_ALL_1273_ORIGINAL_ARMOR_NAME_REFERENCES_SELECTED_STATIC_ONLY',rows=rows,
        armor_classes=dict(Counter(r['category'] for r in rows)),ordinary_family_reference_cells=1029,named_reference_cells=240,literal_AAA_reference_cells=4,
        newly_authored_this_continuation=1272,initial_pants1388_preserved=True,natural_availability_equip_layout_affix_gameplay_QA=False,full_game_completion=False,release_eligible=False))
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args()
    if a.action=='audit':audit()
    else:pipeline.select(SPEC,sys.modules[__name__],DRAFTS)

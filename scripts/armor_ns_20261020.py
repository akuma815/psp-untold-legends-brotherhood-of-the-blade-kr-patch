"""Netted throughShadowclaw equipment families, exact item-title source field."""
import argparse
from armor_ns_drafts_20261020 import DRAFTS as ALL_DRAFTS
from armor_name_common import ArmorNames
DRAFTS={k:v for k,v in ALL_DRAFTS.items() if k!=1388}
BATCH=ArmorNames(ALL_DRAFTS,585,795,'Netted throughShadowclaw armor andshield families',[
    'Quilted andQuiltedHide families are interleaved in source order but kept as distinct full physical records.',
    'Sackcloth follows already selected1388 자루천 바지. That original SSOT entry andwording are preserved;209new names plusone existing name cover210source rows.',
    'Petrified/Prismatic/Sacred names are titles, not new elemental/statistical gameplay claims.',
    'SavantVelvet andSentinelPlate are equipment labels; no cross-bank person/quest identity or shared ownership inferred.',
    'Every full name is explicit. Source headbands plural does not create a new numeric quantity.'])
def population():return {k:v for k,v in BATCH.population().items() if k in DRAFTS}
def context():
    from survey import ROOT
    from catalog_survey034 import lines
    from audit_translation138 import resolve
    from map_corpus_20261020 import decisions
    s=BATCH.population()[1388]['source'];e=next(e for e in lines(ROOT/'workspace/translation/entries.jsonl') if e['id']==s['id']);d=e['development_diagnostic_selection'];ds=decisions()
    assert e['state']=='needs_human_review' and resolve(ds[d])==ALL_DRAFTS[1388]=='자루천 바지'
    c=dict(BATCH.context());c['preserved_prior_name']=dict(source=s,current_decision=d,wording_ref=ds[d]['wording_ref'],text=ALL_DRAFTS[1388],new_selection=False);return c
def validate(r,book,encoder,decoder):
    assert r['key'] in DRAFTS
    return BATCH.validate(r,book,encoder,decoder)
negative_cases=BATCH.negative_cases
SPEC=dict(name='armor_ns_20261020',config='development_armor_ns_20261020.json',prior_name='armor_gm_20261020',prior_config='development_armor_gm_20261020.json',
    prior_config_sha256='10c58a05c64b835955c54eae56aec0901bbcbd6cc92a70782958c8418f79f175',prior_artifact_sha256='68ad353aa04307473fa7d28673ca4c656d27c9ee971423981fc14b7cb3283a88',
    prior_decisions=2057,expected_states=dict(untranslated=2029,needs_human_review=1840,in_progress=104),write_scope='Exact209 new static armor names with existing1388 preserved, originaltable5u16field0; no DB/effect/prefix/suffix policy changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

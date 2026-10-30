"""214 exact weapon/ammo base names, same source-wide item name consumer."""
import argparse
from weapons_ac_drafts_20261020 import DRAFTS
from armor_name_common import ArmorNames
NOTES=[
    'Exact table5u16field0 itemname path6FF94->DA6342048wide->DA478owned$i250UTF8; same inventorytitle consumer as original097dagger/pants. Category-specific acquisition/use/throw/ammo paths remain runtime-unverified.',
    'Original source classes0/1/2/3 are recorded, without inventing hand-count, equipclass, elemental damage or projectile behavior from a name.',
    '214 full names authored explicitly, not generated from material/type replacement rules. Current weapon technical vocabulary remains provisional.',
    'Ashen is 애션 pending material/color sense review; no unsupported ash-tree orburnt-material assertion. Bloodore/Beryl remain fantasy material naming proposals.',
    'Stilleto source spelling stays in source bindings; Korean 스틸레토 proposal does not rewrite English source, sourceDB or raw spelling.',
    'Stave=봉 andStaff=지팡이, HandAxe=손도끼/Hatchet=작은 도끼/Adze=자귀, Dagger=단검/ShortSword=짧은 검 keep source-name distinctions. No combat mechanism is established by those titles.',
    'Baculus/Hurlbat/Voulge etc use provisional phonetic names rather than asserting a specific historical weapon reconstruction.',
    'AAA prefix retained, default413Dagger excluded only from this new-name cohort andpreserved selected. Unresolved static/trans names617/624 remain separate global work.']
BATCH=ArmorNames(DRAFTS,1273,1487,'AAA throughCutlass weapon/ammunition names',NOTES,allowed_categories=(0,1,2,3))
population=BATCH.population
def context():
    c=dict(BATCH.context());c['semantic_notes']=NOTES;c['exclusions']='Existing413Dagger remains its prior original development wording. Namespace-unresolved andlater weapon names remain in overall scope; not declared unused.';return c
def validate(r,book,encoder,decoder):
    if r['key']==3683:assert r['source_text'].startswith('AAA ') and r['text'].startswith('AAA ') and r['text'].count('AAA')==1
    return BATCH.validate(r,book,encoder,decoder)
def negative_cases():
    r,cases=BATCH.negative_cases();assert r['key']==3683
    return r,cases+[('lost_AAA',dict(text=r['text'][4:]))]
SPEC=dict(name='weapons_ac_20261020',config='development_weapons_ac_20261020.json',prior_name='armor_unique_20261020',prior_config='development_armor_unique_20261020.json',
    prior_config_sha256='a7f1aa7f0748b4e29987668a06e1ce33e7c982862ccb2e3ab71fd2657398f111',prior_artifact_sha256='bcfae90d48296ad53998bc1b7eea6589c41731e92fb11f1d6e22c724c177b33a',
    prior_decisions=2748,expected_states=dict(untranslated=1333,needs_human_review=2536,in_progress=104),write_scope='Exact214 static weapon/ammo names, originaltable5u16field0; preserveAAA, no DB/effect/prefix/suffix policy changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

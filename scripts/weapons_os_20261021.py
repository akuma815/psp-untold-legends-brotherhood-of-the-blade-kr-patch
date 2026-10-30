"""78 source names/79DB cells; original duplicate197 references preserved."""
import argparse,sys
from armor_name_common import ArmorNames
from weapons_os_drafts_20261021 import DRAFTS
NOTES=['All78 complete names individually authored; original table5rows1610..1688 has79cells because197 is referenced twice at1613/1614.',
       'No record/value merge: static197 has one source string andtwo original definition consumers. Same-English unbound trans624 stays separate.',
       'Opaline rendered오팔빛 pending material/sheen review. Plated rendered도금 as provisional title wording; exact coating orcrafting material not established.',
       'Runic=룬, Petrified=석화된. No added combat stats, rarity, physical construction, elemental effects or acquisition claims.',
       'Source6FF94owned$i250UTF8 and2048wide unchanged; allprefix/suffix/form templates remain outside this cohort; runtime/layout pending.']
BATCH=ArmorNames(DRAFTS,1610,1689,'Obsidian through Sacred weapon names',NOTES,allowed_categories=(0,1,2,3),expected_reference_counts={197:2})
population=BATCH.population
def context():
    c=dict(BATCH.context());c['semantic_notes']=NOTES;return c
validate=BATCH.validate
negative_cases=BATCH.negative_cases
SPEC=dict(name='weapons_os_20261021',date='20261021',config='development_weapons_os_20261021.json',prior_name='weapons_dl_20261021',prior_config='development_weapons_dl_20261021.json',
          prior_config_sha256='4fee5ef968a36edc8b73df31d48e3df59ec233441f07daee771bb070de9a2b85',prior_artifact_sha256='a909b56aa23972dee626e8d3dffe3281a44070467399ec2be2ac51787768cc79',
          prior_decisions=3098,expected_states=dict(untranslated=1119,needs_human_review=2750,in_progress=104),write_scope='Exact78 static itemnames with79 originaltable5u16field0 refs; no DB or composition changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

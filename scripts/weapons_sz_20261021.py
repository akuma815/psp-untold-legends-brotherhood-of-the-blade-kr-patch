"""Final163 ordinary weapon titles, original table5rows1689..1851."""
import argparse,sys
from armor_name_common import ArmorNames
from weapons_sz_drafts_20261021 import DRAFTS
NOTES=['163 complete names authored individually, not transformed by material/type substitution. All original typed rows and category bytes retained.',
       'Sanguine=핏빛 distinguishes priorCrimson진홍. Scorched=검게 탄 andSeared=그슬린 are title wording proposals, no elemental damage or current item condition inferred.',
       'Serpentine Javeline rendered서펜틴 투창, keeping mineral/snake-form sense unresolved rather than choosing a material from title alone. Original spelling retained.',
       'Ward=수호의, Wrapped=감싼; no specific ward mechanic or wrapping material asserted. Shadow andShadowed wording distinctions retained.',
       'OriginalStilleto spelling stays source-exact. Stave=봉, Staff=지팡이, Dirk=더크, Poniard=포니아드 retained as provisional equipment naming distinctions.',
       'Maul=마울 here; older names used대형 망치. Cross-cohort terminology review pending, no unapproved rewrite of earlier manuscripts.',
       'Source6FF94owned$i250UTF8/2048wide unchanged; prefix/suffix/titleform templates, availability and widget geometry are separate unresolved QA.']
BATCH=ArmorNames(DRAFTS,1689,1852,'Sanguine through Zweihander ordinary weapon names',NOTES,allowed_categories=(0,1,2,3))
population=BATCH.population
def context():
    c=dict(BATCH.context());c['semantic_notes']=NOTES;return c
validate=BATCH.validate
negative_cases=BATCH.negative_cases
SPEC=dict(name='weapons_sz_20261021',date='20261021',config='development_weapons_sz_20261021.json',prior_name='weapons_os_20261021',prior_config='development_weapons_os_20261021.json',
          prior_config_sha256='2b302aa111ef2092aa25ac9af18bd04f7639053649bb1e8530b97aa8efe53b4c',prior_artifact_sha256='457309fec21eef6c428013ffba603040fd93fb22c6143d8c25f54b4cbe35456a',
          prior_decisions=3176,expected_states=dict(untranslated=956,needs_human_review=2913,in_progress=104),write_scope='Exact163 static base weapon names; originaltable5u16field0, no DB/prefix/suffix/code changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

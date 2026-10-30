"""Source-bound names table5 rows1488..1609, preserving already selected413."""
import argparse,sys
from weapons_dl_drafts_20261021 import DRAFTS
from armor_name_common import ArmorNames
NOTES=[
    '122 full names individually authored, no material/type replacement rules. Original table5u16field0 and complete source rows retained.',
    'Existing413Dagger atrow1487 excluded unchanged. Dirk=더크 andPoniard=포니아드 preserve source-title distinctions, without inventing a blade length or equip behavior.',
    'Great=대형 is a provisional item-title qualifier; no superior damage or two-handed use asserted. Convincer remains설득자 following previous weapon proposals.',
    'Jade=옥, Flint=부싯돌. No unsupported stats, crafting material use, projectile operation or actual acquisition assertions.',
    'static178IronBattleAxe has the actual table5row1566 reference; same-English trans617 is a distinct unbound record, not merged or declared unused.',
    'Source name6FF94->DA6342048wide->DA478owned$i250UTF8 unchanged. Geometry, composition and gameplay QA remain pending.'
]
BATCH=ArmorNames(DRAFTS,1488,1610,'Dart through Morningstar weapon names',NOTES,allowed_categories=(0,1,2,3))
population=BATCH.population
def context():
    c=dict(BATCH.context());c['semantic_notes']=NOTES;return c
validate=BATCH.validate
negative_cases=BATCH.negative_cases
SPEC=dict(name='weapons_dl_20261021',date='20261021',config='development_weapons_dl_20261021.json',prior_name='fallback_names_20261021',prior_config='development_fallback_names_20261021.json',
          prior_config_sha256='4d22999e0105b7beca75a95866225b2e535707f80869fe5dd237b40980ddd0c5',prior_artifact_sha256='d0a6179a6d23bda51b826834b8d77943971e1286f411ff23c21cf83ae6b099af',
          prior_decisions=2976,expected_states=dict(untranslated=1197,needs_human_review=2672,in_progress=104),write_scope='Exact122 static base weapon names; originaltable5u16field0, no DB/prefix/suffix/code changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

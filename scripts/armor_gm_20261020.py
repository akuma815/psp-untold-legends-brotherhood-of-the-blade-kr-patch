"""Goldvine throughMoonweave names, same verified item title consumer."""
import argparse
from armor_gm_drafts_20261020 import DRAFTS
from armor_name_common import ArmorNames
BATCH=ArmorNames(DRAFTS,384,585,'Goldvine throughMoonweave armor andshield families',[
    'Source Guilded spelling is retained as 길디드 proposal, not silently corrected toGilded or a gold-plating effect.',
    'Imbued,Marrowhusk,MoonCured set names are provisional lexical readings, not new enchantment/material process evidence.',
    'Maiden andMatron are item-family labels; do not identify a character owner, age or gameclass from them.',
    'Original armor classes checked; no inferred template family expansions. Only201 explicitly authored complete names are selected.'])
population=BATCH.population;context=BATCH.context;validate=BATCH.validate;negative_cases=BATCH.negative_cases
SPEC=dict(name='armor_gm_20261020',config='development_armor_gm_20261020.json',prior_name='armor_cg_20261020',prior_config='development_armor_cg_20261020.json',
    prior_config_sha256='91175ed27b5654b29fd98483bd92daea48fdbfcf0bef0ff4ecde3a02d9c61db3',prior_artifact_sha256='a59d3b892713dc50d90ce0423b8461e8b26b6bc3fa43d23fb11a67d38e6d0c45',
    prior_decisions=1856,expected_states=dict(untranslated=2238,needs_human_review=1631,in_progress=104),write_scope='Exact201 static armor names, originaltable5u16field0; no DB/effect/prefix/suffix policy changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

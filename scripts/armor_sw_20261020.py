"""ShadowedHide throughWoven armor names; completes the generic family cohort."""
import argparse
from armor_sw_drafts_20261020 import DRAFTS
from armor_name_common import ArmorNames
BATCH=ArmorNames(DRAFTS,795,1033,'ShadowedHide throughWoven armor andshield families',[
    'SoftHide andSoftLeather remain separate full source names andproposals, not merged due to similar material wording.',
    'Velvetine source spelling retained as 벨벳틴, not silently corrected toVelvet orVelveteen.',
    'Spirit/Tempest/Valor/Totemic modifiers are equipment-family labels; actual magical effects or character identity not inferred.',
    'Waxed stays a generic wax-treatment proposal, not a specific wax ingredient.',
    'This finishes ordinary named families attable5rows4..1032, not all1273 armorrows or wholegame. Existing1388pants andAAA test-like rows remain distinct.'])
population=BATCH.population;context=BATCH.context;validate=BATCH.validate;negative_cases=BATCH.negative_cases
SPEC=dict(name='armor_sw_20261020',config='development_armor_sw_20261020.json',prior_name='armor_ns_20261020',prior_config='development_armor_ns_20261020.json',
    prior_config_sha256='927c46ed5986633e38515ec23ac6e3c2041764a61d634ce2027b43010e694af7',prior_artifact_sha256='7993d3d376b13145355bc40cc62db165816b8a42ff58f327b4af147fc917371e',
    prior_decisions=2266,expected_states=dict(untranslated=1791,needs_human_review=2078,in_progress=104),write_scope='Exact238 static armor names, originaltable5u16field0; no DB/effect/prefix/suffix policy changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    import sys
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

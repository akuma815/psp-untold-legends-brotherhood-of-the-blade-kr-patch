"""15 exact category13 potion names, no invented recovery amount or mechanics."""
import argparse,sys
from armor_name_common import ArmorNames
DRAFTS={852:'생명력 병',849:'생명력 약병',853:'큰 생명력 병',850:'큰 생명력 약병',859:'큰 기력 병',856:'큰 기력 약병',862:'큰 활력 약병',858:'기력 병',855:'기력 약병',861:'활력 약병',851:'작은 생명력 병',848:'작은 생명력 약병',857:'작은 기력 병',854:'작은 기력 약병',860:'작은 활력 약병'}
NOTES=['15 full titles manually authored. Bottle병/Vial약병 preserve distinct source forms, andSmall작은/Large큰 preserve explicit size qualifiers; no automatic name generation.',
       'Health생명력/Power기력 follow current source-bound UI terminology. Rejuvenation활력 is a provisional name, not a claim of restoring both meters or a specified quantity.',
       'All15 original definitionfield72 areFFFFFFFF, so there is no linked body text to translate. No amount, duration, glass material, auto-use behavior or recipe added.',
       'Same itemname6FF94owned$i250UTF8/2048wide; actual use, purchase, inventory icons, recovery effects and geometry QA pending.']
BATCH=ArmorNames(DRAFTS,2003,2018,'15potion base names',NOTES,allowed_categories=(13,))
population=BATCH.population
def context():
    c=dict(BATCH.context());c['semantic_notes']=NOTES
    for p in population().values():assert int.from_bytes(bytes.fromhex(p['references'][0]['complete_row_hex'])[72:76],'little')==0xffffffff
    return c
validate=BATCH.validate
negative_cases=BATCH.negative_cases
SPEC=dict(name='potion_names_20261021',date='20261021',config='development_potion_names_20261021.json',prior_name='named_jewelry_20261021',prior_config='development_named_jewelry_20261021.json',
          prior_config_sha256='946c2207d9dece62924b9f490a99f9514fb9b5d2734555fd876f52786e7e3f08',prior_artifact_sha256='35a67ead7abeb9dc7f3271c2e4d2eb53e2c3f6ae0f62965d81724f484cb6451c',
          prior_decisions=3483,expected_states=dict(untranslated=797,needs_human_review=3072,in_progress=104),write_scope='Exact15 originaltable5u16field0 potion names; no DB or game-mechanic changes')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

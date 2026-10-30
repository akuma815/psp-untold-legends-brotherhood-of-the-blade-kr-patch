"""144 static titles/151 DB cells; seven selected trans names remain untouched."""
import argparse,sys,struct,json
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from armor_name_common import ArmorNames
from named_jewelry_drafts_20261021 import DRAFTS
SKIP={3929:1878,3930:1879,3931:1880,3933:1882,3935:1884,3936:1886,3937:1887}
NOTES=['44 named weapon proposals and100 jewelry proposals individually authored. Seven trans-name references alreadyselected unchanged, no static duplicate added.',
       'Hailfyre/Wraithfyre/Deadwoe/Stormthroe/Sunderwound/StaticShill/Deathrake/Ripthroat are provisional phonetic names where compound meaning is uncertain; no invented lore or effects.',
       'Zenith Wake, Masters andCerebral naming remain interpretation proposals. Maul vocabulary unification with older대형 망치 pending; previous manuscripts unchanged.',
       'static3989Horizon\'s Breach and3990Netherwail are actual row1881/1883 references. Similar trans3932/3934 are separate unbound records, not merged ordeclared unused.',
       'Jewelry distinguishesAmulet호신부/Charm부적, Band가락지/Ring반지, Hoop고리 귀걸이/Stud장식 귀걸이. Namedearring/stud assets support the interpretation, but icon-to-DB binding andequip slots are not claimed verified.',
       'Deadeye명사수, Ethereal천상의, Spectral유령, Spirit정령 are provisional source-name readings, not accuracy/damage/summon effects. No bonuses inferred.',
       'Source common item-name consumer6FF94->DA6342048wide->DA478owned$i250UTF8 applies; no special acquisition, equip, all-class, prefix/suffix composition or geometry runtime QA.']
class Titles(ArmorNames):
    @lru_cache(maxsize=1)
    def population(self):
        from fallback_names_20261021 import population as fallback
        fallback()
        db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
        ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};off,n=struct.unpack_from('<II',db,40);assert (off,n)==(35748,2088)
        pop={};skipped={}
        for row in range(1852,2003):
            raw=db[off+row*84:off+(row+1)*84];key=struct.unpack_from('<H',raw)[0];assert raw[59] in self.allowed_categories
            if key in SKIP:assert key not in ss;skipped[key]=row;continue
            assert key in DRAFTS and key not in pop and key in ss
            pop[key]=dict(source=ss[key],references=[dict(table=5,row=row,field=0,width=2,stride=84,offset=off+row*84,complete_row_hex=raw.hex(),category=raw[59],effect_id=struct.unpack_from('<I',raw,32)[0])])
        assert skipped==SKIP and set(pop)==set(DRAFTS) and len(pop)==144
        for row in range(n):
            k=struct.unpack_from('<H',db,off+row*84)[0]
            if k in pop:assert row==pop[k]['references'][0]['row']
        assert sum(v['references'][0]['category'] in (10,11,12) for v in pop.values())==100
        return pop
BATCH=Titles(DRAFTS,1852,2003,'Named weapons andjewelry,44+100static proposals/seven priortrans names',NOTES,allowed_categories=(0,1,2,3,10,11,12))
population=BATCH.population
def context():
    c=dict(BATCH.context());c['semantic_notes']=NOTES;c['preserved_trans_references']=SKIP
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));c['supporting_asset_labels_not_runtime_icon_binding']=[r['trailing_label_candidate'] for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1] in ['tex_ui_icon_earring_gold_1x1','tex_ui_icon_earring_iron_1x1','tex_ui_icon_stud_gold_1x1','tex_ui_icon_stud_silver_1x1']]
    return c
validate=BATCH.validate
negative_cases=BATCH.negative_cases
SPEC=dict(name='named_jewelry_20261021',date='20261021',config='development_named_jewelry_20261021.json',prior_name='weapons_sz_20261021',prior_config='development_weapons_sz_20261021.json',
          prior_config_sha256='6b0bce20f9691d370e3f6634175b6b4a758e4cf23af25d7dea0d4aec2fc21eb2',prior_artifact_sha256='c67751ef854db4489a823a0b031395a85369dc24f69a78ada6d962b9edab0d6f',
          prior_decisions=3339,expected_states=dict(untranslated=812,needs_human_review=3057,in_progress=104),write_scope='Exact144 static named weapon/jewelry titles; preserve seven selected trans names andall original DB definitions')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

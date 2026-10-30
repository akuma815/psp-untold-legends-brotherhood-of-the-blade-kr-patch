"""Remaining124 currently catalogued static actor names; exactsource partition."""
import argparse,sys,struct,re,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from actor_named_drafts_20261021 import DRAFTS
from actor_variants_drafts_20261021 import DRAFTS as PRIOR_VARIANTS
PRIOR_OTHER={3001,3041,3198,3237,766,776,886}
@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};off,n=struct.unpack_from('<II',db,16);assert (off,n)==(3464,270)
    pop={};all_static=set()
    for row in range(n):
        raw=db[off+row*112:off+(row+1)*112];key=struct.unpack_from('<H',raw)[0]
        if key in ss:all_static.add(key)
        if key not in DRAFTS:continue
        assert key not in pop and raw[2:4]==bytes.fromhex('cccc')
        pop[key]=dict(source=ss[key],references=[dict(table=2,row=row,field=0,width=2,stride=112,offset=off+row*112,complete_row_hex=raw.hex(),actor_hash=hex(struct.unpack_from('<I',raw,4)[0]),source_HUD_guard=raw[0x5d])])
    assert len(pop)==len(DRAFTS)==124 and set(pop)==set(DRAFTS)
    assert all_static==set(DRAFTS)|set(PRIOR_VARIANTS)|PRIOR_OTHER and len(all_static)==190
    return pop
@lru_cache(maxsize=1)
def context():
    from actor_variants_20261021 import context as prior
    from audit_translation138 import resolve
    from map_corpus_20261020 import decisions
    c=prior();es={e['id']:e for e in lines(ROOT/'workspace/translation/entries.jsonl')};ds=decisions();matches=[]
    queries={}
    for k,v in population().items():
        words=v['source']['source_text'].split();queries[k]=[v['source']['source_text']]
        if words[0] in ['Sir','Lord','Duke','General','Commander','Analyst','Oracle','Scout','Outcast','Lady','Mystic','Acolyte','Madam','Overseer','Shepherd','Elder','Templar','Lieutenant','Blacklord']:queries[k].append(' '.join(words[1:]))
        elif words[0]!='The':queries[k].append(words[0])
    for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl'):
        if s['bank']!='trans':continue
        keys=[k for k,qq in queries.items() if any(q.casefold() in s['source_text'].casefold() for q in qq)]
        if not keys:continue
        e=es[s['id']]
        if e['state']=='untranslated':continue
        did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1]
        matches.append(dict(matched_title_keys=keys,source=s,decision=did,current_manuscript=resolve(ds[did])))
    return dict(source_roundtrip_windows=c['source_roundtrip_windows'],source_anchors=c['source_anchors'],consumer_chain=c['consumer_chain'],current_manuscript_matches=matches,
        preserved_static_actor_keys=sorted(set(PRIOR_VARIANTS)|PRIOR_OTHER),
        semantic_notes=['124 full actor titles individually authored. Corresponding original rows/hash/HUD guard retained; no inferred story chronology from row order or speaker identity from portraits.',
        'Existing manuscript spellings retained for수라가울/아카엘스트라/칼립소/볼토르/브레일린/애시가드/애슬록시아 andcoreNPCgiven names; surnames andnewphonetics are provisional.',
        'Currentmanuscripts containboth프레이톡스 and프레톡스. New actor proposals consistentlyuse프레톡스, matchingnewvariantnames; older manuscripts not silently rewritten. Human terminologyreview remainsrequired.',
        'Scourn is not silently corrected toScourge/scorn: provisionalphonetic스코른 retained. Cardinal uses카디널 toavoid inventing rank/direction identity.',
        'Lord/Duke/Commander/General/Templar/etc are title readings, not new rank mechanics. Eviscerated/Tortured/Writhing descriptions retain source meaning without inferring a quest state.',
        'Leviathan3237 is shared exactsourcekey withnamedweapon, alreadyselected andunchanged. Other old66 staticactor titles andeight trans names unchanged.',
        'All190 currentlycatalogued static actor names are covered after selection, not all270definitions. Missingcatalog keys remainunresolved, not unused. Naturalspawns/HUD guards/layout/speaker QA pending.'])
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\d+',t)==re.findall(r'\d+',s['source_text']);b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t
    check_template(t,'Originalactor705DC2048wide; conservative input bound only, not actorwidget geometry');return b
def negative_cases():
    k=2253;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=766)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text='가'*84))]
SPEC=dict(name='actor_named_20261021',date='20261021',config='development_actor_named_20261021.json',prior_name='actor_variants_20261021',prior_config='development_actor_variants_20261021.json',
          prior_config_sha256='3c35695e8095174d5f33503006ed84401b43407c2ec500eef7552de9d3ce21fd',prior_artifact_sha256='c61df51ab3d4f7d3df91a28e388b565c8d0ee90c552c248aad891b0ab3e407c1',
          prior_decisions=3625,expected_states=dict(untranslated=546,needs_human_review=3323,in_progress=104),write_scope='Exact124 static actorname keys inoriginaltable2; preserve DB/HUDguard andall previous manuscripts')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

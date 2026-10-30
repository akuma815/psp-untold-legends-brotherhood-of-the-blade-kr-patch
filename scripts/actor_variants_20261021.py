"""59 source-linked actor names; neither a complete270-actor nor spawn QA claim."""
import argparse,sys,re,struct,unicodedata
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from actor_variants_drafts_20261021 import DRAFTS
ROWS=[60,70,73,76,77,*range(79,126),*range(127,134)]
@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,16);assert (off,n)==(3464,270);ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};pop={}
    for row in ROWS:
        raw=db[off+row*112:off+(row+1)*112];key=struct.unpack_from('<H',raw)[0];assert key in DRAFTS and key not in pop and raw[2:4]==bytes.fromhex('cccc')
        pop[key]=dict(source=ss[key],references=[dict(table=2,row=row,field=0,width=2,stride=112,offset=off+row*112,complete_row_hex=raw.hex(),actor_hash=hex(struct.unpack_from('<I',raw,4)[0]),source_HUD_guard=raw[0x5d])])
    assert set(pop)==set(DRAFTS) and len(pop)==59
    for row in range(n):
        k=struct.unpack_from('<H',db,off+row*112)[0]
        if k in pop:assert row==pop[k]['references'][0]['row']
    return pop
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    from repair_names474 import SPANS
    from audit_translation138 import resolve
    from map_corpus_20261020 import decisions
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    anchors={0x38360:0x0c01c177,0x38364:0x94a50000,0x383ac:0x0c032614,0x20d60:0x94850000,0x20d64:0x0c01c177}
    for pc,w in anchors.items():assert struct.unpack_from('<I',boot,pc+128)[0]==w,(hex(pc),hex(w))
    q=ROOT/'qa/static/20261021_actor_variants';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    for name,a,z in [x for x in SPANS if x[0].startswith('actor_') or x[0]=='target_name_draw']+[('shared_wide_decoder',0x705dc,0x70678)]:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    es={e['id']:e for e in lines(ROOT/'workspace/translation/entries.jsonl')};ds=decisions();matches=[]
    for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl'):
        if s['bank']!='trans' or not any(w in s['source_text'].casefold() for w in ['gerard','kaylee','praetox','vrultok','gorgein']):continue
        e=es[s['id']]
        if e['state']=='untranslated':continue
        did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1]
        matches.append(dict(source=s,decision=did,current_manuscript=resolve(ds[did])))
    return dict(source_roundtrip_windows=windows,source_anchors={hex(k):hex(v) for k,v in anchors.items()},prior_manuscript_context=matches,
        consumer_chain='Originaltable2 row hash lookup5C520 -> actorrow pointer3B49C/1D50 ->20D60 and38364 lhu0 ->705DC2048wide; ownedcopyBDCB0/BD560 ->C9850draw. Original HUD guard checks retained.',
        semantic_notes=['59 complete proposals individually authored, no class/element string substitution rules. Originaltest labels andnumeric variant IDs retained.',
        'Pal abbreviation remainsLatinPal; 2h retained literally, Epic rendered에픽. These labels do not establish a class, two-hand mechanic or rarity; HUD visibility is unverified.',
        'Fire/Ice/Lightning/Magic/Poison are original name qualifiers, not damage type, resistance, spell selection or combat behavior assertions.',
        'Gerard제라드 andKaylee케일리 match existing manuscripts. New proper-name phonetics andfull title readings remain provisional; portraits are not speaker-identity evidence.',
        '60/70 etc are exactsource row selectors, not progression order. Keys absent fromstatic andtrans catalogs elsewhere in270rows remain unresolved; this is not full actor coverage.',
        'Conservative250UTF8-byte name policy below2048wide, without claiming actorconsumer has the item-owned250slot. Naturalspawn/HUD/layout QA pending.'])
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t) and not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\d+',t)==re.findall(r'\d+',s['source_text'])
    if r['key'] in [3865,3866]:assert 'Pal' in t
    if r['key']==3865:assert '2h' in t
    b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t;check_template(t,'Sourceactor705DC2048wide; conservative input bound, naturalwidget pending');return b
def negative_cases():
    k=2954;r=dict(key=k,source_text=population()[k]['source']['source_text'],text=DRAFTS[k])
    return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=766)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text='가'*84)),
        ('variant_number',dict(key=762,source_text=population()[762]['source']['source_text'],text='남성 희생자 1')),('lost_abbreviation',dict(key=3865,source_text=population()[3865]['source']['source_text'],text='그늘진 Pal 2'))]
SPEC=dict(name='actor_variants_20261021',date='20261021',config='development_actor_variants_20261021.json',prior_name='item_affixes_20261021',prior_config='development_item_affixes_20261021.json',
          prior_config_sha256='d92d3f5b7338f190112607da53028732fafc7ad0a26f65a236d0ad25b071f512',prior_artifact_sha256='35b01b9a01f797f09d3636285b2c5646dfadd90d4c3cc641670c8196a5d9f0b0',
          prior_decisions=3566,expected_states=dict(untranslated=670,needs_human_review=3199,in_progress=104),write_scope='Exact59 static actor-name references; preserve originalDB/HUD guards andall previous manuscripts')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

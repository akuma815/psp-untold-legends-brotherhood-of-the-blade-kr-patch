"""Original T6/T7 -> item pointers -> owned slots -> exact Korean forms."""
import argparse,sys,re,struct,unicodedata,json
from collections import defaultdict,Counter
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from item_affixes_drafts_20261021 import DRAFTS
FORMS={2098:'$i',2099:'$i $s',2108:'$p $i',3080:'$p $i $s'}
FORM_DRAFTS={k:DRAFTS[k] for k in FORMS}
@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};refs=defaultdict(list)
    for table,stride,expected in [(6,28,(211140,18)),(7,64,(211644,164))]:
        off,n=struct.unpack_from('<II',db,table*8);assert (off,n)==expected
        for row in range(n):
            raw=db[off+row*stride:off+(row+1)*stride];key=struct.unpack_from('<H',raw)[0]
            if key==0:continue
            assert key in DRAFTS or key==2890
            refs[key].append(dict(table=table,row=row,field=0,width=2,stride=stride,offset=off+row*stride,complete_row_hex=raw.hex()))
    assert len(refs)==65 and len({k for k,v in refs.items() if v[0]['table']==6})==12 and len({k for k,v in refs.items() if v[0]['table']==7})==53
    assert refs[2890][0]['row']==0 and refs[2890][1]['row']==6
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes()
    for key,pc in [(2098,0x70110),(3080,0x70124),(2108,0x70134),(2099,0x70144)]:
        assert struct.unpack_from('<I',boot,pc+128)[0]==0x34060000|key and ss[key]['source_text']==FORMS[key]
        refs[key].append(dict(source_path='PSP_GAME/SYSDIR/BOOT.BIN',offset=pc+128,width=4,instruction=hex(pc),key=key))
    assert set(refs)==set(DRAFTS)|{2890} and len(DRAFTS)==68
    return {k:dict(source=ss[k],references=v) for k,v in refs.items() if k in DRAFTS}

@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    from map_corpus_20261020 import decisions
    from audit_translation138 import resolve
    assert resolve(decisions()['diagnostic098:2890'])=='망가진'
    calls={0x5d000:0xcbe88,0x5d038:0xcc3dc,0xcc420:0xcbe88,0xcc438:0xba6c4,0x1ae84:0x5c4b0,0x1ae9c:0x2b330,0x2b33c:0x2b46c,0x70054:0xda634,0x7007c:0xda478,0x700c0:0xda634,0x700e8:0xda478,0x70154:0xda634,0xda558:0xd6a68,0xd6b60:0xd7638,0xd7120:0xd7160,0xd7254:0xd7e04,0xd8034:0xd777c}
    for pc,target in calls.items():assert struct.unpack_from('<I',boot,pc+128)[0]==0x0c000000|(target>>2),(hex(pc),hex(target))
    q=ROOT/'qa/static/20261021_item_affixes';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    spans=[('prefix_count',0xcbe88,0xcbe94),('prefix_copy',0xcc3dc,0xcc45c),('prefix_install',0x5cff4,0x5d040),('prefix_lookup',0x5c4b0,0x5c520),
           ('source_instance_construction',0x1ae68,0x1aee4),('item_constructor',0x2b330,0x2b358),('install_prefix_and_effect',0x2b46c,0x2b538),
           ('item_slot_and_four_forms',0x6ff94,0x70180),('wide_to_owned_slot',0xda478,0xda590),('set_slot',0xd6a68,0xd6bac),('copy_owned_slot',0xd7638,0xd76bc),
           ('format_entry',0xd703c,0xd7160),('format_scan',0xd7160,0xd72fc),('keyed_expansion',0xd7e04,0xd8070)]
    for name,a,z in spans:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    return dict(source_roundtrip_windows=windows,call_targets={hex(k):hex(v) for k,v in calls.items()},
        consumer_chain=['CC3DC seeks originalobject+5C=header2C+30 table6 offset; CBE88 readsheader34 count; copy count*28,5D000 installs manager85B70/count85B74.',
        '5C4B0 compares prefixfield4 ID, advances28;1AE84 resolves record,2B330->2B46C stores pointer atitem-instance4. Existing table7effect loader/lookup stores effect pointer atinstance8.',
        '6FF94 readsinstance0/4/8 -> lhu recordfield0 -> DA6342048wide -> DA478 -> D6A68/D7638 owned slots keyed i/p/s. Missing/zero prefix orsuffix is cleared byD6CC4.',
        '70104..70158 chooses exact original2098/2099/2108/3080 depending pointer presence. D7160 scans template; D7E04 indexes object90B0 by encountered variable character, not positional order.',
        'D7E04 invokesD777C to expand encountered slot. Reordering the two explicitly authored forms changes display order, not slot ownership or game state.'],
        preserved_prefix=dict(key=2890,text='망가진',decision='diagnostic098:2890',source_rows=[0,6]),
        original_forms=FORMS,individually_authored_forms=FORM_DRAFTS,source_equal_control_forms=[2098,2108],
        semantic_notes=['64 new linguistic fragments plus4 format-control entries; existingRuined망가진 unchanged. No automatic rewriting of translated prose.',
        'Two exact source templates reorder$i/$s and$p/$i/$s to$s/$i and$s/$p/$i. Variable kinds andmultiplicity preserved; other static templates keep original strict ordering guard.',
        'Each prefix/suffix manually written as one fragment. No bonus, magnitude, probability or elemental behavior inferred from fragment alone. Test-likeofbadness retains literalnegative meaning.',
        'Prefix+base andsuffix+prefix+base use fixed Korean qualifiers, no dynamic particles or gender/number changes. Specific names, terminology andgrammatical collocations require review.',
        'Static bounds andformat ordering are not native formatter execution or natural equip/drop/layout proof. Runtime unavailable after previous native termination.'])

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS;s=population()[r['key']]['source']
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    t=r['text'];assert t and t==unicodedata.normalize('NFC',t)
    if r['key'] in FORMS:
        assert t==FORM_DRAFTS[r['key']] and Counter(re.findall(r'\$[a-z]',t))==Counter(re.findall(r'\$[a-z]',r['source_text']))
    else:assert not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t
    check_template(t,'Original ownedslots250UTF8; finaltemplate2048wide/formatter5000bytes');return b
def negative_cases():
    r=dict(key=2,source_text=population()[2]['source']['source_text'],text=DRAFTS[2])
    return r,[('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=0)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text='가'*84)),
        ('unapproved_order',dict(key=2099,source_text=FORMS[2099],text=FORMS[2099])),('lost_variable',dict(key=3080,source_text=FORMS[3080],text='$s $i')),('repeated_variable',dict(key=2099,source_text=FORMS[2099],text='$s $i $i'))]
SPEC=dict(name='item_affixes_20261021',date='20261021',config='development_item_affixes_20261021.json',prior_name='potion_names_20261021',prior_config='development_potion_names_20261021.json',
          prior_config_sha256='7bfdd61f5290d6e1b0519a502d636add52ec7b6a810e52f416b369c7c66cc379',prior_artifact_sha256='0b559c7bf3fedc9960073a4a9045b87e472ebf53738c7d54d4ee99472e57e07d',
          prior_decisions=3498,expected_states=dict(untranslated=729,needs_human_review=3140,in_progress=104),expected_unchanged_static_keys=[2098,2108],
          write_scope='Exact64 new affix fragments plus4 control forms, twoexplicit order changes; preserve all original DB andexistingRuined wording')
if __name__=='__main__':
    import static_name_batch_pipeline as pipeline
    p=argparse.ArgumentParser();p.add_argument('action',choices=['select','audit']);a=p.parse_args();getattr(pipeline,a.action)(SPEC,sys.modules[__name__],DRAFTS)

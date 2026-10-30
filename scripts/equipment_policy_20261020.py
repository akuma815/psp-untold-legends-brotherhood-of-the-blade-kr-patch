"""Source table7 field44 through actual item-effect consumers; no DB writes."""
import re,struct,unicodedata
from collections import defaultdict
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from equipment_drafts_20261020 import DRAFTS as NEW
from ability_corpus_drafts_20261020 import EFFECTS

POLICY='table7_item_effect_field44_705DC_plain_CRLF_2048_v1'
KEYS=set(NEW)|set(EFFECTS)
SPANS=[('db_header',0xcbdb8,0xcbe48),('effect_count',0xcbe94,0xcbea0),('effect_copy',0xcc45c,0xcc4d4),
       ('effect_load',0x5d040,0x5d078),('effect_lookup',0x5c440,0x5c4b0),('item_effect_install',0x2b3e0,0x2b46c),
       ('item_effect_install_explicit',0x2b46c,0x2b538),('selected_effect_description',0x27904,0x279fc),
       ('category5_effect_descriptions',0x27c20,0x27d88),('sync_decoder',0x705dc,0x70678),('CRLF_owned_normalizer',0x4717c,0x47234)]

@lru_cache(maxsize=1)
def context():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    off,n=struct.unpack_from('<II',db,56);assert (off,n)==(211644,164)
    fields=defaultdict(list);rows=[];ids=set()
    for row in range(n):
        raw=db[off+row*64:off+(row+1)*64];effectid=struct.unpack_from('<I',raw,4)[0];assert effectid not in ids;ids.add(effectid)
        k=struct.unpack_from('<I',raw,44)[0]
        if k==0xffffffff:continue
        assert k in KEYS
        fields[k].append((7,row,44));rows.append(dict(table=7,row=row,stride=64,offset=off+row*64,key=k,effect_id=effectid,complete_row_hex=raw.hex()))
    assert set(fields)==KEYS and len(fields)==77 and len(rows)==77 and len(NEW)==60 and len(EFFECTS)==17
    anchors={0xcbe20:0x2625002c,0xcbe2c:0x340600a8,0xcbe9c:0x8c82003c,0xcc480:0x8e250064,
             0xcc4a8:0x00023180,0x5d050:0xac825b7c,0x5d05c:0x00042180,0x5d068:0xac825b78,
             0x5c468:0x8ce75b78,0x5c474:0x8caa0004,0x5c490:0x24a50040,
             0x2b438:0xae040008,0x27904:0x8e900008,0x279d0:0x8e05002c,0x279d4:0x0c01c177,
             0x279e0:0x0c02f72c,0x70644:0x0c03698d,0x70648:0x34060800}
    for pc,w in anchors.items():assert struct.unpack_from('<I',boot,pc+128)[0]==w,(hex(pc),hex(struct.unpack_from('<I',boot,pc+128)[0]),hex(w))
    # Verify byte-identical assembly across the complete relevant original windows.
    from allegrex_profile import Profile
    profile=Profile();q=ROOT/'qa/static/20261020_equipment_consumer';q.mkdir(parents=True,exist_ok=True);windows=[]
    for name,a,z in SPANS:
        raw=boot[a+128:z+128];decoded=profile.verify_roundtrip(raw,a,q,name)
        windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instruction_count=len(decoded)))
    return dict(fields=dict(fields),complete_rows=rows,source_instruction_anchors={hex(k):hex(v) for k,v in anchors.items()},source_roundtrip_windows=windows,
        new_manuscripts=60,prior_manuscripts_selected_unchanged=17,all_nonnegative_table7_description_keys=77,
        consumer_chain=['CBDB8 reads168-byte original header to object+2C; CBE94 count at2C+3C equals table7 count.',
            'CC45C seeks header offset atobject64 (2C+38), copies count*64;5D040 installs allocated records atmanager85B78/count85B7C.',
            '5C440 compares effect-ID field4, advances64;2B438/2B4D4 install record atitem-instance8.',
            '27904 loads selected item-instance8,279D0 passes effect+2C to705DC,279E0 copies wide result withBDCB0,4717C changes CR ofCRLF to space in owned copy.',
            'Category5 branch27C20 resolves two original effect IDs and passes each samefield44 through705DC andowned wide copy.',
            '705DC callsDA634 with2048wide capacity, returns scratch+20 beforeowned copy; values are plain finite source text.'],
        limitations=['Static consumer evidence only; no natural equipment obtain/equip/hover/paging/layout/probability/combat QA.',
            'Exact ++ signs, digits, percent runs, colon count and CRLF retained; source anomalies are not corrected.',
            'Stamina=체력, Health=생명력, Power=기력 follow existing static UI labels. Earlier ability wording was not silently changed.',
            'Effect titles are provisional descriptions; suffix fragments and namespace-mismatched names require separate composition/fallback investigation.'])

ALL_FIELDS=context()['fields'];FIELDS=ALL_FIELDS
@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in FIELDS:
        s=ss[k];b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256'] and b==s['source_text'].encode('utf8')
    return {k:ss[k] for k in FIELDS}

def punctuation(s):return re.findall(r'\+\+ ?\d+|%+|:|\r\n',s)
def validate_draft(k,text,book,encoder,decoder):
    s=sources()[k];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\t[]{}$#&*<=>\\^~')
    assert punctuation(text)==punctuation(s['source_text']) and re.findall(r'\d+',text)==re.findall(r'\d+',s['source_text'])
    assert '\r' not in text.replace('\r\n','') and '\n' not in text.replace('\r\n','')
    b=encoder(text,book).encode('utf8');assert decoder(b.decode('utf8'),book)==text and len(b)+1<=5000
    check_template(text,'Original effect description705DC2048wide; natural widget geometry pending')
    return b
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY and r['source_text']==sources()[r['key']]['source_text']
    return validate_draft(r['key'],r['text'],book,encoder,decoder)
def negative_cases(drafts):
    k=2996;r=dict(key=k,source_text=sources()[k]['source_text'],text=drafts[k],control_policy=POLICY)
    return r,[('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3773)),('changed_number',dict(text=r['text'].replace('3','4'))),
        ('lost_plus',dict(text=r['text'].replace('++','+'))),('changed_percent',dict(text=r['text'].replace('%','%%'))),
        ('lost_CRLF',dict(text=r['text'].replace('\r\n',' '))),('NUL',dict(text=r['text']+'\0')),('page',dict(text=r['text']+'[p]')),
        ('overflow',dict(text=r['text']+'가'*2048))]

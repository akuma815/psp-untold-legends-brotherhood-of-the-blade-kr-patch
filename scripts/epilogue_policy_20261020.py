"""Exact three epilogue selector branches, owned concatenation and background tags."""
import json,re,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
from epilogue_drafts_20261020 import DRAFTS

POLICY='epilogue_selector_1_2_3_exact_background_paragraphs_2048_v1'
FIELDS={3882:[('BOOT_selector',0x709d4,1)],4004:[('BOOT_selector',0x709e8,2)],4005:[('BOOT_selector',0x709f8,3)]};ALL_FIELDS=FIELDS
@lru_cache(maxsize=1)
def sources():
    ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans'};raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    for k in FIELDS:
        s=ss[k];b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256'] and b==s['source_text'].encode('utf8')
    return {k:ss[k] for k in FIELDS}
@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    anchors={0x709d4:0x34060f2a,0x709e8:0x34060fa4,0x709f8:0x34060fa5,0x70a58:0x0c03698d,0x70a5c:0x34060800,
        0x6eb4c:0x0c01c26a,0x6eb50:0x34050001,0x6eb58:0x0c02f72c,0x6eb7c:0x0c01c26a,0x6eb80:0x34050002,
        0x6eb88:0x0c02f773,0x6eb9c:0x0c01c26a,0x6eba0:0x34050003,0x6eba8:0x0c02f773,0x6ebc0:0x0c01b771}
    for pc,w in anchors.items():assert struct.unpack_from('<I',boot,pc+128)[0]==w,(hex(pc),hex(struct.unpack_from('<I',boot,pc+128)[0]),hex(w))
    ranges=[('selector_decode',0x709a8,0x70a94),('owned_epilogue_concat',0x6eb00,0x6ebd0),('owned_append_capacity',0xbddcc,0xbde64),
            ('CRLF_normalizer',0x6ef40,0x6efb0),('background_parser',0x6ddc4,0x6e26c)]
    p=Profile();q=ROOT/'qa/static/20261020_epilogue_consumer';q.mkdir(parents=True,exist_ok=True);windows=[]
    for name,a,z in ranges:
        raw=boot[a+128:z+128];dec=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(dec)))
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));assets={}
    for s in sources().values():
        for tag in re.findall(r'\[bg_([^\]]+)\]',s['source_text']):
            matches=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag];assert len(matches)==1;assets[tag]=matches[0]
    assert set(assets)=={f'SL_end{n}' for n in range(1,6)}
    return dict(fields=FIELDS,selector_order=[3882,4004,4005],source_roundtrip_windows=windows,background_assets=assets,
        paragraph_alignment={k:[dict(ordinal=i,source=s,text=t) for i,(s,t) in enumerate(zip(sources()[k]['source_text'].split('\r\n\r\n'),DRAFTS[k].split('\r\n\r\n')))] for k in FIELDS},
        consumer_chain=['709A8 maps selector1/2/3 to3882/4004/4005;70A58 DA6342048wide per section,6F0DC resource handling and6EF40 CRLF normalizer.',
            '6EB40 copies selector1 toownedobject14,6EB70/90 append selector2/3 withBDDCC before6DDC4 parses background tags.',
            'BDDCC compares required sum length against ownedcapacity and callsBD920 withsum+20 before append; do not apply per-section2048limit to entire scroll.',
            '6DDC4 same original background consumer: exactfive endtags retained; original054 hash correspondence and matching WAD assets preserved.'],
        limitations=['Static selection/copy/append/background evidence; ending trigger, natural scrolling, allfive backgrounds, timing, wrapping and complete playthrough remain runtime-unverified.',
            'Original leadingCRLF on4004/4005 and all paragraph/tag positions retained; no invented ending, gendered Guardian or changed Task/Crown interpretation.',
            'Names and lore remain development proposals; no human approval or release eligibility.'])
def validate_draft(k,text,book,encoder,decoder):
    s=sources()[k]['source_text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\t{}$#%&*+<=>\\^~')
    aa=s.split('\r\n\r\n');bb=text.split('\r\n\r\n');assert len(aa)==len(bb) and bool(s.startswith('\r\n'))==bool(text.startswith('\r\n'))
    assert re.findall(r'\r\n+',s)==re.findall(r'\r\n+',text) and '\r' not in text.replace('\r\n','') and '\n' not in text.replace('\r\n','')
    for a,b in zip(aa,bb):
        tags=re.findall(r'\[[^\]]+\]',a);assert tags==re.findall(r'\[[^\]]+\]',b)
        if tags:
            assert len(tags)==1 and re.fullmatch(r'\[bg_SL_end[1-5]\]',tags[0])
            assert a.lstrip('\r\n').startswith(tags[0]) and b.lstrip('\r\n').startswith(tags[0])
    b=encoder(text,book).encode('utf8');assert decoder(b.decode('utf8'),book)==text and len(b)+1<=5000
    check_template(text,'Epilogue section2048wide; owned full scroll grows separately; runtime geometry pending')
    return b
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY and r['source_text']==sources()[r['key']]['source_text']
    return validate_draft(r['key'],r['text'],book,encoder,decoder)
def negative_cases(drafts):
    k=4004;r=dict(key=k,source_text=sources()[k]['source_text'],text=drafts[k],control_policy=POLICY)
    return r,[('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=3881)),('background_changed',dict(text=r['text'].replace('SL_end3','SL_end1'))),
        ('paragraph_lost',dict(text=r['text'].replace('\r\n\r\n',' ',1))),('leading_CRLF_lost',dict(text=r['text'][2:])),
        ('new_page',dict(text=r['text']+'[p]')),('variable',dict(text=r['text']+'$a')),('overflow',dict(text=r['text']+'가'*2048))]

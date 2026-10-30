"""56 individually authored ability titles and their original definition consumers."""
import re,struct,unicodedata,json
from functools import lru_cache
from collections import defaultdict
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

DRAFTS={808:'화염 탄환',809:'쌍수 무기',813:'방어',814:'근접 공격',815:'궁술',816:'다중 사격',817:'치명 사격',818:'상처 치유',
819:'연속 공격',820:'인내',823:'강타',824:'반격',825:'용맹의 오라',826:'쪼개기',827:'방패 치기',828:'화살 회수',829:'힘의 귀감',
830:'산성 분사',831:'화염 폭탄',833:'골렘 제작',834:'골렘 폭파',835:'독 탄환',836:'마법진',837:'변환',
2952:'자연의 약',2953:'쏘기',2956:'기력 끌어오기',2875:'늪지',2877:'경계 태세',2879:'석화의 시선',2882:'연쇄 번개',2881:'정신 교란',2874:'물약 제조',
3017:'야성의 돌진',3018:'질주',3061:'찢기',3023:'난타',3045:'휘감는 덩굴',3044:'상처의 오라',3046:'북방의 숨결',3047:'고요한 마음',
3048:'가시 망토',3049:'번개 타격',3050:'지진',886:'폭풍',3052:'대지 정화',3053:'꿰뚫는 울부짖음',3054:'무리의 냄새',3055:'피를 얼리는 공포',
3057:'죽음의 숨결',3024:'투척 무기',3025:'투척 무기 회수',3026:'야만의 일격',3027:'가시 미끼',3035:'바위 폭풍',3058:'광기 감염'}

@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    src={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};off,n=struct.unpack_from('<II',db,96);assert (off,n)==(308604,298)
    rows=defaultdict(list);unresolved=[]
    for row in range(n):
        raw=db[off+row*92:off+(row+1)*92];key=struct.unpack_from('<I',raw,60)[0]
        if key not in src:unresolved.append(dict(row=row,key=key,reason='Catalogue namespace unresolved orzero; not declared unused'));continue
        assert key in DRAFTS
        rows[key].append(dict(table=12,row=row,field=60,width=4,stride=92,offset=off+row*92,complete_row_hex=raw.hex(),description_key=struct.unpack_from('<I',raw,64)[0]))
    assert set(rows)==set(DRAFTS) and len(rows)==56
    return dict(titles={k:dict(source=src[k],references=v) for k,v in rows.items()},unresolved_title_definitions=unresolved,
        mapped_title_reference_cells=sum(map(len,rows.values())),all298_definitions_accounted_for=sum(map(len,rows.values()))+len(unresolved)==298)

@lru_cache(maxsize=1)
def consumer():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    anchors={0x13758:0x8e250000,0x13760:0x0c01c177,0x13764:0x8ca5003c,0x1376c:0x0c02f72c,
        0x137d8:0x02203025,0x137e0:0x0c006a2d,0x1aafc:0x8e460000,0x1ab04:0x8cc50040,
        0x5e4:0x8c850000,0x5ec:0x0c01c177,0x5f0:0x8ca5003c,0x638:0x0c032614}
    for pc,w in anchors.items():assert struct.unpack_from('<I',boot,pc+128)[0]==w,(hex(pc),hex(struct.unpack_from('<I',boot,pc+128)[0]),hex(w))
    q=ROOT/'qa/static/20261020_ability_titles';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    for name,a,z in [('rank_title_description',0x13714,0x13820),('direct_title_draw',0x5d0,0x640),('title_decoder',0x705dc,0x70678)]:
        raw=boot[a+128:z+128];dec=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(dec)))
    return dict(source_roundtrip_windows=windows,anchors={hex(k):hex(v) for k,v in anchors.items()},
        chain='13758 loads same definition as137D8->1A8B4 description: titlefield60->705DC2048wide->BDCB0owned wide. Direct5E0/5F0 title route copiesowned and passesC9850 draw.',
        original_definition_identity='Existing052 native Block first92bytes equals originaltable12row71; ability_corpus_policy proves exact descriptionfield64 chain using same instance0 definition.',
        limits='2048wide per title decoder,5000byte formatter; all proposals plain short names. Pixel geometry, allclasses/ranks and availability are separate runtime QA.',
        naming='Full source names individually composed with corresponding original descriptions/current manuscripts. Provisional ability terminology, no global text transformations or new approvals.')

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS
    s=population()['titles'][r['key']]['source'];raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    b=encoder(text,book).encode('utf8');assert len(b)+1<=5000 and decoder(b.decode('utf8'),book)==text
    check_template(text,'Source definitionfield60 ability title2048wide; geometry/runtime pending')
    return b

"""66 individual category13 item-name proposals with exact original u16 consumers."""
import re,struct,unicodedata
from functools import lru_cache
from collections import defaultdict
from survey import ROOT,digest
from catalog_survey034 import lines

DRAFTS={
3483:'철의 돌',3484:'그늘의 해골',3485:'바람의 토템',3486:'은은히 빛나는 수정',3487:'불탄 해골',3488:'폭풍의 토템',
3489:'냉기의 사파이어',3490:'화염의 루비',3491:'미덕의 돌',3492:'사악한 해골',
2252:'먼지 쌓인 고서',2531:'찢어진 일지 쪽',840:'아다만틴 밧줄',2563:'순수의 방패',845:'부적 조각',2260:'오래된 일지',
842:'아스트랄 물약',2713:'뼈 유골함',2920:'이가 나간 다이아몬드 반응로',2262:'증류 수정',2630:'마법이 깃든 일지',
841:'에테르 열쇠',2714:'에테르 유골함',2849:'갈라진 강철 챔버',2711:'황금 유골함',
3684:'고대 일지 I권',3698:'고대 일지 X권',3699:'고대 일지 XI권',3708:'고대 일지 XII권',3700:'고대 일지 XIII권',
3701:'고대 일지 XIV권',3702:'고대 일지 XV권',3703:'고대 일지 XVI권',3690:'고대 일지 II권',3691:'고대 일지 III권',
3692:'고대 일지 IV권',3693:'고대 일지 V권',3694:'고대 일지 VI권',3695:'고대 일지 VII권',3696:'고대 일지 VIII권',3697:'고대 일지 IX권',
3659:'리세타의 돌',2712:'대리석 유골함',2637:'메리디언의 조각',843:'구슬',2624:'봉인의 구슬',847:'페일 에일 술통',
2635:'피너클의 조각',838:'프레이톡스의 독',2647:'너덜너덜한 일지 쪽',3112:'로넌이 휘갈긴 쪽지',2598:'재생의 연고',839:'아벤의 인장',
2785:'셰일룬 검',3533:'형제단의 인장',2794:'제라드 경의 증언',2634:'스파이어의 조각',2638:'서밋의 조각',2691:'타엘의 기록',
2918:'아벤의 고서',3497:'아벤의 고서 II권',844:'간수의 열쇠',2812:'나그네의 책',2770:'와일드문 토템',2636:'제니스의 조각',846:'베리하트 꽃잎'
}

@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    off,n=struct.unpack_from('<II',db,40);assert (off,n)==(35748,2088)
    src={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'};rows=defaultdict(list)
    for row in range(2018,n):
        raw=db[off+row*84:off+(row+1)*84];key=struct.unpack_from('<H',raw)[0];assert raw[59]==13
        if key not in {2523,2263,3003}:rows[key].append(dict(table=5,row=row,field=0,width=2,stride=84,offset=off+row*84,complete_row_hex=raw.hex(),field72_candidate=struct.unpack_from('<I',raw,72)[0]))
    assert set(rows)==set(DRAFTS) and len(rows)==66 and sum(map(len,rows.values()))==67
    return {k:dict(source=src[k],references=refs) for k,refs in rows.items()}

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text'} and r['key'] in DRAFTS
    s=population()[r['key']]['source'];raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    # Individual volume labels retain the exact source Roman numeral, not a prose conversion rule.
    roman=re.search(r'Volume ([IVX]+)$',s['source_text'])
    if roman:assert text.endswith(' '+roman[1]+'권')
    encoded=encoder(text,book).encode('utf8');assert len(encoded)+1<=250 and decoder(encoded.decode('utf8'),book)==text
    return encoded

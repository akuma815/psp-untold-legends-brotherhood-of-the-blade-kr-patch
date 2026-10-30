"""Nine exact illness followups plus immutable neighbouring quest context."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={3762:(11,8),3863:(12,8),3612:(14,9),2455:(14,10),2454:(14,11),3609:(14,38),3610:(14,39),3611:(14,40),3613:(14,41)}
ANCHORS={2343,2344,2345,2347,2395,2396,2311,2441,2443,2444,2445,2446,2447,2448,2450,2482}
def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};source=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in source if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));fields=[];records=[]
    for row in [1,11,12,14]:
        raw=db[336020+row*260:336020+(row+1)*260]
        for word,key in enumerate(struct.unpack('<65I',raw)):fields.append(dict(row=row,word=word,u32=key,complete_row_sha256=digest(raw)))
    for key,(row,word) in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and 'BUG' not in s['source_text'].upper()
        assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==key
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        tag=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tag)==1
        match=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag[0]];assert len(match)==1
        refs=[dict(row=f['row'],word=f['word']) for f in fields if f['u32']==key]
        records.append(dict(key=key,source=s,row=row,word=word,all_refs_in_four_rows=refs,portrait=tag[0],portrait_WAD=match[0]))
    p=b/'packets/illness325';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'full_four_rows.jsonl',serialized(fields));protected_write(p/'source_context.jsonl',serialized(records))
    anchors=[s for s in source if (s['bank']=='trans' and s['key'] in ANCHORS) or (s['bank']=='static' and s['key'] in [38,2262])]
    for s in anchors:
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    protected_write(p/'quest_anchor_sources.jsonl',serialized(anchors))
    protected_write(p/'REVIEW.md','''# 질병 후속9개 — 325

table13 row1/11/12/14 전체260필드,9개 대상과 원본 quest 단위의 주변 문맥을 보존했다.3762/3863은 row8과38에 같은 key가 들어 있다. 배열 순서를 실제 사건 순서로 단정하지 않는다.

3762는 병 또는 저주라는 전언이며 감염 원인을 확정하지 않는다.3863은 케일리나 감독관이 죽는다면이라는 조건부 경고다. 리세타의3612는 시간 부족,3609는 서쪽 지하묘지로의 독촉,3610은 죽음보다 더 나쁜 그림자의 광기를 우려한다.3611은 케일리의 회복 가능성을 맡은 상태이지 완치 선언이 아니다.3613은 해독제 제조에 증류 수정이 필요하다는 뜻이며 손에 이미 수정이 있다는 문장을 덧붙이지 않는다.

2455는 회수한 책과 예언에 관한 장로와의 대화,2454는 케일리에게 현재 사안을 물으라는 지시다. prophecy의 정체와 책 내용은 원문에 없는 설명을 붙이지 않는다. 장로 이름은 본문에 없는 경우 덧붙이지 않는다.

static38 Western Catacombs와 static2262 Distilling Crystal을 명칭 대조용으로 포함했다. 명칭은 개발 초안이며 승인1건인 울부짖는 소나무 여관 이외에는 인간 승인으로 올리지 않는다. Alice2318의 half her elbow는 범위 표현이 애매해 이번 대상에서 제외한다. BUG·후기 결말 행도 선택하지 않는다.
''')
    save_json(ROOT/'qa/reports/illness_stage325_context.json',dict(status='PASS_325_NINE_ILLNESS_FOLLOWUPS_CONTEXT',fields=260,keys=list(FIELDS),anchors=len(anchors),source_backed_portraits=9,wording_or_game_changes=0,release_eligible=False))
    print('PASS325 full260fields/nine exact source slots and portraits/quest anchors')
if __name__=='__main__':main()

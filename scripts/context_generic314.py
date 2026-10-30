"""Four source NPC rows and16 generic slots;immutable source context."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2348:(9,1),2342:(9,2),2349:(9,3),2350:(9,4),2355:(11,1),2356:(11,2),2357:(11,3),2358:(11,4),
        2359:(12,1),2360:(12,2),2361:(12,3),2362:(12,4),2367:(14,1),2368:(14,2),2369:(14,3),2370:(14,4)}
def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};ss={s['key']:s for s in lines(b/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    fields=[];records=[];wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'))
    for row in [9,11,12,14]:
        raw=db[336020+row*260:336020+(row+1)*260];w=struct.unpack('<65I',raw)
        for word,key in enumerate(w):fields.append(dict(row=row,word=word,u32=key,complete_row_sha256=digest(raw)))
    assert len(fields)==260
    for k,(row,word) in FIELDS.items():
        s=ss[k];assert es[s['id']]['state']=='untranslated'
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256'] and 'BUG' not in s['source_text'].upper()
        assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==k
        tag=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tag)==1
        match=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag[0]];assert len(match)==1
        records.append(dict(key=k,source=s,row=row,word=word,selector=word,portrait=tag[0],portrait_WAD=match[0]))
    p=b/'packets/generic314';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'full_four_rows.jsonl',serialized(fields));protected_write(p/'source_context.jsonl',serialized(records))
    notes='''# 일반 대사16개 — 314

table13 row9/11/12/14 전체260필드와 generic selector1~4를 연결했다. 레일라의 소네트/공연과 네이선의 모험심,도리안·프라이스의 카드놀이·로넌 상실 반응,리세타의 인사와 역사를 기록하는 태도가 원문 단위의 문맥이다.

Layla2349의 love and fortune은 특정 연애 관계를 새로 확정하지 않는다.2350의 영웅이 나중에 전사한다면이라는 어색한 발언과 말끝 흐림을 순화하거나 삭제하지 않는다. 도리안2356의 us가 누구인지 이름을 덧붙이지 않고,프라이스2360은 lad/Nathan 문맥을 유지한다.2362는 돌려받지 못할 빚에 대한 자기중심적인 탄식이다.

리세타2369 acolytes와2370 zenith는 이번 화자/문맥의 임시 초안으로 인간 승인이 없다. speaker-to-addressee 말투는 기존 개발 초안의 각 인물 말투와 맞추되 승인으로 올리지 않는다. 다른 행의 *BUG THIS*/*BUG ME*는 변경·선택하지 않는다. 보관 순서가 실제 무작위 발화 순서라는 주장은 하지 않는다.
'''
    protected_write(p/'REVIEW.md',notes)
    save_json(ROOT/'qa/reports/generic_stage314_context.json',dict(status='PASS_314_FOUR_COMPLETE_ROWS_16_GENERIC_SLOTS',fields=260,keys=list(FIELDS),wording_or_game_changes=0,release_eligible=False))
    print('PASS314 four complete rows260fields/16 generic slots/16 exact portrait resources')
if __name__=='__main__':main()

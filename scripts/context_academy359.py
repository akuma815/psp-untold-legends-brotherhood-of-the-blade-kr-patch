"""Five source NPC rows and20 generic slots;immutable source context."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2408:(4,1),2409:(4,2),2410:(4,3),2411:(4,4),2418:(5,1),2419:(5,2),2420:(5,3),2421:(5,4),2426:(6,1),2427:(6,2),2428:(6,3),2429:(6,4),2430:(7,1),2431:(7,2),2432:(7,3),2433:(7,4),2371:(15,1),2372:(15,2),2373:(15,3),2374:(15,4)}

REVIEW="""# 다섯 인물 일반 대사20개 — 359

table13 row4/5/6/7/15의 전체325필드와 selector1~4를 보존했다. 아이다스·그레일린·마이아·사빈·케일리의 정확한 초상화 자원과 원문 바이트/해시를 연결했다. 배열 순서와 실제 무작위 발화 순서는 구분한다. BUG가 포함된 Bron/Brady/Ronan 행은 선택하지 않는다.

2409의 grace/reseed는 드루이드가 말하는 세계관 표현이다. 구체적인 마법 원리나 생태 복구 단계는 원문에 없으므로 덧붙이지 않는다.2411의 dread to cross는 길을 건너는 뜻이 아니라 적대하기 두렵다는 뜻이다.

2418은 장로가 흡수한 오염이 몸에 부담을 주고 수명이 줄어드는 상황을 설명하며,곧 상실을 느낄 것이라는 예고다. 이미 죽었다는 서술로 바꾸지 않는다.2421은 케일리가 사람들의 사랑을 편안히 받아들이지 못하는 자존감에 관한 평가이며,사랑받지 못한다고 뒤집지 않는다.

2428의 도난은 화자의 연구실 물품이며,아카데미의 증류 수정 도난과 동일 사건으로 단정하지 않는다.2429의 druids/cause를 특정 사망이나 희생 의식으로 확장하지 않는다.

2430의 잔혹한 영웅적 행동을 즐거워하는 화자의 태도를 순화하지 않는다.2432의 mistress와sisters는 지칭 대상을 이 묶음만으로 확정하지 않는다.친자매나 특정 부대를 새로 명명하지 않는다.

2371은 원문이 Queen을 쓴다.다른 원문의Crown과 차이가 있으므로 원문어감을 보존하되 최종 용어 검토에 남긴다.2372는 한 사람이 변화를 일으킬 수 있느냐는 질문,2373은 자신의 역할에 대한 반문,2374는 두 사람 중 주인공이 더 강할지도 모른다는 화자의 생각이다. 확정 판단으로 바꾸지 않는다.

새 고유명사·신앙 표현·말투는 개발 초안이며 인간 승인이 없다.자연NPC선택·후속사건·장로의생사·완주·저장·배포 검증으로 확대하지 않는다.
"""

def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};ss={s['key']:s for s in lines(b/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    fields=[];records=[];wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'))
    for row in [4,5,6,7,15]:
        raw=db[336020+row*260:336020+(row+1)*260];w=struct.unpack('<65I',raw)
        for word,key in enumerate(w):fields.append(dict(row=row,word=word,u32=key,complete_row_sha256=digest(raw)))
    assert len(fields)==325
    for k,(row,word) in FIELDS.items():
        s=ss[k];assert es[s['id']]['state']=='untranslated'
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256'] and 'BUG' not in s['source_text'].upper()
        assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==k
        tag=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tag)==1
        match=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag[0]];assert len(match)==1
        records.append(dict(key=k,source=s,row=row,word=word,selector=word,portrait=tag[0],portrait_WAD=match[0]))
    p=b/'packets/academy359';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'full_five_rows.jsonl',serialized(fields));protected_write(p/'source_context.jsonl',serialized(records))
    notes=REVIEW
    protected_write(p/'REVIEW.md',notes)
    save_json(ROOT/'qa/reports/academy_stage359_context.json',dict(status='PASS_359_FIVE_COMPLETE_ROWS_20_GENERIC_SLOTS',fields=325,keys=list(FIELDS),wording_or_game_changes=0,release_eligible=False))
    print('PASS359 five complete rows325fields/20 generic slots/20 exact portrait resources')
if __name__=='__main__':main()

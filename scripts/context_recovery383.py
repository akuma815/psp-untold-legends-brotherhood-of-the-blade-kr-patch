"""Seventeen remaining invasion/illness/crystal reminders; full source rows preserved."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2318:(1,9),2412:(4,7),2414:(4,8),2415:(4,38),2416:(4,9),2417:(4,39),2422:(5,7),2424:(5,8),2425:(5,38),3059:(7,37),3060:(6,37),2375:(15,8),2376:(15,38),2377:(15,9),2378:(15,39),3615:(15,40),3614:(15,41)}
REVIEW='''# 침공·질병·수정 회수 후속17개 — 383

table13 row1/4/5/6/7/15 전체390필드와17개 정확한 key/word/원문/초상화WAD를 연결했다. word7/37처럼 같은 key가 반복되어도 하나의 원문을 두 번 번역한 것으로 세지 않는다. 기존 질병·해독제·성소·수정회수 대사와 연결해 원문 상태의 차이를 보존한다.

앨리스2318은 물릴 뻔했지만 실제 물렸다는 말은 아니다. 케일리의 팔이 보랗게 변했다는 소문과 감독관도 그렇다는 질문은 화자의 전언·반응이다. 아이다스2412는 숲과 신전이 침공 피해를 입지 않았다는 말이며,아카데미도 그러했기를 바라는 것과 구분한다.2414는 아직 소식을 받지 못했고2416은 감독관이 이야기할 수 있게 된 이후의 계획이다.2415는 기도와 행동의 역할을 구분하며,coven은 기존 문맥의 동료 드루이드들로 옮기는 개발 초안이다.2417은 여왕의 독을 해독제 재료로 기대하는 단계이며 완성된 치료/효과 실측이 아니다.

그레일린2422는 장로가 안전하게 신전으로 돌아왔음을 말하고 서쪽 지하묘지에서 계단 위로 이동하는 프레이톡스를 목격했다.2424/2425의 행운과 비극은 구체적인 사망을 임의로 넣지 않는다.사빈3059는 계단과 시장 광장을 통한 아카데미 방향·맨홀 경계·평소 공격적이지 않았다는 관찰을 보존한다.마이아3060의 [p] 토큰 및 앞뒤 CRLF는 원문 그대로 유지한다.기존057에서 [p]의 강제 페이지 분할은 관찰되지 않았으므로 이번에도 강제 분할 기능을 주장하지 않는다.

케일리2375/2377은 병든 상태에서 감독관을 우선하라는 부탁,2376은 통증과 비슷하지만 꼭 아프지는 않은 감각과 두려움이다.3615는 성소의 마력이 소진되었을 때의 조건부 위험,3614는 수정 회수에 관한 두 사람의 신뢰를 보존한다.성소 실패나 실제 수정 회수·치료·장로생사·장소 길찾기를 실행 검증했다고 확대하지 않는다.화자 말투·운명의 의인화·coven·이름/용어는 인간 의미 검토가 남은 개발 초안이다.
'''

def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));fields=[];records=[]
    for row in [1,4,5,6,7,15]:
        raw=db[336020+row*260:336020+(row+1)*260]
        for word,key in enumerate(struct.unpack('<65I',raw)):fields.append(dict(row=row,word=word,u32=key,complete_row_sha256=digest(raw)))
    for key,(row,word) in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and 'BUG' not in s['source_text'].upper()
        assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==key
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        tag=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tag)==1
        match=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag[0]];assert len(match)==1
        records.append(dict(key=key,source=s,row=row,word=word,all_refs_in_six_rows=[dict(row=f['row'],word=f['word']) for f in fields if f['u32']==key],portrait=tag[0],portrait_WAD=match[0]))
    p=b/'packets/recovery383';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'full_six_rows.jsonl',serialized(fields));protected_write(p/'source_context.jsonl',serialized(records))
    anchors=[s for s in src if s['bank']=='trans' and s['key'] in {2311,2316,2347,2443,3613,2435,2436,2442}]
    protected_write(p/'quest_anchor_sources.jsonl',serialized(anchors));protected_write(p/'REVIEW.md',REVIEW)
    save_json(ROOT/'qa/reports/recovery_stage383_context.json',dict(status='PASS_383_SEVENTEEN_RECOVERY_SOURCE_CONSUMERS',fields=390,keys=list(FIELDS),anchors=len(anchors),source_backed_portraits=17,wording_or_game_changes=0,release_eligible=False))
    print('PASS383 full390 fields/17 exact source slots and portraits')
if __name__=='__main__':main()

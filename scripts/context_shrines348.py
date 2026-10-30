"""Source-exact shrine quest and crystal-return dialogue/Book fields."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2434:[(15,24,40),(15,25,40),(15,26,40),(15,47,40),(15,48,40)],2435:[(15,24,24)],2436:[(14,32,0)],2437:[(15,47,24)],2438:[(15,48,24)],2439:[(15,25,24)],2442:[(15,26,32)],2449:[(15,29,32)],2451:[(15,30,24)],2452:[(13,0,40)],2453:[(13,0,44)],2456:[(13,15,40)]}
DIALOGUE_KEYS=[2436,2442,2449,2452,2453,2456]
BOOK_KEYS=[2434,2435,2437,2438,2439,2451]
TITLES={2434}

REVIEW="""# 성소·수정 반환 후속12개 — 348

원문 table13/14/15의 제목1·일지5·대화6개를 정확한 필드와 전체 행에 연결했다. table15+24 본문/+32 대사/+40 제목은 구분한다.2434는 다섯 일지 단계가 공유하는 제목이며,앞선2441의 원래 제목이다.2440과2423은 이 세 table의 알려진 소비 필드에서 연결되지 않아 이번에 선택하지 않는다. 이것만으로 미사용으로 확정하지 않는다.

2436은 드루이드 성소3개가 수백 년 동안 숲을 지켰으나 고르진 주술사들이 마력을 빼내고 있다는 설명이다.2435의 seeping은 같은 퀘스트2436의 leeching 문맥으로 해석한다.세 적 defiler/reaver/corruptor와 Lightfall Grove/Shadowpine/Tornwood Forest를 혼동하지 않는다.허락을 먼저 받아야 한다는 일지와 장로가 이미 허락을 받아 두었다는 대사의 시점 차이를 임의로 수정하지 않는다.

2442의 공존해 온 기간과 새 적의 등장,Unataca의 주민들이 광기에 빠지는 상황은 화자의 판단과 우려다.원인을 이 단계에서 확정하지 않는다.고대문서와현재사태의유사성및coven이축복한보상이라는단서도보존한다.축복은대사내용이며실제획득/아이템효과런타임검증과는별개다.

2449는 반환 약속 이행과 아벤 사람들의 멸시,우리 중 한 사람을 넘겨준 지200년,도시의 목적/사명,고르진 부족 사이의 어두운 조짐을 말한다.그 한 사람이 누구인지는 원문에 없으므로 밝히지 않는다.2450의 미확정 질문에 대한 맥락이며 기존2450 문구는 바꾸지 않는다.구름 속 도시라는 표현의 구체 지형이나 비행 구조를 덧붙이지 않는다.

2451은 노파가 실제 약속을 지켜 돌려준 뒤의 일지이고,제때 전달할 수 있기를 바라는 상태다.2456은 크라운 선출 이후의 꿈과공격이전의꿈질문,아무에게도말하지않음/주인공에게만말함,예감인지궁금해하는불확실성을유지한다.잠깐말을끊는Never mind를삭제하지않는다.

인명/지명·고르진 세 적의 표기·드루이드 모임의 coven 번역은 개발 초안이며 인간 승인이 없다.작업 범위는 원문 연결·개별 번역·재삽입과 필요한 화면 검증이다.자연 사건·완주·저장·배포 검증으로 올리지 않는다.
"""

def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};ss={s['key']:s for s in lines(b/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];rows={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and 'BUG' not in s['source_text'].upper()
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256'];out=[]
        for table,row,field in refs:
            off,count=struct.unpack_from('<II',db,table*8);stride={13:260,14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride]
            assert row<count and struct.unpack_from('<I',r,field)[0]==key
            assert (table==13 and field in [40,44]) or (table==14 and field==0) or (table==15 and field==(32 if key in DIALOGUE_KEYS else 40 if key in TITLES else 24))
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r)))
            rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        matches=[]
        if key in DIALOGUE_KEYS:
            tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tags)==1
            matches=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(matches)==1
        else:assert not any(c in s['source_text'] for c in '[]\r\n')
        records.append(dict(key=key,source=s,references=out,portrait_WAD_matches=matches,kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key in TITLES else 'Book_body'))
    p=b/'packets/shrines348';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'source_context.jsonl',serialized(records));protected_write(p/'full_consumer_rows.jsonl',serialized(list(rows.values())))
    protected_write(p/'REVIEW.md',REVIEW)
    save_json(ROOT/'qa/reports/shrines_stage348_context.json',dict(status='PASS_348_TWELVE_EXACT_SHRINE_CRYSTAL_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=6,wording_or_game_changes=0,release_eligible=False))
    print('PASS348 exact12 consumers/six portraits/six Book keys')
if __name__=='__main__':main()

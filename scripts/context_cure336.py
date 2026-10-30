"""Source-exact dialogue/Book fields for the illness and crystal quest arc."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2343:[(15,23,40),(15,49,40)],2344:[(15,49,24)],2345:[(15,23,24)],2347:[(14,44,0)],2395:[(13,17,32)],2396:[(13,17,152)],2441:[(15,26,24)],2443:[(14,33,0)],2444:[(15,27,40),(15,28,40),(15,29,40),(15,30,40)],2445:[(15,27,24)],2446:[(15,27,32)],2447:[(15,28,24)],2448:[(15,29,24)],2450:[(15,30,32)],2482:[(14,36,0)]}
DIALOGUE_KEYS=[2347,2395,2396,2443,2446,2450,2482]
BOOK_KEYS=[2343,2344,2345,2441,2444,2445,2447,2448]
TITLES={2343,2444}
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
            assert (table==13 and field in [32,152]) or (table==14 and field==0) or (table==15 and field==(32 if key in DIALOGUE_KEYS else 40 if key in TITLES else 24))
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r)))
            rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        matches=[]
        if key in DIALOGUE_KEYS:
            tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tags)==1
            matches=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(matches)==1
        else:assert not any(c in s['source_text'] for c in '[]\r\n')
        records.append(dict(key=key,source=s,references=out,portrait_WAD_matches=matches,kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key in TITLES else 'Book_body'))
    p=b/'packets/cure336';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'source_context.jsonl',serialized(records));protected_write(p/'full_consumer_rows.jsonl',serialized(list(rows.values())))
    protected_write(p/'REVIEW.md','''# 질병 본퀘스트·증류 수정15개 — 336

목표2개·일지6개·대화7개를 원본table13/14/15의 정확한 소비 필드와 연결했다. table15+32는 퀘스트 대사이며+24 일지나+40 제목으로 취급하지 않는다. 원본 전체 행을 보존하고 배열 순서를 실제 플레이 경과로 단정하지 않는다.2350 등 앞선 일반 대사의 의미 검토를 완료한 것으로 처리하지 않는다.

2347은 여관에서 쓰러뜨린 것과 비슷한 어두운 프레이톡스에게 물린 뒤의 전언이다. source Howling Pine은 승인된 울부짖는 소나무 여관으로 쓴다. 죽음보다 사악한 결과라는 우려는 원문 수준으로 남긴다.2344의 도서관 폐허·망령은 소문,2345의 둥지가 없다는 판단과 저주받았다는 독백을 구분한다.

2443은 혈청이 도움이 되었으나 완치하지 못했고,리세타는 쇠약해지며 케일리는 자기 상태가 나아지는 것 같다고 생각하는 상황이다. 드레이븐의 와일들링에 대한 태도와 보복을 원하지 않는 케일리의 입장을 지우지 않는다. 적과 공모했다는 것은 가정이지 확정 사실이 아니다.

2446의 고대 역할·혈연·유일한 상속자라는 단서는 보존한다. 손녀 구출이 수정 반환의 조건이며 수정은 아직 노파에게 있고 고르진은 받지 못했다.2447은 잡아먹겠다는 협박,2448은 구출 뒤 반환 약속을 믿고 기다리는 심경이다.2450의 what wildling was given to us는 누구/무엇인지 이 자료만으로 좁히지 않는다. 그 모호한 대상과 도시의 목적에 대한 질문은 그대로 남긴다.

2482의 two centuries ago는200년 전이며 프롤로그의2000년과 합치지 않는다. Aldus와Aidas는 서로 다른 사람이다. 회수한 책의 표기·와일들링·고르진·그림자소나무/셰도파인·황량한 광산/블리크 광산은 정식 승인 없이 새 표기를 확정하지 않는다. 기존 개별 초안과 명칭 대조 후 수동 작성한다. 전 항목 인간 의미 검토 대기이며 완주·자연퀘스트·저장 검증은 별도다.
''')
    save_json(ROOT/'qa/reports/cure_stage336_context.json',dict(status='PASS_336_FIFTEEN_EXACT_CURE_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=7,wording_or_game_changes=0,release_eligible=False))
    print('PASS336 exact15 consumers/seven portraits/eight Book keys')
if __name__=='__main__':main()

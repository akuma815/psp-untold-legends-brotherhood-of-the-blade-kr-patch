"""Repair Gates five exact typed consumers;no source-order narrative assumption."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
FIELDS={2520:[(15,5,40),(15,6,40)],2521:[(15,5,24)],2522:[(14,17,0)],2524:[(15,6,24)],2525:[(15,6,32)]}
DIALOGUE_KEYS=[2522,2525]
BOOK_KEYS=[2520,2521,2524]
TITLES={2520}

def main():
    b=ROOT/'workspace/translation';assert (b/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_454_checkpoint/entries.jsonl').read_bytes()
    src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'};es={e['id']:e for e in lines(b/'entries.jsonl')}
    ds={d['id']:d for p in [b/'diagnostic_decisions.jsonl',*b.glob('decisions_*.jsonl')] for d in lines(p)}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];rows={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated'
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key in TITLES else 'Book_body';out=[]
        for table,row,field in refs:
            off,n=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride]
            assert row<n and struct.unpack_from('<I',r,field)[0]==key
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r),mode=1 if table==14 else {24:4,32:6,40:8}[field]))
            rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);portraits=[]
        if kind=='dialogue':
            assert tags==['PI_DeanLysetta'];portraits=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(portraits)==1
        else:assert not tags and not any(c in s['source_text'] for c in '[]\r\n')
        assert '[p]' not in s['source_text']
        records.append(dict(key=key,source=s,kind=kind,references=out,portrait_WAD_matches=portraits))
    off,_=struct.unpack_from('<II',db,14*8);r=db[off+17*44:off+18*44];assert [x for x in struct.unpack_from('<6h',r,18) if x>=0]==[5,6]
    anchors=[]
    for s in src:
        if not any(x in s['source_text'].casefold() for x in ['shattercove','splinterfull','dreadwind','waning waste','whispering chasm','alyssia','containment shard','tornwood','overseer lysetta']):continue
        e=es[s['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision')
        anchors.append(dict(source=s,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
    dest=b/'packets/gates460';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'source_context.jsonl',serialized(records));protected_write(dest/'full_consumer_rows.jsonl',serialized(list(rows.values())));protected_write(dest/'anchors.jsonl',serialized(anchors))
    protected_write(dest/'REVIEW.md','''# 관문 수리 — 원문 연결460

table14행17의 시작대사2522는 signed subquest5/6을 가리킨다.table15행5/6의 제목2520,본문2521/2524,완료대사2525를 전체3행과 함께 연결했다.5키 중 대사2·Book제목1/본문2이며 event field36 문구는 없다.

원문2521의 경로는 톤우드 숲→섀터코브 서부/동부→스플린터풀 숲→드레드윈드 황야→쇠락의 황무지→속삭이는 심연이다.최종 장소에서 세이렌 증오의 알리시아가 가진 봉인 조각을 얻는 것으로,새로운 이동 방법이나 처치 조건을 만들지 않는다.시작대사2522는 장치가 세이렌을 적으로부터 보호했고 알리시아를 수백 년 잠들게 했다는 두 설명을 함께 유지한다.현재 임무는 조각 회수이며 관문 보호 조율은 감독관과 시종들이 맡는다.2524는 방어 성공 확정이 아닌 제때 조율되길 바라는 생각,2525는 즉시 작업 시작과 드레이븐에게 긴급 복귀 지시다.

8개 관련 static 명칭은 문맥 앵커로만 수집하며 이번5키에 몰래 포함하지 않는다.새 지명·세이렌/알리시아·봉인 조각은 개발 후보다.톤우드 숲/브룰토크/매로록/리세타 감독관/성전기사 드레이븐/수호자는 기존 원고와 대조한다.초상화 태그·CRLF문단 순서 유지,없는[p] 추가 금지.자연 회수·조율·관문 방어 효과·보상은 별도 미검증이다.
''')
    save_json(ROOT/'qa/reports/gates_stage460_context.json',dict(status='PASS_460_FIVE_TYPED_REPAIR_GATE_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=2,wording_or_game_changes=0,release_eligible=False))
    print('PASS460 exact5 consumers/3 complete rows')

if __name__=='__main__':main()

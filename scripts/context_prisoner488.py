"""Eight exact portrait/Book consumers for Rescue Prisoner;entry thought kept separate."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
FIELDS={2526:[(15,7,40),(15,8,40),(15,9,40)],2528:[(15,7,32)],2530:[(15,7,24)],2538:[(15,9,32)],2539:[(15,9,24)],2549:[(14,18,0)],3019:[(15,8,32)],3759:[(15,8,24)]}
DIALOGUE_KEYS=[2549,2528,3019,2538]
BOOK_KEYS=[2526,2530,3759,2539]
TITLES={2526}
PORTRAITS={2549:'PI_Draven',2528:'PI_KayleeSickly',3019:'PI_KayleeSickly',2538:'PI_DeanLysetta'}

def main():
    b=ROOT/'workspace/translation';assert (b/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_486_checkpoint/entries.jsonl').read_bytes()
    src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'};es={e['id']:e for e in lines(b/'entries.jsonl')}
    ds={d['id']:d for p in [b/'diagnostic_decisions.jsonl',*b.glob('decisions_*.jsonl')] for d in lines(p)}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];rows={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated'
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key in TITLES else 'Book_body';out=[]
        for table,row,field in refs:
            off,n=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride]
            assert row<n and struct.unpack_from('<I',r,field)[0]==key
            assert (table==14 and field==0 and kind=='dialogue') or (table==15 and field==dict(dialogue=32,title=40,Book_body=24)[kind])
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r),mode=1 if table==14 else {24:4,32:6,40:8}[field]));rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);portraits=[]
        if kind=='dialogue':
            assert tags==[PORTRAITS[key]];portraits=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(portraits)==1
        else:assert not tags and not any(c in s['source_text'] for c in '[]\r\n')
        assert s['source_text'].count('[p]')==(5 if key==2528 else 0)
        records.append(dict(key=key,source=s,kind=kind,references=out,portrait_WAD_matches=portraits))
    off,_=struct.unpack_from('<II',db,14*8);r=db[off+18*44:off+19*44];assert [x for x in struct.unpack_from('<6h',r,18) if x>=0]==[7,8,9] and struct.unpack_from('<I',r,8)[0]==3578
    # Preserve entry-thought3578 as a different typed consumer,not an image dialogue or Book body.
    extra=dict(key=3578,source=ss[3578],table=14,row=18,field=8,mode=3,disposition='Source/context only;not in eight-key draft/build cohort;separate mode3 dispatch investigation remains.')
    queries=['kaylee','screeching halls','dreadwind','splinterfull','aldus','[i_pi_deanlysetta]','[i_pi_draven]'];anchors=[]
    for s in src:
        if not any(x in s['source_text'].casefold() for x in queries):continue
        e=es[s['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision');anchors.append(dict(source=s,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
    nearby=[]
    for key in [2527,2532]:
        refs=[]
        for table,stride,fields in [(14,44,[0,4,8]),(15,56,[24,32,36,40])]:
            o,n=struct.unpack_from('<II',db,table*8)
            refs.extend(dict(table=table,row=i,field=f) for i in range(n) for f in fields if struct.unpack_from('<I',db,o+i*stride+f)[0]==key)
        nearby.append(dict(key=key,source=ss[key],typed_fields_scanned_matches=refs,not_unused_proof=True,not_in_cohort=True))
    dest=b/'packets/prisoner488';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'source_context.jsonl',serialized(records));protected_write(dest/'full_consumer_rows.jsonl',serialized(list(rows.values())));protected_write(dest/'anchors.jsonl',serialized(anchors));protected_write(dest/'separate_consumers.json',json.dumps(dict(entry_thought=extra,nearby=nearby),ensure_ascii=False,indent=2)+'\n')
    protected_write(dest/'REVIEW.md','''# 포로 구출 — 원문 연결488

원본table14행18의 시작대사2549와 signed subquest7/8/9를 연결했다.table15행7/8/9의 제목2526,Book본문2530/3759/2539,대사2528/3019/2538을 전체4행으로 보존했다.총8키는 초상화대사4·Book제목1/본문3이다.별도 table14행18field8의entry-thought3578은mode3이므로 이8키에 숨겨 넣지 않고 소비 조사 대상으로 남겼다.이웃한2527과다중이미지2532도 저장순서만으로 같은 경로에 합치지 않는다.좁은 필드 검색의 음성 결과는 미사용 증거가 아니다.

2549에서 크라운 케일리는 부상병을 돕고자 누구에게도 알리지 않고 전선 의료시설로 떠났고,도착 몇 시간 안에 브룰토크에게 납치된다.습격 생존자들의 납치/사령술사 저주,성전기사의 안전귀환 최우선 태도를 보존한다.2530의 위치는 스플린터풀 숲 너머 드레드윈드 황야의 비명의 전당이다.기존지명과원문경로를맞춘다.

2528은 케일리가 일지를 반드시 감독관에게 전달하라고 부탁하고,부상병을 도우러 간 선택과 위험을 자신의 의지로 감수했음을 말한다.수호자의 직책을 존중하지 않은 사과와 과거 잘못에도 흔들리지 않은 헌신에 대한 감사를 함께 유지한다.기존케일리2375–2378/2443/2450/2456/3614/3615의친숙한반말과약한말투를대조한다.원래[i_PI_KayleeSickly]와[p]5개/CRLF순서를보존하며새강제페이지를추가하지않는다.

3759는 일지를 받았어도 여전히 구출이 필요한 상태다.3019는 케일리가 너무 쇠약해 함께 돌아갈 수 없다며 아카데미 복귀를 말한다.이 문구를 새 호위/이동 조작 지시나 건강 회복 확정으로 바꾸지 않는다.2539는 케일리가 아벤으로 떠나기 전에 받은 알두스 일지를 감독관에게 조사시키려는 상태다.

2538은 리세타가 케일리의 고집·선의·무모한 방법을 구분하고,현재 몸은 안전하지만 마음과 앞으로의 운명은 걱정된다고 말한다.병명·죽음·치유 확정을 만들지 않는다.기존 리세타 하게체/자네·크라운·알두스·아벤·수호자를 개별 대조한다.새 비명의 전당 명칭과 모든 문구는 인간 미승인 개발 후보이며 실제 구출·일지획득·아카데미 복귀·퀘스트 완료·savedata 증거는 별도다.
''')
    save_json(ROOT/'qa/reports/prisoner_stage488_context.json',dict(status='PASS_488_EIGHT_TYPED_PRISONER_QUEST_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=4,source_p_tokens={2528:5},forced_page_break_claim=False,separate_entry_thought3578_unselected=True,wording_or_game_changes=0,release_eligible=False))
    print('PASS488 exact8 consumers/4 complete rows;mode3 thought3578 separate')

if __name__=='__main__':main()

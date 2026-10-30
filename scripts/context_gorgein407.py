"""Twentyone exact quest consumers;mode7 event text is distinct from Book/dialogue."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2463:[(15,31,40),(15,32,40),(15,33,40)],2464:[(15,31,24)],2465:[(14,34,0)],2466:[(15,32,24)],2467:[(15,32,36)],2468:[(15,31,36)],2469:[(15,33,24)],2470:[(15,33,32)],2471:[(15,34,40),(15,35,40)],2472:[(15,34,24)],2473:[(15,34,32)],2474:[(15,35,24)],2475:[(15,35,32)],2476:[(14,35,0)],2477:[(15,36,40),(15,37,40),(15,38,40)],2478:[(15,36,24)],2479:[(15,36,32)],2480:[(15,37,24)],2481:[(15,37,36)],2483:[(15,38,32)],2484:[(15,38,24)]}
DIALOGUE_KEYS=[2465,2470,2473,2475,2476,2479,2483]
EVENT_KEYS=[2467,2468,2481]
BOOK_KEYS=[2463,2464,2466,2469,2471,2472,2474,2477,2478,2480,2484]
TITLES={2463,2471,2477}
REVIEW='''# 고르진 분쟁·4인의 도구 본퀘스트21개 — 407

제목3·일지8·인물대사7·초상화없는이벤트서술3을원본table14/15의정확한필드와전체행에연결했다.기존2482는이미선택된문구로남기고바꾸지않는다.table15+24는Book본문,+32는mode6인물대사,+36은mode7이벤트문자열,+40은Book제목이다.이벤트3개를Book본문이나NPC대사로잘못분류하지않는다.265의원본4E7F4~4E838은field24(hex)/cache5C를선택해공통6F5D4/706FC/BDCB0으로적재한다.이정적연결이자연사건실행증거는아니다.

2465의다이애나는왈로핏전사매로터스크를죽인뒤스나우트롯족장크렐가크를죽이고증거를심어두부족의충돌을유발하라는계획을설명한다.2468은첫전사의부서진무기를챙긴후이고2467은다른족장의시신옆에놓은후다.서로다른행동/시점과가짜증거라는정보를보존한다.이미소유한무기를새로생성했다거나서로다른부족의지도자를혼동하지않는다.

2464는왈로핏최상층의매로터스크,2472는가장깊은곳의여족장스컬크그라를구분한다.2473은인간을먹겠다는고르진화자의위협이며,2474의사망은명시된완료일지다.2475의안전과새위협의심도구분하고아이템보상대사를실제보상효과검증으로확대하지않는다.초상화태그PI_MatronSkulgra는WAD에그대로존재하며원문본문/이름Skulkgra와철자차이가있어도태그를자동수정하지않는다.

2479는리세타가치료법을찾는동안예언을연구하며4개유물중하나의회수를부탁하는단계다.동료드루이드들이감히성역에들어가지못함과필요이상으로성지를훼손하지말라는부탁을보존한다.2480의드루이드화환과2483의영속의화환은같은회수문맥에서쓰인서로다른원문호칭으로유지한다.2481은이슬·향기·덩굴의묘사와손상/적의탈취전에돌아가려는긴급성을보존한다.2483은형제단이선의와힘을지녔다는장로의판단,남은3유물·연구시간·성급한출발의위험·드레이븐의다음부름을포함한다.

고르진/왈로핏/스나우트롯/매로터스크/크렐가크/스컬크그라,성스러운묘실/썩어가는사제/드루이드화환/영속의화환/검의형제단/4인의도구등의표기는개발초안이다.형제단의정체·예언해석·유물효과·플레이어행동을인간의미승인이나자연퀘스트검증으로표시하지않는다.[p]와원문CRLF/초상화순서는보존하며강제페이지분할은주장하지않는다.
'''

def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    prior=json.loads((ROOT/'qa/reports/quest_stage265_static.json').read_text(encoding='utf8'));assert prior['modes']['7']==dict(table=15,field=36,cache=92)
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];rows={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and not re.search(r'\*BUG(?: THIS| ME)?\*',s['source_text'].upper())
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256'];out=[]
        kind='dialogue' if key in DIALOGUE_KEYS else 'event_text' if key in EVENT_KEYS else 'title' if key in TITLES else 'Book_body'
        for table,row,field in refs:
            off,count=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride]
            assert row<count and struct.unpack_from('<I',r,field)[0]==key
            assert (table==14 and field==0 and kind=='dialogue') or (table==15 and field==dict(dialogue=32,event_text=36,title=40,Book_body=24)[kind])
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r),mode=1 if table==14 else {24:4,32:6,36:7,40:8}[field]))
            rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        matches=[];tags=re.findall(r'\[i_([^\]]+)\]',s['source_text'])
        if kind=='dialogue':
            assert len(tags)==1
            matches=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(matches)==1
        else:assert not tags
        if kind in ['title','Book_body']:assert not any(c in s['source_text'] for c in '[]\r\n')
        records.append(dict(key=key,source=s,references=out,portrait_WAD_matches=matches,kind=kind))
    p=b/'packets/gorgein407';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'source_context.jsonl',serialized(records));protected_write(p/'full_consumer_rows.jsonl',serialized(list(rows.values())))
    anchors=[s for s in src if (s['bank']=='trans' and s['key'] in {2482,2490,2491,2492,2437,2438,2439}) or (s['bank']=='static' and s['key'] in {2263,3001,54,55,56,59,63,64,65,766,776})]
    protected_write(p/'name_and_quest_anchors.jsonl',serialized(anchors));protected_write(p/'REVIEW.md',REVIEW)
    save_json(ROOT/'qa/reports/gorgein_stage407_context.json',dict(status='PASS_407_TWENTYONE_TYPED_GORGEIN_PROPHECY_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,events=EVENT_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=7,mode7_window_sha256=digest(boot[128+0x4e7f4:128+0x4e83c]),wording_or_game_changes=0,release_eligible=False))
    print('PASS407 exact21 typed consumers;7 portrait dialogues/3 events/11 Book keys')
if __name__=='__main__':main()

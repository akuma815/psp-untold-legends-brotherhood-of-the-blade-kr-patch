"""Twelve exact consumers for the first two vrultok border-defense quests."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
FIELDS={2508:[(15,0,40),(15,1,40),(15,2,40)],2509:[(15,0,24)],2510:[(15,0,32)],2511:[(14,15,0)],2512:[(15,1,24)],2513:[(15,2,24)],2514:[(15,2,32)],2515:[(15,3,40),(15,4,40)],2516:[(15,3,24)],2517:[(14,16,0)],2518:[(15,4,24)],2519:[(15,4,32)]}
DIALOGUE_KEYS=[2510,2511,2514,2517,2519]
BOOK_KEYS=[2508,2509,2512,2513,2515,2516,2518]
TITLES={2508,2515}

def main():
    b=ROOT/'workspace/translation';assert (b/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_441_checkpoint/entries.jsonl').read_bytes()
    src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'};es={e['id']:e for e in lines(b/'entries.jsonl')}
    ds={d['id']:d for p in [b/'diagnostic_decisions.jsonl',*sorted(b.glob('decisions_*.jsonl'))] for d in lines(p)}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];complete={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and not re.search(r'\*BUG(?: THIS| ME)?\*',s['source_text'].upper())
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key in TITLES else 'Book_body';out=[]
        for table,row,field in refs:
            off,n=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride]
            assert row<n and struct.unpack_from('<I',r,field)[0]==key
            assert (table==14 and field==0 and kind=='dialogue') or (table==15 and field==dict(dialogue=32,title=40,Book_body=24)[kind])
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r),mode=1 if table==14 else {24:4,32:6,40:8}[field]))
            complete[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);portraits=[]
        if kind=='dialogue':
            assert len(tags)==1;portraits=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(portraits)==1
        else:assert not tags and not any(c in s['source_text'] for c in '[]\r\n')
        assert '[p]' not in s['source_text']
        records.append(dict(key=key,source=s,kind=kind,references=out,portrait_WAD_matches=portraits))
    # Exact subquest references,not an assumption that text storage order is narrative order.
    for table14_row,wanted in [(15,[0,1,2]),(16,[3,4])]:
        off,n=struct.unpack_from('<II',db,14*8);r=db[off+table14_row*44:off+(table14_row+1)*44]
        # Six signed references end before field1E (300),which is not a subquest index.
        refs=[x for x in struct.unpack_from('<6h',r,0x12) if x>=0];assert refs==wanted
    queries=['vrultok','Marrowrock','Deadeye','Ironstone','Shaelunn','Templar'];anchors=[]
    for s in src:
        if not any(q.casefold() in s['source_text'].casefold() for q in queries):continue
        e=es[s['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision')
        anchors.append(dict(source=s,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
    dest=b/'packets/vrultok443';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'source_context.jsonl',serialized(records));protected_write(dest/'full_consumer_rows.jsonl',serialized(list(complete.values())));protected_write(dest/'name_and_role_anchors.jsonl',serialized(anchors))
    protected_write(dest/'REVIEW.md','''# 브룰토크 침공 초기 두 퀘스트12개 — 443

원본table14행15의시작대사2511→table15행0/1/2(제목2508·본문2509/2512/2513·대사2510/2514),table14행16의시작대사2517→table15행3/4(제목2515·본문2516/2518·대사2519)를정확한전체7행으로연결했다.인물대사5·Book제목2/본문5의12키이며이번묶음에event36문자열은없다.서로다른제목본문이나NPC/Book경로를혼동하지않는다.

2511은고르진격퇴뒤새적의침공에맞서성전기사가기사들을외곽으로보낼수없는이유와다이애나의정보를안내한다.2510은관문을공격하는장군을막으라는지시와안전한구덩이통과물건을준다.2512에서그물건이밧줄이며라이트폴숲의매로록북부구덩이→매로록남부→데드아이능선경로임이명시된다.지시대사에원문없는행동단계·새장비효과를추가하지않는다.2513의장군사망과더큰적위협,2514의과거정찰병손실/예상밖공격/고르진격퇴직후라는의심과보상대사를보존한다.

2517/2516은이미완성된성채를공성하는것이아니라데드아이능선동굴의아이언스톤공동건설현장장군을죽여건설을중단시키는임무다.2518의건설중단·현장병력제거는완료상태이나적의재개는시간문제라는긴급성을유지한다.2519의셰일룬몰대장장이선물은물건종류를임의확정하지않고다음리세타감독관임무로연결한다.자연퀘스트완료·보상실제효과증거는별도다.

브룰토크/매로록/데드아이능선/아이언스톤공동/셰일룬몰/야생의영혼은신규개발후보이며인간명칭·발음·신앙해석은미승인이다.성전기사·다이애나부인·리세타감독관·아벤·라이트폴숲·수호자는기존문맥원고와대조한다.원문초상화태그와CRLF문단순서는유지한다.[p]없는대사이며강제페이지구분을추가하지않는다.2500의player cannot refuse문구나별도장면2505를이12키에자동포함하지않는다.
''')
    save_json(ROOT/'qa/reports/vrultok_stage443_context.json',dict(status='PASS_443_TWELVE_TYPED_BORDER_QUEST_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(complete),source_portraits=5,table14_subquest_rows={15:[0,1,2],16:[3,4]},wording_or_game_changes=0,release_eligible=False))
    print('PASS443 exact12 consumers/7 complete rows/5 dialogue/7 Book keys')
if __name__=='__main__':main()

"""Seventeen source-connected transition reminders; preserve full seven NPC rows."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2485:(0,12),2486:(0,13),2487:(0,14),2497:(3,12),2498:(3,13),2503:(3,14),2506:(4,12),2507:(4,13),2488:(14,12),2489:(14,13),2490:(15,12),2491:(15,13),2492:(15,14),2493:(16,12),2494:(16,14),2495:(17,13),2496:(17,14)}
REVIEW='''# 고르진 분쟁·예언 조사 전환17개 — 395

table13 row0/3/4/14/15/16/17 전체455필드와17개 원문/정확한슬롯/초상화WAD를 연결한다.부족충돌유발·족장/족모제거·예언유물조사의실제지시2463~2484도원문으로보존해전환안내가어느사건에관한것인지구분한다.슬롯12/13/14는원문소비참조이며실제quest phase의수치로임의확정하지않는다.

윌2485의전쟁은술자리에서과장된소문일수있다는화자의유보를유지한다.2486은플레이어가부족간유혈충돌을부추겼다는반응이며,현재분쟁이자연적으로일어났다고바꾸지않는다.2487은예언과옛유물에관해감독관을찾으라는조언이다.아이다스2507은내부봉기에플레이어가관여했다는소식을듣고후속이더있으리라추정한다.

아르몬의부름에응하라는말은실제성문출입제한코드검증과별개다.리세타/드레이븐/다이애나의대사는다음도움을청하는화자와의뢰인을구분한다.다이애나2496은정찰병을연구에보내고싶어도지금은여유가없다는뜻이다.

케일리2490은플레이어의검/자신의갑옷비유와무력감을함께보존한다.2491은상호이해에대한감사·내전으로약해져도다시도시를향할분노를구분한다.2492의꿈에는넷,때로는여섯빛나는형상이돌고그중둘이손을맞잡는다.보호받는다고느끼다가경비병들이안쪽을향해자신으로부터세상을지킨다는악몽으로바뀌는반전이다.인물의정체·확정예언해석·연애관계·진단·미래사망을추가하지않는다.원문[p]/CRLF의순서를보존하되강제페이지분할기능을주장하지않는다.

고르진/부족명·acolytes·Overseer/Templar지위·화자말투는개발초안이며인간승인대상이남아있다.이번묶음표시검증을실제전쟁진행·분쟁유발·예언성취·유물회수·저장·완주증거로확대하지않는다.
'''

def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));fields=[];records=[]
    for row in [0,3,4,14,15,16,17]:
        raw=db[336020+row*260:336020+(row+1)*260]
        for word,key in enumerate(struct.unpack('<65I',raw)):fields.append(dict(row=row,word=word,u32=key,complete_row_sha256=digest(raw)))
    for key,(row,word) in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and 'BUG' not in s['source_text'].upper()
        assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==key
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        tag=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tag)==1
        match=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag[0]];assert len(match)==1
        records.append(dict(key=key,source=s,row=row,word=word,all_refs_in_seven_rows=[dict(row=f['row'],word=f['word']) for f in fields if f['u32']==key],portrait=tag[0],portrait_WAD=match[0]))
    p=b/'packets/transition395';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'full_seven_rows.jsonl',serialized(fields));protected_write(p/'source_context.jsonl',serialized(records))
    anchors=[s for s in src if s['bank']=='trans' and 2463<=s['key']<=2484]
    for s in anchors:
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    protected_write(p/'quest_anchor_sources.jsonl',serialized(anchors));protected_write(p/'REVIEW.md',REVIEW)
    save_json(ROOT/'qa/reports/transition_stage395_context.json',dict(status='PASS_395_SEVENTEEN_TRANSITION_SOURCE_CONSUMERS',fields=455,keys=list(FIELDS),anchors=len(anchors),source_backed_portraits=17,wording_or_game_changes=0,release_eligible=False))
    print('PASS395 full455 fields/17 exact source slots and portraits/22 quest anchors')
if __name__=='__main__':main()

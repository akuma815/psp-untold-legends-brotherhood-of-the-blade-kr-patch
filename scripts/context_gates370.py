"""Thirtyone exact gate/security consumers and immutable quest context."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
FIELDS={2399:(3,1),2400:(3,2),2401:(3,3),2402:(3,7),2403:(3,37),2404:(3,8),2405:(3,38),2406:(3,9),2407:(3,39),2461:(3,10),2462:(3,11),2379:(16,1),2380:(16,2),2381:(16,3),2383:(16,7),2384:(16,37),2385:(16,8),2386:(16,38),2387:(16,9),2388:(16,39),2457:(16,10),2458:(16,11),2389:(17,1),2390:(17,2),2391:(17,3),2392:(17,4),2393:(17,7),2397:(17,9),2398:(17,39),2459:(17,10),2460:(17,11)}
ANCHORS={2435,2436,2443,2449,2455,2456}
REVIEW="""# 성문·치안 대사31개 — 370

table13 row3/16/17 전체195필드와31개 원문 key의 정확한 위치를 보존했다. 일반 selector1~4뿐 아니라word7~11·37~39의 조건별 참조도 포함하며,그 번호를 실제 quest 단계나 허가flag의 의미로 임의 확정하지 않는다.같은2393은row17 word7/37의 동일key이고,2383/2384는같은원문을가진서로다른key이므로둘다보존한다.

아르몬의 아직허가없음/크라운위험/케일리귀환/독둥지추적/성소출발/도난중이탈에대한대사를구분한다.허가거부대사가실제로출입을막는코드조건이라는런타임증거와텍스트표시검증은별개다.2497등더후기의지시는이번묶음에서제외한다.

드레이븐의권위적말투·멸시·추방자/성밖사람들에대한편견을지우거나서술자의객관적사실로바꾸지않는다.2388은구하면존중/실패하면분노라는조건부경고다.2387의아직치료법을만들기전이라는시점과다른회복후대사를임의로합치지않는다.

다이애나는드레이븐의편견과성문봉쇄를비판하며,밖에도문명화된사람들이있다고말한다.2392의낯선이를피하지만지켜보고있다는정보를유지한다.2393의공격출처는화자의추측,2397의전문성은말을잠깐멈추는표현을유지한다.2398의백배강함은화자의경고이지실제능력치배율을검증한것이아니다.그림자에서빠르게공격후물러남·정찰자매들의상실을보존한다.

2457~2462는장로요청과도난직후의도움을촉구하는서로다른NPC지시다.필요한주변문맥2435/2436/2443/2449/2455/2456도원문으로보존한다.종족·지위·도시비유·화자말투는개발초안이며인간승인이없다.자연출입허가·사망/구출·전투수치·완주·저장·배포로표시검증을확대하지않는다.
"""

def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')};source=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in source if s['bank']=='trans'}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));fields=[];records=[]
    for row in [3,16,17]:
        raw=db[336020+row*260:336020+(row+1)*260]
        for word,key in enumerate(struct.unpack('<65I',raw)):fields.append(dict(row=row,word=word,u32=key,complete_row_sha256=digest(raw)))
    for key,(row,word) in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated' and 'BUG' not in s['source_text'].upper()
        assert struct.unpack_from('<I',db,336020+row*260+word*4)[0]==key
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        tag=re.findall(r'\[i_([^\]]+)\]',s['source_text']);assert len(tag)==1
        match=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tag[0]];assert len(match)==1
        refs=[dict(row=f['row'],word=f['word']) for f in fields if f['u32']==key]
        records.append(dict(key=key,source=s,row=row,word=word,all_refs_in_four_rows=refs,portrait=tag[0],portrait_WAD=match[0]))
    p=b/'packets/gates370';p.mkdir(parents=True,exist_ok=True)
    protected_write(p/'full_three_rows.jsonl',serialized(fields));protected_write(p/'source_context.jsonl',serialized(records))
    anchors=[s for s in source if (s['bank']=='trans' and s['key'] in ANCHORS) or (s['bank']=='static' and s['key'] in [38,2262])]
    for s in anchors:
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
        assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
    protected_write(p/'quest_anchor_sources.jsonl',serialized(anchors))
    protected_write(p/'REVIEW.md',REVIEW)
    save_json(ROOT/'qa/reports/gates_stage370_context.json',dict(status='PASS_370_THIRTYONE_GATE_SECURITY_CONSUMERS',fields=195,keys=list(FIELDS),anchors=len(anchors),source_backed_portraits=31,wording_or_game_changes=0,release_eligible=False))
    print('PASS370 full195fields/31 exact source slots and portraits/quest anchors')
if __name__=='__main__':main()

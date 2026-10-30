"""Nine exact typed consumers for Destroy the Threat;mode3 entry is separate."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
FIELDS={2540:[(15,i,40) for i in [10,11,12,13]],2541:[(15,10,24)],2542:[(15,10,32)],2544:[(15,12,24)],2545:[(15,11,24)],2546:[(15,12,32)],2547:[(15,13,24)],2548:[(15,13,32)],2550:[(14,19,0)]}
DIALOGUE_KEYS=[2550,2542,2546,2548]
BOOK_KEYS=[2540,2541,2545,2544,2547]
PORTRAITS={2550:'PI_DeanLysetta',2542:'PI_Draven',2546:'PI_Draven',2548:'PI_DeanLysetta'}

def main():
    b=ROOT/'workspace/translation';assert (b/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_499_checkpoint/entries.jsonl').read_bytes()
    src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'};es={e['id']:e for e in lines(b/'entries.jsonl')}
    ds={d['id']:d for p in [b/'diagnostic_decisions.jsonl',*b.glob('decisions_*.jsonl')] for d in lines(p)}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];rows={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated'
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key==2540 else 'Book_body';out=[]
        for table,row,field in refs:
            off,n=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride];assert row<n and struct.unpack_from('<I',r,field)[0]==key
            assert (table==14 and field==0 and kind=='dialogue') or (table==15 and field==dict(dialogue=32,title=40,Book_body=24)[kind])
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r),mode=1 if table==14 else {24:4,32:6,40:8}[field]));rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);portraits=[]
        if kind=='dialogue':
            assert tags==[PORTRAITS[key]];portraits=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(portraits)==1
        else:assert not tags and not any(c in s['source_text'] for c in '[]')
        if key==2540:assert '\r' not in s['source_text'] and '\n' not in s['source_text']
        records.append(dict(key=key,source=s,kind=kind,references=out,portrait_WAD_matches=portraits))
    off,_=struct.unpack_from('<II',db,112);r=db[off+19*44:off+20*44];assert [j for j in struct.unpack_from('<6h',r,18) if j>=0]==[10,11,12,13] and struct.unpack_from('<I',r,8)[0]==3579
    queries=['nethereye','deadeye','necrosis','necromanc','[i_pi_deanlysetta]','[i_pi_draven]'];anchors=[]
    for s in src:
        if not any(x in s['source_text'].casefold() for x in queries):continue
        e=es[s['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision');anchors.append(dict(source=s,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
    dest=b/'packets/threat504';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'source_context.jsonl',serialized(records));protected_write(dest/'full_consumer_rows.jsonl',serialized(list(rows.values())));protected_write(dest/'anchors.jsonl',serialized(anchors))
    protected_write(dest/'separate_consumers.json',json.dumps(dict(entry_thought=dict(key=3579,source=ss[3579],table=14,row=19,field=8,mode=3,not_in_cohort=True),unresolved_prior=[3578,2527,2532,2276,2290,2312]),ensure_ascii=False,indent=2)+'\n')
    save_json(ROOT/'qa/reports/threat_stage504_context.json',dict(status='PASS_504_NINE_TYPED_THREAT_QUEST_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=4,separate_entry_thought3579_unselected=True,wording_or_game_changes=0,release_eligible=False))
    print('PASS504 exact9 consumers/5 complete rows;mode3 thought3579 separate')

if __name__=='__main__':main()

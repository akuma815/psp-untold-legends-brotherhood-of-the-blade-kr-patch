"""Five exact typed consumers for Recover the Second;mode3 entry is separate."""
import json,struct,re
from survey import ROOT,digest,save_json
from catalog_survey034 import lines,serialized,protected_write
from audit_translation138 import resolve
FIELDS={2560:[(15,i,40) for i in [14,15]],2561:[(14,20,0)],2562:[(15,14,24)],2564:[(15,15,24)],2565:[(15,15,32)]}
DIALOGUE_KEYS=[2561,2565]
BOOK_KEYS=[2560,2562,2564]
PORTRAITS={2561:'PI_DeanLysetta',2565:'PI_DeanLysetta'}

def main():
    b=ROOT/'workspace/translation';assert (b/'entries.jsonl').read_bytes()==(ROOT/'qa/ssot/20261019_528_checkpoint/entries.jsonl').read_bytes()
    src=lines(b/'baseline/source_entries.jsonl');ss={s['key']:s for s in src if s['bank']=='trans'};es={e['id']:e for e in lines(b/'entries.jsonl')}
    ds={d['id']:d for p in [b/'diagnostic_decisions.jsonl',*b.glob('decisions_*.jsonl')] for d in lines(p)}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    wad=json.loads((ROOT/'workspace/analysis/wad_index_candidates.json').read_text(encoding='utf8'));records=[];rows={}
    for key,refs in FIELDS.items():
        s=ss[key];assert es[s['id']]['state']=='untranslated'
        raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert raw.hex()==s['source_hex'] and digest(raw)==s['source_sha256']
        kind='dialogue' if key in DIALOGUE_KEYS else 'title' if key==2560 else 'Book_body';out=[]
        for table,row,field in refs:
            off,n=struct.unpack_from('<II',db,table*8);stride={14:44,15:56}[table];r=db[off+row*stride:off+(row+1)*stride];assert row<n and struct.unpack_from('<I',r,field)[0]==key
            assert (table==14 and field==0 and kind=='dialogue') or (table==15 and field==dict(dialogue=32,title=40,Book_body=24)[kind])
            out.append(dict(table=table,row=row,field=field,complete_row_hex=r.hex(),sha256=digest(r),mode=1 if table==14 else {24:4,32:6,40:8}[field]));rows[(table,row)]=dict(table=table,row=row,stride=stride,complete_row_hex=r.hex(),sha256=digest(r))
        tags=re.findall(r'\[i_([^\]]+)\]',s['source_text']);portraits=[]
        if kind=='dialogue':
            assert tags==[PORTRAITS[key]];portraits=[r for r in wad['entries'] if r['trailing_label_candidate'].split('\\')[-1]=='tex_ui_'+tags[0]];assert len(portraits)==1
        else:assert not tags and not any(c in s['source_text'] for c in '[]')
        if key==2560:assert '\r' not in s['source_text'] and '\n' not in s['source_text']
        records.append(dict(key=key,source=s,kind=kind,references=out,portrait_WAD_matches=portraits))
    off,_=struct.unpack_from('<II',db,112);r=db[off+20*44:off+21*44];assert [j for j in struct.unpack_from('<6h',r,18) if j>=0]==[14,15] and struct.unpack_from('<I',r,8)[0]==3580
    queries=['aegis','acaelstra','temple of dreams','riven flats','brotherhood of the blade','wreath of continuance','[i_pi_deanlysetta]'];anchors=[]
    for s in src:
        if not any(x in s['source_text'].casefold() for x in queries):continue
        e=es[s['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision');anchors.append(dict(source=s,state=e['state'],decision_ref=did,current_draft=resolve(ds[did]) if did else None))
    dest=b/'packets/second530';dest.mkdir(parents=True,exist_ok=True)
    protected_write(dest/'source_context.jsonl',serialized(records));protected_write(dest/'full_consumer_rows.jsonl',serialized(list(rows.values())));protected_write(dest/'anchors.jsonl',serialized(anchors))
    protected_write(dest/'separate_consumers.json',json.dumps(dict(entry_thought=dict(key=3580,source=ss[3579],table=14,row=20,field=8,mode=3,not_in_cohort=True),unresolved_prior=[3578,3579,2543,2527,2532,2276,2290,2312]),ensure_ascii=False,indent=2)+'\n')
    save_json(ROOT/'qa/reports/second_stage530_context.json',dict(status='PASS_530_FIVE_TYPED_SECOND_RELIC_CONSUMERS',keys=list(FIELDS),dialogues=DIALOGUE_KEYS,Book=BOOK_KEYS,complete_rows=len(rows),source_portraits=2,separate_entry_thought3580_unselected=True,wording_or_game_changes=0,release_eligible=False))
    print('PASS530 exact5 consumers/3 complete rows;mode3 thought3580 separate')

if __name__=='__main__':main()

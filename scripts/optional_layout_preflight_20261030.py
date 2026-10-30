"""In-memory exact locale rewrite plan for pending choices;never approves/applies prose."""
import json,re,struct,unicodedata
from survey import ROOT,digest,save_json
from unicode_codec042 import encode_unicode,decode_unicode
from book_role_runtime_20261024 import artifact
ROOTREL='workspace/runtime/dialogue3541_20261026'
PREFIX='PSP_GAME/USRDIR/locale/en_us_'
PARENT='6847b0b4d0627af0fc5cf2c7d02569d95f320bd0d70047f45c6fb49c7922b2f2'
ENTRIES='a61e3654b73b04c0d86e6a5f3bc39540bb3db605a4cf45ada03afa530604e301'
def control_tokens(text):return re.findall(r'\[[^]]+\]|\$[0-9a-zA-Z]|\d+|\r\n',text)
def frozen_rows():
    rd=lambda p:json.loads((ROOT/p).read_text(encoding='utf8'))
    hubpath='qa/reports/optional_layout11_review_20261030.json';hub=rd(hubpath);assert len(hub['records'])==11
    packet=rd('workspace/translation/review/20261026_schema24_inventory_v17/packet.json');by={r['key']:r for r in packet['records'] if r['bank']=='trans'};rows=[]
    for item in hub['records']:
        source=rd(item['source_packet']);assert digest((ROOT/item['source_packet']).read_bytes())==item['source_packet_sha256']
        p=next(x for x in source['rows'] if x['key']==item['key']) if 'rows' in source else source
        r=by[item['key']];before=p['current'];after=p['proposed']
        assert before==r['wording'] and r['status']=='selected' and digest(before.encode('utf8'))==item['current_wording_sha256']
        assert p['source_sha256']==r['source_sha256'] and digest(after.encode('utf8'))==item['proposed_wording_sha256']
        test=before
        for change in item['exact_changes']:
            assert test.count(change['before'])==1;test=test.replace(change['before'],change['after'],1)
        assert test==after and before!=after and control_tokens(before)==control_tokens(after)
        assert after==unicodedata.normalize('NFC',after) and '\0' not in after
        assert len(after.encode('utf8'))+1<=5000 and len(after.encode('utf-16le'))//2+1<=2048
        assert encode_unicode(after,{})==decode_unicode(after,{})==after
        rows.append(dict(key=r['key'],id=r['id'],source_sha256=r['source_sha256'],previous_decision=r['decision'],before=before,after=after,before_sha256=digest(before.encode('utf8')),after_sha256=digest(after.encode('utf8')),exact_changes=item['exact_changes']))
    assert len(rows)==len({r['key'] for r in rows})==11
    return hubpath,rows
def rewrite(directory,trans,rows):
    assert len(directory)%20==0
    records=[struct.unpack_from('<IIIHHHH',directory,p) for p in range(0,len(directory),20)];assert len(records)==860
    assert [r[0] for r in records]==sorted({r[0] for r in records})
    changes={r['key']:r for r in rows};assert len(changes)==len(rows) and set(changes)<={r[0] for r in records}
    result=bytearray();newrows=[];cursor=0;actually_changed=[]
    for row in records:
        key,ep,tp,el,tl,flag,res=row;assert tp==cursor and tp+tl<=len(trans);raw=trans[tp:tp+tl];cursor+=tl
        if key in changes:
            change=changes[key];assert raw==change['before'].encode('utf8') and digest(raw)==change['before_sha256']
            new=change['after'].encode('utf8');actually_changed.append(key)
        else:new=raw
        assert len(new)<=65535
        newrows.append((key,ep,len(result),el,len(new),flag,res));result.extend(new)
    assert cursor==len(trans) and set(actually_changed)==set(changes)
    newdir=b''.join(struct.pack('<IIIHHHH',*r) for r in newrows);newtrans=bytes(result)
    for before,after in zip(records,newrows):
        k,ep,tp,el,tl,flag,res=before;assert (after[0],after[1],after[3],after[5],after[6])==(k,ep,el,flag,res)
        beforebytes=trans[tp:tp+tl];afterbytes=newtrans[after[2]:after[2]+after[4]]
        assert afterbytes==(changes[k]['after'].encode('utf8') if k in changes else beforebytes)
    return newdir,newtrans
def main():
    out=ROOT/'workspace/analysis/optional_layout_preflight_20261030';assert not out.exists()
    assert artifact('dialogue3541_20261026')==PARENT and digest((ROOT/'workspace/translation/entries.jsonl').read_bytes())==ENTRIES
    hub,rows=frozen_rows();folder=ROOT/ROOTREL/'disc';directory=(folder/(PREFIX+'dir.dat')).read_bytes();trans=(folder/(PREFIX+'trans.dat')).read_bytes()
    same_dir,same_trans=rewrite(directory,trans,[]);assert same_dir==directory and same_trans==trans
    variants=[]
    for name,subset in [('existing10',[r for r in rows if r['key']!=2675]),('all11',rows)]:
        newdir,newtrans=rewrite(directory,trans,subset)
        variants.append(dict(choice=name,keys=sorted(r['key'] for r in subset),changed_trans_payloads=len(subset),unchanged_trans_payloads=860-len(subset),expected_changed_files=[PREFIX+'dir.dat',PREFIX+'trans.dat'],directory_bytes=len(newdir),before_trans_bytes=len(trans),after_trans_bytes=len(newtrans),delta_trans_bytes=len(newtrans)-len(trans),planned_file_sha256={PREFIX+'dir.dat':digest(newdir),PREFIX+'trans.dat':digest(newtrans)},all860_reextracted_payloads_exact=True,English_offsets_lengths_flags_reserved_and_order_preserved=True,all_other78_current_files_are_outside_writer_scope=True,binary_outputs_written=False,user_approval_received=False))
    # No raw candidate locale files,configuration,approvals,decisions or product trees are written.
    value=dict(status='PASS_PENDING_OPTIONAL10_OR11_IN_MEMORY_LOCALE_REWRITE_PLAN_NOT_APPLIED',parent_artifact_sha256=PARENT,entries_sha256=ENTRIES,hub=hub,hub_sha256=digest((ROOT/hub).read_bytes()),rows=rows,variants=variants,unchanged_roundtrip_exact=True,existing_full_modern_Hangul11172_font_proof_reused=True,new_font_build_needed=False,approved_scope_before_write_required=True,choices_pending=True,game_SSOT_approval_decision_recipe_ISO_changes=0,scope='Memory-onlyserialization/reextraction. It doesnotcreateanapprovedrecipe,productbuild,patch,source-onlyreproduction ornewnativeproof. Actualselectionmustbindtheuseranswerandmatchthefrozenhashes;thenfullbuild/apply/runtimechecksremain.',release_eligible=False)
    save_json(out/'report.json',value);save_json(ROOT/'qa/reports/optional_layout_preflight_20261030.json',value)
    print(json.dumps(dict(unchanged_roundtrip=True,variants=[{k:v[k] for k in ['choice','changed_trans_payloads','unchanged_trans_payloads','delta_trans_bytes','binary_outputs_written','user_approval_received']} for v in variants],product_changes=0)))
if __name__=='__main__':main()

"""Cold folder-runtime preparation and complete source/derived-role audit."""
import argparse,json,re,struct
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from book_role_split_20261024 import NAME,CONFIG,roles

def artifact(name=NAME):
    assert name in [NAME,'book_role_compat_20261024','mode3_journal_20261024','victory_journal_20261024','marker_footer_20261024','loading_korean_20261024','map_korean_20261024','map_generated_korean_20261024','title_geography_20261024','controls_visibility_20261024','property_grouping_20261024','review17_20261024','title_original_20261025','optional6_20261025','dialogue3541_20261026','optional_layout_20261030','second_review_apply_20261030','map_crisp27_20261030']
    p=ROOT/f'workspace/runtime/{name}/artifact.json';a=json.loads(p.read_text(encoding='utf-8'))
    assert len(a['files'])==80
    for rel,m in a['files'].items():
        raw=(p.parent/'disc'/rel).read_bytes();assert len(raw)==m['size'] and digest(raw)==m['sha256']
    return digest(p.read_bytes())

def prepare(q,name=NAME):
    sha=artifact(name)
    import environment_batch378 as e
    e.configure(47800,q);e.static();e.observe('before')
    source=ROOT/'qa/runtime/20261024_source_key_probe_attempt01/boot_commands.json'
    protected_write(q/'boot_commands.json',source.read_text(encoding='utf-8'))
    protected_write(q/'artifact_pin.json',json.dumps(dict(artifact_name=name,artifact_sha256=sha),indent=2)+'\n')
    print('Protected cold runtime preparation complete.')

def preflight(q):
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf-8'))
    cpu=read('before_cpu')['state'];rr=read('before_ranges')['reads'];assert cpu['cpu.pc']==0x08804000+0x4f358
    assert [r['length'] for r in rr]==[1980,136]
    assert struct.unpack_from('<I',bytes.fromhex(rr[0]['hex']),1760)[0]==2499
    t15=struct.unpack_from('<I',bytes.fromhex(rr[1]['hex']),4)[0]-73*56
    assert 0x08800000<t15<t15+7504<0x0a000000
    npc=[];book=[]
    for r in roles():
        expected=r['text'].replace('\r',' ').replace('*B','Itself')
        clean=re.sub(r'\[i_[^]]+\]','',expected)
        if r['role']=='npc_dialogue':npc.append(dict(r,expected=expected,input_units=len(expected)+1,clean_units=len(clean)+1,clean_hex=(clean+'\0').encode('utf-16le').hex(),images=1))
        else:book.append(dict(r,copied_source_key=r['source_key'],null_actor_expected=expected))
    name=read('artifact_pin')['artifact_name']
    pre=dict(artifact_name=name,artifact_sha256=artifact(name),kind='korean_role_split',cpu=cpu,ranges=rr,T15_address=t15,
        cases=book,npc_cases=npc,cold_boot=True,other_artifact_state_imports=0,release_eligible=False)
    protected_write(q/'preflight.json',json.dumps(pre,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(pre,ensure_ascii=True))

def audit(q):
    from environment_owned_scope_20261022 import environment
    from PIL import Image
    read=lambda n:json.loads((q/(n+'.json')).read_text(encoding='utf-8'))
    pre=read('preflight');rr=read('before_full_ranges')['reads']
    assert artifact(pre['artifact_name'])==pre['artifact_sha256'] and read('final_cpu')['state']==pre['cpu']
    assert read('final_ranges')['reads']==rr and [x['length'] for x in rr]==[1980,136,7504]
    edited=bytearray.fromhex(rr[2]['hex'])
    for label,key,field,slot in [('body',4010,24,0x2c),('title',4009,40,0x6c)]:
        assert read(label+'_reference')['written']==4
        struct.pack_into('<I',edited,73*56+field,key)
        c=read(label+'_async_cpu')['state'];assert (c['cpu.a1'],c['cpu.a2'],c['cpu.a3'])==(key,0,pre['cpu']['cpu.s0']+slot)
        expected=next(r['text'] for r in roles() if r['key']==key)+'\0'
        assert read(label+'_full')['hex']==read('reentry_'+label+'_full')['hex']==expected.encode('utf-16le').hex()
    assert read('edited_T15')['hex']==edited.hex()
    pages={};inherited_NPC_evidence=pre['artifact_name']=='book_role_compat_20261024'
    if inherited_NPC_evidence:
        parent=json.loads((ROOT/f'workspace/runtime/{NAME}/artifact.json').read_text(encoding='utf-8'))
        current=json.loads((ROOT/f'workspace/runtime/{pre["artifact_name"]}/artifact.json').read_text(encoding='utf-8'))
        for path,meta in parent['files'].items():
            if not any(path.endswith(l+'_dir.dat') for l in ['de_de','es_es','fr_fr','it_it']):assert current['files'][path]==meta
        old=json.loads((ROOT/f'qa/reports/{NAME}_runtime.json').read_text(encoding='utf-8'));pages=old['NPC_common_widget_pages']
    for r in pre['npc_cases']:
        if inherited_NPC_evidence:continue
        prefix=f'k{r["key"]}_images';actual=read(prefix+'_actual_input');assert actual['text']==r['expected']
        assert read(prefix+'_clean')['hex']==r['clean_hex'] and read(prefix+'_image_vector_summary')['actual_image_records']==1
        obs=read(prefix+'_observations');assert obs['observations'][-1]['done'];pages[r['key']]=obs['pages']
        for p in range(obs['pages']):
            file=q/f'{prefix}_page{p}.png';assert digest(file.read_bytes())==read(f'{prefix}_page{p}_shot')['provenance']['sha256']
    def mask(label):
        p=q/f'Book_alias_{label}.png';assert digest(p.read_bytes())==read('Book_alias_'+label)['provenance']['sha256']
        raw=Image.open(p).convert('RGB').crop((212,44,478,236)).tobytes()
        return bytes(min(raw[i:i+3])>160 for i in range(0,len(raw),3))
    assert mask('visible')==mask('right')==mask('reopen') and mask('visible')!=mask('close')
    visual=read('visual_review');assert visual['Book_title_body_readable_no_overlap'] and visual['Book_no_portrait_tag_or_debug_suffix']
    assert read('terminal_bootstrap')['runtime_reservation_count']==0
    report=dict(status='PASS_ROLE_SPLIT_KOREAN_BOOK_AND_TWO_COMMON_WIDGET_DIALOGUES_CONTROLLED_FIXTURES',artifact_name=pre['artifact_name'],artifact_sha256=pre['artifact_sha256'],
        original_source_selected=3540,held=433,derived_Korean_Book_roles=2,decision_history=4353,
        native_cold_boot=True,cross_artifact_state_imports=0,Book_full_UTF16_NUL_and_reentry=True,Book_screens=4,
        NPC_common_widget_pages=pages,NPC_original_portrait_records=1,NPC_original_macro_effect_preserved=True,
        Book_tag_and_debug_omitted_only_in_derived_roles=True,Book_title_adapted=True,
        CPU_and9620_restored=True,all80_after_verified=True,environment=environment(q),
        NPC_evidence_inherited_from_unchanged_parent_files=inherited_NPC_evidence,
        reference_write_receipts=2 if inherited_NPC_evidence else 4,reference_write_bytes=8 if inherited_NPC_evidence else 16,natural_Bron_dialogue_or_row81_quest_acquisition=False,
        exact_wording_or_presentation_human_approval=False,full_playthrough_verified=False,release_eligible=False)
    save_json(q/'completed.json',report);save_json(ROOT/f'qa/reports/{pre["artifact_name"]}_runtime.json',report)
    print(json.dumps(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','preflight','audit']);p.add_argument('--q',required=True);p.add_argument('--artifact',default=NAME);a=p.parse_args()
    if a.action=='prepare':prepare(ROOT/a.q,a.artifact)
    else:globals()[a.action](ROOT/a.q)

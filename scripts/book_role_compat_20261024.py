"""Preserve the other four locale paths after the shared DB's Book keys split."""
import argparse,copy,json,struct
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from book_role_split_20261024 import derive_split,CONFIG as PARENT_CONFIG

NAME='book_role_compat_20261024';CONFIG=f'development_{NAME}.json'
LANGUAGES=['de_de','es_es','fr_fr','it_it']

def derive_compatible(cfg):
    assert set(cfg)=={'schema_version','policy','parent_config','parent_config_sha256','compatibility_locales','source_to_alias_keys'}
    assert cfg['schema_version']==10 and cfg['policy']=='development_poc_non_distributable'
    assert cfg['parent_config']==PARENT_CONFIG and cfg['compatibility_locales']==LANGUAGES
    assert cfg['source_to_alias_keys']==[[2334,4009],[2335,4010]]
    pp=ROOT/'config'/cfg['parent_config'];assert digest(pp.read_bytes())==cfg['parent_config_sha256']
    plan,outputs=derive_split(json.loads(pp.read_text(encoding='utf-8')))
    plan=copy.deepcopy(plan);outputs=dict(outputs);preserved=[]
    for lang in LANGUAGES:
        prefix=f'PSP_GAME/USRDIR/locale/{lang}';path=prefix+'_dir.dat'
        source=(ROOT/'extracted/disc'/path).read_bytes();rows=[struct.unpack_from('<IIIHHHH',source,i) for i in range(0,len(source),20)]
        assert len(rows)==858 and [r[0] for r in rows]==sorted(set(r[0] for r in rows))
        eng=(ROOT/'extracted/disc'/(prefix+'_eng.dat')).read_bytes();trans=(ROOT/'extracted/disc'/(prefix+'_trans.dat')).read_bytes()
        final=bytearray(source);records=[]
        for oldkey,newkey in cfg['source_to_alias_keys']:
            assert all(r[0]!=newkey for r in rows) and newkey>rows[-1][0]
            old=next(r for r in rows if r[0]==oldkey);row=(newkey,*old[1:]);final.extend(struct.pack('<IIIHHHH',*row))
            _,ep,tp,el,tl,flag,res=row
            assert ep+el<=len(eng) and tp+tl<=len(trans)
            records.append(dict(source_key=oldkey,alias_key=newkey,directory_tuple=list(row),
                original_eng_sha256=digest(eng[ep:ep+el]),original_trans_sha256=digest(trans[tp:tp+tl]),
                payload_alias_to_same_original_range=True))
        assert bytes(final[:len(source)])==source and len(final)==17200
        outputs[path]=bytes(final)
        plan['writes'].append(dict(owner='Other-locale compatibility for shared Book keys',path=path,offset=len(source),size=40,
            expected_sha256=digest(b''),final_sha256=digest(final[len(source):]),source_size=len(source),
            derivation='Append two sorted directory rows aliasing the exact original2334/2335 eng/trans ranges. Preserve all source rows and payload files.'))
        preserved.append(dict(locale=lang,source_directory_sha256=digest(source),final_directory_sha256=digest(final),
            original_858_rows_byte_equal=True,all_eng_trans_payload_bytes_unchanged=True,records=records))
    plan['writes'].sort(key=lambda w:(w['path'],w['offset']));plan['allowed_changed_files']=sorted(outputs)
    plan['diagnostic_input']=cfg;plan['Book_locale_compatibility']=preserved
    plan['source_scope_caveat']='Korean adaptation remains en_us only; other locale alias keys preserve their own exact original text, markers and existing layout.'
    return plan,outputs

def configure():
    pp=ROOT/'config'/PARENT_CONFIG
    cfg=dict(schema_version=10,policy='development_poc_non_distributable',parent_config=PARENT_CONFIG,parent_config_sha256=digest(pp.read_bytes()),
        compatibility_locales=LANGUAGES,source_to_alias_keys=[[2334,4009],[2335,4010]])
    protected_write(ROOT/'config'/CONFIG,json.dumps(cfg,indent=2)+'\n')
    report=dict(status='COMPATIBILITY_DEFECT_IDENTIFIED_AND_SOURCE_ALIAS_REPAIR_CONFIGURED',
        defective_parent='book_role_split_20261024',issue='Shared DB new keys4009/4010 were absent in four other locale directories.',
        fix='Append exact source-key directory aliases in each other locale; preserve all locale payload bytes and original858 rows.',
        no_new_wording_or_scope_choice=True,SSOT_changed=False,new_selected=0,other_locale_runtime_pending=True,release_eligible=False)
    save_json(ROOT/'qa/reports/book_role_compatibility_defect_20261024.json',report)
    print(json.dumps(report))

if __name__=='__main__':configure()

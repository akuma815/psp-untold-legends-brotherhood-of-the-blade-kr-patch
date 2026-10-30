"""Restore the complete source title-map texture under the user's explicit scope decision."""
import argparse,copy,json,shutil
from survey import ROOT,digest,save_json
from catalog_survey034 import protected_write
from review17_20261024 import CONFIG as PARENT,derive_review17
from title_geography_20261024 import source,WAD,WORK as OLD_TITLE

NAME='title_original_20261025'
CONFIG='development_'+NAME+'.json'
DECISION='workspace/translation/approvals/20261025_title_map_original.json'


def configuration():
    decision=json.loads((ROOT/DECISION).read_text(encoding='utf8'))
    assert decision['user_instruction']=='이거 타이틀의 지도명은 굳이 번역하지 말고 원문 그대로 둬'
    return dict(schema_version=22,policy='development_poc_non_distributable',parent_config=PARENT,
        parent_config_sha256=digest((ROOT/'config'/PARENT).read_bytes()),
        title_map_scope_decision=DECISION,title_map_scope_decision_sha256=digest((ROOT/DECISION).read_bytes()),
        restore_original_WAD_index=5419,restore_original_record_sha256='4f2bd149ebf75bca7816fbf33936290475a769e82a2c3013181dfb0ce93d7475',
        scope='All place-name pixels in title background remain original,including Aven,Badlands and clipped Woodland Ring. In-game worldmap and all text unchanged.',
        main_translation_SSOT_changed=False,release_eligible=False)


def prepare():
    snap=ROOT/'qa/ssot/20261025_before_title_map_original';assert not snap.exists()
    names=['docs/HANDOFF.md','docs/HANDOFF_2026-10-25.md','AGENTS.md','README.md','qa/reports/continuation_queue_20261024.json',
        'scripts/build_font_folder.py','scripts/book_role_runtime_20261024.py','scripts/manual_play_20261024.py',
        'workspace/runtime/review17_20261024/artifact.json','workspace/runtime/review17_20261024/expected_writes.json']
    for name in names:
        to=snap/name;to.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,to)
    decision=dict(status='USER_EXPLICITLY_RETAINS_ORIGINAL_TITLE_MAP_PLACE_NAMES',authority='user',date_local='2026-10-25',
        user_instruction='이거 타이틀의 지도명은 굳이 번역하지 말고 원문 그대로 둬',
        previous_artifact='workspace/runtime/review17_20261024/artifact.json',
        previous_artifact_sha256=digest((ROOT/'workspace/runtime/review17_20261024/artifact.json').read_bytes()),
        restore_source_title_record5419=True,source_title_place_names_retained=['Aven','The Badlands','clipped original Woodland Ring'],
        in_game_map_six_Korean_labels_and_body_text_retained=True,original_logo_retained=True,
        new_left_title_Korean_draft_not_adopted=True,whole_project_wording_layout_or_release_approval=False)
    protected_write(ROOT/DECISION,json.dumps(decision,ensure_ascii=False,indent=2)+'\n')
    generated=ROOT/'workspace/graphics/title_left_kr_20261025_v1'
    src=ROOT.home()/'.codex/generated_images/01a144f9-078e-7992-9d6a-e42ffa5d54f9/exec-b217cd8e-f095-4422-9a32-594f44d8c205.png'
    assert src.is_file();shutil.copy2(src,generated/'imagegen_01.png')
    save_json(generated/'decision.json',dict(status='UNADOPTED_USER_RETAINS_ORIGINAL_TITLE_MAP',decision=DECISION,
        generator='built-in image_gen',original_generated_path=str(src),generated_sha256=digest(src.read_bytes()),
        prompt='prompt.txt',no_draft_pixels_in_product=True))
    protected_write(ROOT/'config'/CONFIG,json.dumps(configuration(),ensure_ascii=False,indent=2)+'\n')
    save_json(snap/'manifest.json',dict(status='BEFORE_EXPLICIT_TITLE_SCOPE_RESTORE',files={n:digest((ROOT/n).read_bytes()) for n in names},
        entries_sha256=digest((ROOT/'workspace/translation/entries.jsonl').read_bytes()),
        terms_sha256=digest((ROOT/'workspace/translation/terminology.json').read_bytes()),release_eligible=False))
    print('Recorded explicit title-map original scope;draft preserved unadopted;schema22 config prepared,game not yet changed.')


def derive_original_title(cfg):
    assert cfg==configuration()
    parentcfg=json.loads((ROOT/'config'/PARENT).read_text(encoding='utf8'))
    plan,outputs=derive_review17(parentcfg);plan=copy.deepcopy(plan);outputs=dict(outputs)
    parent=json.loads((ROOT/'workspace/runtime/review17_20261024/artifact.json').read_text(encoding='utf8'))
    assert digest(outputs[WAD])==parent['files'][WAD]['sha256']
    entry,original,palette,pixels,rgba=source();at=entry['offset'];end=at+len(original)
    translated=(OLD_TITLE/'title_korean512.bin').read_bytes();before=outputs[WAD]
    assert before[at:end]==translated and translated[:1056]==original[:1056]
    owners=[w for w in plan['writes'] if w['path']==WAD and not (w['offset']+w['size']<=at or w['offset']>=end)]
    assert len(owners)==1 and owners[0]['owner']=='Generated Korean2 title-map captions'
    assert (owners[0]['offset'],owners[0]['size'])==(at+1056,len(original)-1056)
    plan['writes'].remove(owners[0])
    outputs[WAD]=before[:at]+original+before[end:]
    assert len(outputs[WAD])==len(before) and outputs[WAD][:at]==before[:at] and outputs[WAD][end:]==before[end:]
    plan['diagnostic_input']=cfg
    plan['title_map_captions']=dict(status='ORIGINAL_SOURCE_PIXELS_RETAINED_USER_SCOPE',captions=['Aven','The Badlands','original clipped Woodland Ring'],
        source_record_index=5419,source_record_sha256=digest(original),scope_decision=DECISION,
        translated_title_map_captions_selected=0,original_logo_preserved=True,release_eligible=False)
    plan['original_title_restore']=dict(parent_artifact_sha256=digest((ROOT/'workspace/runtime/review17_20261024/artifact.json').read_bytes()),
        offset=at,bytes=len(original),removed_prior_writer=owners[0],source_indexed_roundtrip=True,
        other79_files_and_WAD_outside_this_record_unchanged=True,actual_game_code_or_main_text_changes=0)
    return plan,outputs


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare']);p.parse_args();prepare()

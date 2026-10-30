"""Single-unit diagnostic and PRX hook, not an approved font or translation."""
import json
import re
import struct
from survey import ROOT,digest,save_json
from allegrex_profile import Profile
from hangul_columns import atlas,DIAGNOSTIC,rebuild_locale
from text_limits import check_template

VIRTUAL_FIRST,VIRTUAL_END,TEXTURE_FIRST,TOTAL=256,11428,11428,14675
PACK_OFFSETS=[*range(2,8),*range(16,32)]

def virtual_metrics(book):
    records=bytearray()
    for ordinal,(code,seq) in enumerate(book['mapping'].items()):
        assert code==0xac00+ordinal
        tids=[book['metrics'][slot-256][0] for slot in seq]
        packed=sum(tid<<(12*x) for x,tid in enumerate(tids)).to_bytes(22,'little')
        record=bytearray(32)
        struct.pack_into('<H',record,0,256+ordinal)
        struct.pack_into('<ii',record,8,14,0)
        for offset,value in zip(PACK_OFFSETS,packed):record[offset]=value
        assert int.from_bytes(bytes(record[i] for i in PACK_OFFSETS),'little')==int.from_bytes(packed,'little')
        records.extend(record)
    assert digest(records)=='6b29afd9011e95fd2f9bb7e110eb2b9e734d0913deac7dc12a426bf0f57bbad2'
    return records

def atlas_single(source,src_pixels,book):
    pixels,_,indices=atlas(source,src_pixels,book)
    metrics=virtual_metrics(book)
    for tid,col in enumerate(book['textures']):
        x,y,w,h=book['cells'][tid]
        metrics.extend(struct.pack('<Iiii4f',TEXTURE_FIRST+tid,0,0,0,
                                   (x+1)/512,(y+1)/512,(x+2)/512,(y+1+len(col))/512))
    assert len(metrics)//32+256==TOTAL
    return pixels,metrics,indices

def encode(text,book):
    result=[]
    for char in text:
        code=ord(char)
        if code<=255:result.append(char)
        elif code in book['mapping']:result.append(chr(256+code-0xac00))
        else:raise ValueError(f'Unmapped single-unit character U+{code:04X}')
    return ''.join(result)

def decode(text,book):
    result=[]
    for char in text:
        code=ord(char)
        if code<=255:result.append(char)
        elif 256<=code<11428:result.append(chr(0xac00+code-256))
        else:raise ValueError(f'Invalid single-unit code {code}')
    return ''.join(result)

def rebuild_single_locale(directory,trans,book,diagnostic=None,unicode_hangul=False):
    if diagnostic is None:return rebuild_locale(directory,trans,book,encoder=encode,decoder=decode)
    if diagnostic.get('schema_version') in [7,8]:
        #Source-preserved development input:never synthesize a3881 font/wrap fixture.
        expected={'schema_version','policy','target_key','replace_body','cases','static_overrides','file_replacement','trans_overrides','encoding_policy','unmapped_probe_codepoints','prologue_policy'}
        assert set(diagnostic)==expected and unicode_hangul
        assert diagnostic['policy']=='development_poc_non_distributable' and diagnostic['file_replacement']=='exact'
        assert diagnostic['target_key']==3881 and diagnostic['replace_body'] is False and diagnostic['cases']==[]
        assert diagnostic['unmapped_probe_codepoints']==[] and diagnostic['encoding_policy']=='utf8_modern_hangul_v1'
        if diagnostic['schema_version']==7:
            assert diagnostic['prologue_policy']=='preserve_original_unselected' and 3881 not in {r['key'] for r in diagnostic['trans_overrides']}
        else:
            assert diagnostic['prologue_policy']=='translate_original_contextual' and 3881 in {r['key'] for r in diagnostic['trans_overrides']}
        from unicode_codec042 import encode_unicode,decode_unicode
        return replace_observed_trans(directory,trans,directory,trans,book,diagnostic['trans_overrides'],encoder=encode_unicode,decoder=decode_unicode)
    expected={'schema_version','policy','target_key','replace_body','cases'}
    if diagnostic['schema_version'] in [2,3,4,5,6]:expected.add('static_overrides')
    if diagnostic['schema_version'] in [3,4,5,6]:
        expected.add('file_replacement')
        assert diagnostic['file_replacement']=='exact'
    if diagnostic['schema_version'] in [4,5,6]:expected.add('trans_overrides')
    if diagnostic['schema_version'] in [5,6]:expected.update(['encoding_policy','unmapped_probe_codepoints'])
    if diagnostic['schema_version']==6:expected.add('event_resource_probe')
    assert set(diagnostic)==expected
    assert diagnostic['schema_version'] in [1,2,3,4,5,6] and diagnostic['policy']=='development_poc_non_distributable'
    assert unicode_hangul==(diagnostic['schema_version'] in [5,6])
    assert diagnostic['target_key']==3881 and diagnostic['replace_body'] is True
    assert diagnostic['cases'] and len({c['id'] for c in diagnostic['cases']})==len(diagnostic['cases'])
    for case in diagnostic['cases']:
        assert set(case)=={'id','text'} and isinstance(case['text'],str)
        assert not any(c in case['text'] for c in '\r\n[]')
    text='\r\n'.join(c['text'] for c in diagnostic['cases'])
    encoder,decoder=encode,decode
    if unicode_hangul:
        from unicode_codec042 import encode_unicode,decode_unicode
        assert diagnostic['encoding_policy']=='utf8_modern_hangul_v1'
        probes=diagnostic['unmapped_probe_codepoints'];assert len(probes)==len(set(probes))
        assert all(type(n) is int and 255<n<=65535 and not 0xac00<=n<=0xd7a3 and not 0xd800<=n<=0xdfff for n in probes)
        assert set(probes)=={ord(c) for c in text if ord(c)>255 and not 0xac00<=ord(c)<=0xd7a3}
        encoder=lambda value,book:encode_unicode(value,book,probes)
        decoder=lambda value,book:decode_unicode(value,book,probes)
    result=rebuild_locale(directory,trans,book,encoder=encoder,decoder=decoder,diagnostic_text=text,replace_body=True)
    if diagnostic['schema_version'] in [4,5,6]:
        newdir,newtrans,changes=result
        if unicode_hangul:encoder,decoder=encode_unicode,decode_unicode
        newdir,newtrans,additional=replace_observed_trans(directory,trans,newdir,newtrans,book,diagnostic['trans_overrides'],encoder=encoder,decoder=decoder,resource_probe=diagnostic.get('event_resource_probe'))
        return newdir,newtrans,changes+additional
    return result


def replace_tutorial2499(source_dir,source_trans,directory,trans,book,overrides,encoder=encode,decoder=decode):
    """Observed literal-bracket tutorial only; unknown text grammars fail closed."""
    assert len(overrides)==1
    r=overrides[0]
    assert set(r)=={'key','source_text','text','control_policy'}
    assert r['key']==2499 and r['control_policy']=='tutorial2499_observed_literal_brackets_v1'
    for value in [r['source_text'],r['text']]:
        assert isinstance(value,str) and value and '\0' not in value
        parts=value.split('\r\n');assert len(parts)==4 and parts[1]==''
        assert not any(c in parts[0] for c in '[]$')
        assert parts[2].startswith('[') and parts[2].endswith(']') and parts[3].startswith('[') and parts[3].endswith(']')
        assert value.count('[')==value.count(']')==2
        assert '$' not in parts[2] and re.findall(r'\$[A-Za-z]',value)==['$x'] and value.count('$')==1
    assert r['source_text'].count('\r\n')==r['text'].count('\r\n')==3
    encoded=encoder(r['text'],book).encode('utf-8')
    assert decoder(encoded.decode('utf-8'),book)==r['text']
    #037 confirmed2499 enters D8FD4 with2048 units, via DA810/DB03C's5000-byte formatter.
    check_template(encoded.decode('utf-8'),'Tutorial2499')
    assert len(encoded)<=65535
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)


def replace_observed_trans(source_dir,source_trans,directory,trans,book,overrides,encoder=encode,decoder=decode,resource_probe=None):
    """Only individually observed contexts; unknown IDs/policies fail closed."""
    assert len({r['key'] for r in overrides})==len(overrides)
    from alice_table149 import FIELDS
    from layla_table177 import FIELDS as LAYLA_FIELDS
    from nathan_table186 import FIELDS as NATHAN_FIELDS
    from will_table197 import FIELDS as WILL_FIELDS
    from trio_table207 import FIELDS as TRIO_FIELDS
    from generic_table219 import FIELDS as GENERIC_FIELDS
    from warnings_table229 import FIELDS as WARNING_FIELDS
    from quest_journal273 import FIELDS as QUEST_FIELDS
    from inn_rescue283 import FIELDS as INN_RESCUE_FIELDS
    from rescue_dialogue294 import FIELDS as RESCUE_DIALOGUE_FIELDS
    from pending304 import FIELDS as PENDING_FIELDS
    from generic316 import FIELDS as FOUR_GENERIC_FIELDS
    from illness327 import FIELDS as ILLNESS_FIELDS
    from cure338 import FIELDS as CURE_FIELDS
    from shrines350 import FIELDS as SHRINE_FIELDS
    from academy361 import FIELDS as ACADEMY_FIELDS
    from gates372 import FIELDS as GATE_FIELDS
    from recovery385 import FIELDS as RECOVERY_FIELDS
    from transition397 import FIELDS as TRANSITION_FIELDS
    from gorgein409 import FIELDS as GORGEIN_FIELDS
    from vrultok445 import FIELDS as VRULTOK_FIELDS
    from gates463 import FIELDS as REPAIR_GATE_FIELDS
    from prisoner490 import FIELDS as PRISONER_FIELDS
    from threat506 import FIELDS as THREAT_FIELDS
    from second532 import FIELDS as SECOND_FIELDS
    from relic_arc_policy_20261020 import FIELDS as RELIC_ARC_FIELDS
    from main_story_policy_20261020 import FIELDS as MAIN_STORY_FIELDS
    from sidequest_policy_20261020 import FIELDS as SIDEQUEST_FIELDS
    from late_dialogue_policy_20261020 import FIELDS as LATE_DIALOGUE_FIELDS
    from ability_corpus_policy_20261020 import FIELDS as ABILITY_CORPUS_FIELDS
    from document_body_policy_20261020 import FIELDS as DOCUMENT_BODY_FIELDS
    from document_portraits_20261022 import FIELDS as DOCUMENT_PORTRAIT_FIELDS
    from document_markup_20261022 import FIELDS as DOCUMENT_MARKUP_FIELDS
    from document_zero_20261022 import FIELDS as DOCUMENT_ZERO_FIELDS
    from npc_marker_preserve_20261022 import FIELDS as NPC_MARKER_FIELDS
    from npc_pages_preserve_20261022 import FIELDS as NPC_PAGE_FIELDS
    from button_hints_20261022 import FIELDS as BUTTON_HINT_FIELDS
    from story_portraits_20261022 import FIELDS as STORY_PORTRAIT_FIELDS
    from story_controls_20261023 import FIELDS as STORY_CONTROL_FIELDS
    from book_literal_20261023 import FIELDS as BOOK_LITERAL_FIELDS
    from failure_meaning_20261023 import FIELDS as FAILURE_MEANING_FIELDS
    from shared_voice_20261023 import FIELDS as SHARED_VOICE_FIELDS
    from item_description_policy_20261020 import FIELDS as ITEM_DESCRIPTION_FIELDS
    from equipment_policy_20261020 import FIELDS as EQUIPMENT_FIELDS
    from epilogue_policy_20261020 import FIELDS as EPILOGUE_FIELDS
    from fallback_names_20261021 import FIELDS as FALLBACK_NAME_FIELDS
    allowed = [{2499},{2499,3081},{2499,3081,2266,2502},{2499,3081,2266,2502,2501,2267,2269,2272},{2499,3081,2266,2502,2501,2267,2269,2272,3881},{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273},{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273,2270},{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273,2270,3022},{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273,2270,3022}|set(FIELDS),{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273,2270,3022}|set(FIELDS)|set(LAYLA_FIELDS),{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273,2270,3022}|set(FIELDS)|set(LAYLA_FIELDS)|set(NATHAN_FIELDS),{2499,3081,2266,2502,2501,2267,2269,2272,3881,2271,2273,2270,3022}|set(FIELDS)|set(LAYLA_FIELDS)|set(NATHAN_FIELDS)|set(WILL_FIELDS)]
    cumulative=allowed[-1]
    for batch in [TRIO_FIELDS,GENERIC_FIELDS,WARNING_FIELDS,QUEST_FIELDS,INN_RESCUE_FIELDS,RESCUE_DIALOGUE_FIELDS,PENDING_FIELDS,FOUR_GENERIC_FIELDS,ILLNESS_FIELDS,CURE_FIELDS,SHRINE_FIELDS,ACADEMY_FIELDS,GATE_FIELDS,RECOVERY_FIELDS,TRANSITION_FIELDS,GORGEIN_FIELDS,VRULTOK_FIELDS,REPAIR_GATE_FIELDS,PRISONER_FIELDS,THREAT_FIELDS,SECOND_FIELDS]:
        cumulative=cumulative|set(batch)
        allowed.append(cumulative)
    allowed.append(cumulative|set(RELIC_ARC_FIELDS))
    allowed.append(cumulative|set(RELIC_ARC_FIELDS)|set(MAIN_STORY_FIELDS))
    allowed.append(cumulative|set(RELIC_ARC_FIELDS)|set(MAIN_STORY_FIELDS)|set(SIDEQUEST_FIELDS))
    allowed.append(cumulative|set(RELIC_ARC_FIELDS)|set(MAIN_STORY_FIELDS)|set(SIDEQUEST_FIELDS)|set(LATE_DIALOGUE_FIELDS))
    allowed.append(cumulative|set(RELIC_ARC_FIELDS)|set(MAIN_STORY_FIELDS)|set(SIDEQUEST_FIELDS)|set(LATE_DIALOGUE_FIELDS)|set(ABILITY_CORPUS_FIELDS))
    allowed.append(cumulative|set(RELIC_ARC_FIELDS)|set(MAIN_STORY_FIELDS)|set(SIDEQUEST_FIELDS)|set(LATE_DIALOGUE_FIELDS)|set(ABILITY_CORPUS_FIELDS)|set(DOCUMENT_BODY_FIELDS))
    allowed.append(cumulative|set(RELIC_ARC_FIELDS)|set(MAIN_STORY_FIELDS)|set(SIDEQUEST_FIELDS)|set(LATE_DIALOGUE_FIELDS)|set(ABILITY_CORPUS_FIELDS)|set(DOCUMENT_BODY_FIELDS)|set(ITEM_DESCRIPTION_FIELDS))
    allowed.append(allowed[-1]|set(EQUIPMENT_FIELDS))
    allowed.append(allowed[-1]|set(EPILOGUE_FIELDS))
    allowed.append(allowed[-1]|set(FALLBACK_NAME_FIELDS))
    allowed.append(allowed[-1]|set(DOCUMENT_PORTRAIT_FIELDS))
    allowed.append(allowed[-1]|set(DOCUMENT_MARKUP_FIELDS))
    allowed.append(allowed[-1]|set(DOCUMENT_ZERO_FIELDS))
    allowed.append(allowed[-1]|set(NPC_MARKER_FIELDS))
    allowed.append(allowed[-1]|set(NPC_PAGE_FIELDS))
    allowed.append(allowed[-1]|set(BUTTON_HINT_FIELDS))
    allowed.append(allowed[-1]|set(STORY_PORTRAIT_FIELDS))
    allowed.append(allowed[-1]|set(STORY_CONTROL_FIELDS))
    allowed.append(allowed[-1]|set(BOOK_LITERAL_FIELDS))
    allowed.append(allowed[-1]|set(FAILURE_MEANING_FIELDS))
    allowed.append(allowed[-1]|set(SHARED_VOICE_FIELDS))
    assert {r['key'] for r in overrides} in allowed
    changes=[]
    for r in overrides:
        if r['key']==2499:
            if resource_probe is None:
                directory,trans,c=replace_tutorial2499(source_dir,source_trans,directory,trans,book,[r],encoder,decoder)
            else:
                directory,trans,c=replace_event_resource_probe057(source_dir,source_trans,directory,trans,book,r,resource_probe,encoder,decoder)
        elif r['key'] in FALLBACK_NAME_FIELDS:
            from fallback_names_20261021 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in EPILOGUE_FIELDS:
            from epilogue_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in EQUIPMENT_FIELDS:
            from equipment_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in ITEM_DESCRIPTION_FIELDS:
            from item_description_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in SHARED_VOICE_FIELDS:
            from shared_voice_20261023 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in FAILURE_MEANING_FIELDS:
            from failure_meaning_20261023 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in BOOK_LITERAL_FIELDS:
            from book_literal_20261023 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in STORY_CONTROL_FIELDS:
            from story_controls_20261023 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in STORY_PORTRAIT_FIELDS:
            from story_portraits_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in BUTTON_HINT_FIELDS:
            from button_hints_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in NPC_PAGE_FIELDS:
            from npc_pages_preserve_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in NPC_MARKER_FIELDS:
            from npc_marker_preserve_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in DOCUMENT_ZERO_FIELDS:
            from document_zero_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in DOCUMENT_MARKUP_FIELDS:
            from document_markup_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in DOCUMENT_PORTRAIT_FIELDS:
            from document_portraits_20261022 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in DOCUMENT_BODY_FIELDS:
            from document_body_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in ABILITY_CORPUS_FIELDS:
            from ability_corpus_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in LATE_DIALOGUE_FIELDS:
            from late_dialogue_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in SIDEQUEST_FIELDS:
            from sidequest_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in MAIN_STORY_FIELDS:
            from main_story_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in RELIC_ARC_FIELDS:
            from relic_arc_policy_20261020 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in SECOND_FIELDS:
            from second532 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in THREAT_FIELDS:
            from threat506 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in PRISONER_FIELDS:
            from prisoner490 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in REPAIR_GATE_FIELDS:
            from gates463 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in VRULTOK_FIELDS:
            from vrultok445 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in GORGEIN_FIELDS:
            from gorgein409 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in TRANSITION_FIELDS:
            from transition397 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in RECOVERY_FIELDS:
            from recovery385 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in GATE_FIELDS:
            from gates372 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in ACADEMY_FIELDS:
            from academy361 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in SHRINE_FIELDS:
            from shrines350 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in CURE_FIELDS:
            from cure338 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in ILLNESS_FIELDS:
            from illness327 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in FOUR_GENERIC_FIELDS:
            from generic316 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in PENDING_FIELDS:
            from pending304 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in RESCUE_DIALOGUE_FIELDS:
            from rescue_dialogue294 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in INN_RESCUE_FIELDS:
            from inn_rescue283 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in QUEST_FIELDS:
            from quest_journal273 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in WARNING_FIELDS:
            from warnings_table229 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in GENERIC_FIELDS:
            from generic_table219 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in TRIO_FIELDS:
            from trio_table207 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in WILL_FIELDS:
            from will_table197 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in NATHAN_FIELDS:
            from nathan_table186 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in LAYLA_FIELDS:
            from layla_table177 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key'] in FIELDS:
            from alice_table149 import validate
            encoded=validate(r,book,encoder,decoder)
            directory,trans,c=replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)
        elif r['key']==3022:
            directory,trans,c=replace_hurry143(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        elif r['key']==2270:
            directory,trans,c=replace_alice127(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        elif r['key'] in [2271,2273]:
            directory,trans,c=replace_friends122(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        elif r['key']==3881:
            directory,trans,c=replace_prologue115(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        elif r['key'] in [2266,2502]:
            directory,trans,c=replace_quest_literals105(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        elif r['key'] in [2501,2267,2269,2272]:
            directory,trans,c=replace_first_kill_literals112(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        else:
            directory,trans,c=replace_ability3081(source_dir,source_trans,directory,trans,book,r,encoder,decoder)
        changes.extend(c)
    return directory,trans,changes


def replace_hurry143(source_dir,source_trans,directory,trans,book,r,encoder,decoder):
    import unicodedata
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==3022 and r['control_policy']=='alice3022_observed_hurry_v1'
    assert digest(r['source_text'].encode('utf8'))=='87df824abf049fa20960a91d9105bd93de9312a6e838bd95d50e6fb9b395fd62'
    tag='[i_PI_AliceMcKyntireConcerned]';text=r['text']
    assert text==unicodedata.normalize('NFC',text) and text.startswith(tag) and len(text)>len(tag)
    assert not any(c in text[len(tag):] for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text
    check_template(text,'Observed Alice3022 inline widget;shared2270 capacity basis')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)

def replace_alice127(source_dir,source_trans,directory,trans,book,r,encoder,decoder):
    import unicodedata
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==2270
    assert r['control_policy']=='alice2270_observed_portrait_camera_v1' and digest(r['source_text'].encode('utf8'))=='c9005b85c9bb79efe8ade38112e6a608c84ee3d9470946f5a815c65c6badbdf3'
    text=r['text'];tag='[i_PI_AliceMcKyntireConcerned]';assert text and text==unicodedata.normalize('NFC',text) and text.startswith(tag)
    parts=text[len(tag):].split('\r\n\r\n');assert len(parts)==2 and parts[0] and '[' not in parts[0] and ']' not in parts[0]
    assert parts[1].startswith('[') and parts[1].endswith(']') and parts[1].count('[')==parts[1].count(']')==1
    assert re.findall(r'\$[A-Za-z]',text)==['$r','$u','$d','$w','$e']
    stripped=parts[0]+parts[1][1:-1]
    for token in ['$r','$u','$d','$w','$e']:stripped=stripped.replace(token,'')
    assert not any(c in stripped for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text;check_template(text,'Observed Alice2270')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)

def replace_friends122(source_dir,source_trans,directory,trans,book,r,encoder,decoder):
    import unicodedata
    guards={2271:'68f77b7803282e9c4e5c5fad18114fa3376e4163ba7fae0ea34ec4f7ea7d1faa',2273:'24ca0e172051d35324ce5a47271808ceb6d7f72bf84c2abe074614af4af6ffdb'}
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in guards
    assert r['control_policy']=='friends2271_2273_observed_literals_v1' and digest(r['source_text'].encode('utf8'))==guards[r['key']]
    assert r['text'] and r['text']==unicodedata.normalize('NFC',r['text']) and not any(c in r['text'] for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(r['text'],book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==r['text']
    check_template(r['text'],f'Natural friends journal{r["key"]}')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)

def validate_prologue115(r):
    import unicodedata
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==3881
    assert r['control_policy']=='prologue3881_backgrounds_paragraphs_v1'
    assert digest(r['source_text'].encode('utf8'))=='7286a0d320664f925164da6f69d3c00fc5bc9782cd97d6c3fb6eacae8b900303'
    source=r['source_text'].split('\r\n\r\n');target=r['text'].split('\r\n\r\n');assert len(source)==len(target)==10
    tags=['[bg_SL_intro1]','[bg_SL_intro2]']
    assert re.findall(r'\[[^\]]*\]',r['text'])==tags
    for i,text in enumerate(target):
        assert text and text==unicodedata.normalize('NFC',text)
        if i in [0,6]:
            tag=tags[0 if i==0 else 1];assert text.startswith(tag);text=text[len(tag):]
        assert text and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    check_template(r['text'],'Contextual prologue3881')

def replace_prologue115(source_dir,source_trans,directory,trans,book,r,encoder,decoder):
    validate_prologue115(r)
    encoded=encoder(r['text'],book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==r['text']
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)

def replace_first_kill_literals112(source_dir,source_trans,directory,trans,book,r,encoder,decoder):
    """Only the four observed first-kill/scream literals;no general event grammar."""
    guards={2501:'0e90ad0fa6cce77e52d2b2c52a008b3b06a5cbbc0cc7eb63498f4cebc00177ab',
      2267:'6984fb3322fc75dc4cc0b83e30e209ce5b020a01bdb9a68f66a88e349a515855',
      2269:'d512f81eb221c909a4dda66c78d1db03c6427248588898b3d849613af4929026',
      2272:'32bd1c5bede6aff9206b85aefc4304c6a525e286c56497f7aa6ecb86901eb25c'}
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in guards
    assert r['control_policy']=='first_kill_scream_literals_v1' and digest(r['source_text'].encode('utf8'))==guards[r['key']]
    import unicodedata
    for text in [r['source_text'],r['text']]:
        assert isinstance(text,str) and text and text==unicodedata.normalize('NFC',text)
        assert not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(r['text'],book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==r['text']
    check_template(encoded.decode('utf8'),f'First kill/scream literal{r["key"]}')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)


def replace_quest_literals105(source_dir,source_trans,directory,trans,book,r,encoder,decoder):
    """Only the two source-bound first-quest literals; no new text grammar."""
    assert set(r)=={'key','source_text','text','control_policy'}
    guards={2266:'45558a4e916ccc25a3f4a2b924651549d09b4d6d1b43bca580607a094d20417a',
      2502:'5cd81156adada419201b5ed8b9b13a86f90927a641b85ccc3eb1b6ecf59b971d'}
    assert r['key'] in guards and r['control_policy']=='quest2266_2502_observed_literals_v1'
    assert digest(r['source_text'].encode('utf8'))==guards[r['key']]
    import unicodedata
    for text in [r['source_text'],r['text']]:
        assert isinstance(text,str) and text and text==unicodedata.normalize('NFC',text)
        assert not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(r['text'],book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==r['text']
    # Body path observed in104: DB03C5000-byte formatting then D8FD4 with2048 units.
    # Title uses the same conservative development budget; its actual call is a107 gate.
    check_template(encoded.decode('utf8'),f'First quest literal{r["key"]}')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)


def replace_event_resource_probe057(source_dir,source_trans,directory,trans,book,r,probe,encoder=encode,decoder=decode):
    """Explicit temporary QA fixture, not a tutorial wording decision."""
    assert set(probe)=={'policy','source_id','source_sha256','source_tokens','target_key','fixture_not_translation'}
    assert probe['policy']=='event2499_source2465_resource_probe_v1' and probe['target_key']==2499 and probe['fixture_not_translation'] is True
    assert probe['source_id']=='ULKS46015-v1.01:en_us/trans:2465'
    assert probe['source_sha256']=='1697ce51b96406325070b0297973976d58a295f1fd9106742d21c346ec13108d'
    assert probe['source_tokens']==['[i_PI_MadamDiana]','[p]']
    source=next(json.loads(l) for l in (ROOT/'workspace/translation/baseline/source_entries.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(l)['id']==probe['source_id'])
    raw=(ROOT/'extracted/disc'/source['source_path']).read_bytes()[source['offset']:source['offset']+source['byte_length']]
    assert digest(raw)==probe['source_sha256']==source['source_sha256'] and all(t.encode('ascii') in raw for t in probe['source_tokens'])
    assert set(r)=={'key','source_text','text','control_policy'} and r['key']==2499 and r['control_policy']==probe['policy']
    text=r['text'];image,page=probe['source_tokens']
    assert isinstance(text,str) and text.startswith(image) and text.count(image)==text.count(page)==1
    parts=text[len(image):].split(page);assert len(parts)==2 and all(s.strip() for s in parts)
    stripped=''.join(parts)
    assert not any(c in stripped for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    encoded=encoder(text,book).encode('utf-8');assert decoder(encoded.decode('utf-8'),book)==text
    check_template(encoded.decode('utf-8'),'Explicit2499 resource QA fixture')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)


def replace_ability3081(source_dir,source_trans,directory,trans,book,r,encoder=encode,decoder=decode):
    """Numeric slots1..4 in observed Block description; no other grammar adoption."""
    assert set(r)=={'key','source_text','text','control_policy'}
    assert r['key']==3081 and r['control_policy']=='ability3081_observed_numeric_slots_v1'
    assert digest(r['source_text'].encode('utf-8'))=='116ef308c3b4fd1828a6dad57baba7c329dd8f340c21159f1be7100c24b90e36'
    for value in [r['source_text'],r['text']]:
        assert isinstance(value,str) and value and '\0' not in value
        assert re.findall(r'\$[0-9A-Za-z]+',value)==['$1','$2','$3','$4']
        assert value.count('$')==4 and not any(c in value for c in '#%&*+:<=>\\^~[]{}\r\n\t')
        assert '$3-$4' in value
    encoded=encoder(r['text'],book).encode('utf-8')
    assert decoder(encoded.decode('utf-8'),book)==r['text']
    check_template(encoded.decode('utf-8'),'Ability3081')
    from numeric_limits053 import check_ability3081_expansion
    check_ability3081_expansion(encoded.decode('utf-8'))
    # These two captured scenarios are bounded checks, not a general maximum.
    for values in [('5%','5%','1.2','1.4'),('6%','5%','1.4','1.6')]:
        expanded=r['text']
        for n,value in enumerate(values,1):expanded=expanded.replace('$'+str(n),value)
        check_template(encoder(expanded,book),'Ability3081 observed rank expansion')
    return replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded)


def replace_guarded_trans_record(source_dir,source_trans,directory,trans,r,encoded):
    """Rebuild exact stream length and offsets; other records retain their raw payload."""
    assert len(encoded)<=65535
    assert len(source_dir)==len(directory) and len(directory)%20==0
    outdir,outtrans=bytearray(),bytearray();changes=[];expected=[]
    for pos in range(0,len(directory),20):
        old=struct.unpack_from('<IIIHHHH',source_dir,pos);current=list(struct.unpack_from('<IIIHHHH',directory,pos))
        assert old[:2]==tuple(current[:2]) and old[3]==current[3] and old[5:]==tuple(current[5:])
        raw=trans[current[2]:current[2]+current[4]];assert len(raw)==current[4]
        if current[0]==r['key']:
            original=source_trans[old[2]:old[2]+old[4]]
            assert original==r['source_text'].encode('utf-8') and raw==original
            raw=encoded;changes.append({'key':r['key'],'old_offset':old[2],'old_bytes':old[4],'source_sha256':digest(original),
                                        'new_bytes':len(raw),'diagnostic_text':r['text'],'diagnostic_encoded_hex':raw.hex(),
                                        'control_policy':r['control_policy'],'source_utf16_units':len(r['source_text'].encode('utf-16le'))//2})
        current[2]=len(outtrans);current[4]=len(raw)
        outdir.extend(struct.pack('<IIIHHHH',*current));outtrans.extend(raw);expected.append((current,raw))
    assert len(changes)==1
    for i,(fields,raw) in enumerate(expected):
        actual=struct.unpack_from('<IIIHHHH',outdir,i*20)
        assert actual==tuple(fields) and outtrans[actual[2]:actual[2]+actual[4]]==raw
    assert expected[-1][0][2]+expected[-1][0][4]==len(outtrans)
    return bytes(outdir),bytes(outtrans),changes

def rebuild_static(source,book,overrides,encoder=encode,decoder=decode):
    """Key/length records, preserving order, duplicates and all other raw bytes."""
    wanted={r['key']:r for r in overrides};assert len(wanted)==len(overrides)
    for r in overrides:
        from weapons_ac_20261020 import DRAFTS as WEAPONS_AC_KEYS,validate as validate_weapons_ac
        if r['key'] in WEAPONS_AC_KEYS:validate_weapons_ac(r,book,encoder,decoder)
        from weapons_dl_20261021 import DRAFTS as WEAPONS_DL_KEYS,validate as validate_weapons_dl
        if r['key'] in WEAPONS_DL_KEYS:validate_weapons_dl(r,book,encoder,decoder)
        from weapons_os_20261021 import DRAFTS as WEAPONS_OS_KEYS,validate as validate_weapons_os
        if r['key'] in WEAPONS_OS_KEYS:validate_weapons_os(r,book,encoder,decoder)
        from weapons_sz_20261021 import DRAFTS as WEAPONS_SZ_KEYS,validate as validate_weapons_sz
        if r['key'] in WEAPONS_SZ_KEYS:validate_weapons_sz(r,book,encoder,decoder)
        from named_jewelry_20261021 import DRAFTS as NAMED_JEWELRY_KEYS,validate as validate_named_jewelry
        if r['key'] in NAMED_JEWELRY_KEYS:validate_named_jewelry(r,book,encoder,decoder)
        from potion_names_20261021 import DRAFTS as POTION_NAME_KEYS,validate as validate_potion_name
        if r['key'] in POTION_NAME_KEYS:validate_potion_name(r,book,encoder,decoder)
        from item_affixes_20261021 import DRAFTS as ITEM_AFFIX_KEYS,FORMS as ITEM_FORM_KEYS,validate as validate_item_affix
        if r['key'] in ITEM_AFFIX_KEYS:validate_item_affix(r,book,encoder,decoder)
        from actor_variants_20261021 import DRAFTS as ACTOR_VARIANT_KEYS,validate as validate_actor_variant
        if r['key'] in ACTOR_VARIANT_KEYS:validate_actor_variant(r,book,encoder,decoder)
        from actor_named_20261021 import DRAFTS as ACTOR_NAMED_KEYS,validate as validate_actor_named
        if r['key'] in ACTOR_NAMED_KEYS:validate_actor_named(r,book,encoder,decoder)
        from stat_help_20261021 import DRAFTS as STAT_HELP_KEYS,validate as validate_stat_help
        if r['key'] in STAT_HELP_KEYS:validate_stat_help(r,book,encoder,decoder)
        from ui_direct_20261021 import DRAFTS as UI_DIRECT_KEYS,validate as validate_ui_direct
        if r['key'] in UI_DIRECT_KEYS:validate_ui_direct(r,book,encoder,decoder)
        from hud_errors_20261021 import DRAFTS as HUD_ERROR_KEYS,validate as validate_hud_error
        if r['key'] in HUD_ERROR_KEYS:validate_hud_error(r,book,encoder,decoder)
        from item_events_20261021 import DRAFTS as ITEM_EVENT_KEYS,validate as validate_item_event
        if r['key'] in ITEM_EVENT_KEYS:validate_item_event(r,book,encoder,decoder)
        from ui_wrappers_20261021 import DRAFTS as UI_WRAPPER_KEYS,validate as validate_ui_wrapper
        if r['key'] in UI_WRAPPER_KEYS:validate_ui_wrapper(r,book,encoder,decoder)
        from ui_confirmations_20261021 import DRAFTS as UI_CONFIRMATION_KEYS,LITERAL_KEY,validate as validate_ui_confirmation
        if r['key'] in UI_CONFIRMATION_KEYS:validate_ui_confirmation(r,book,encoder,decoder)
        from armor_unique_20261020 import DRAFTS as ARMOR_UNIQUE_KEYS,validate as validate_armor_unique
        if r['key'] in ARMOR_UNIQUE_KEYS:validate_armor_unique(r,book,encoder,decoder)
        from armor_sw_20261020 import DRAFTS as ARMOR_SW_KEYS,validate as validate_armor_sw
        if r['key'] in ARMOR_SW_KEYS:validate_armor_sw(r,book,encoder,decoder)
        from armor_ns_20261020 import DRAFTS as ARMOR_NS_KEYS,validate as validate_armor_ns
        if r['key'] in ARMOR_NS_KEYS:validate_armor_ns(r,book,encoder,decoder)
        from armor_gm_20261020 import DRAFTS as ARMOR_GM_KEYS,validate as validate_armor_gm
        if r['key'] in ARMOR_GM_KEYS:validate_armor_gm(r,book,encoder,decoder)
        from armor_cg_20261020 import DRAFTS as ARMOR_CG_KEYS,validate as validate_armor_cg
        if r['key'] in ARMOR_CG_KEYS:validate_armor_cg(r,book,encoder,decoder)
        from armor_ac_20261020 import DRAFTS as ARMOR_AC_KEYS,validate as validate_armor_ac
        if r['key'] in ARMOR_AC_KEYS:validate_armor_ac(r,book,encoder,decoder)
        from ability_titles_20261020 import DRAFTS as ABILITY_TITLE_KEYS,validate as validate_ability_title
        if r['key'] in ABILITY_TITLE_KEYS:validate_ability_title(r,book,encoder,decoder)
        from document_item_names_20261020 import DRAFTS as DOCUMENT_ITEM_KEYS,validate as validate_document_item
        if r['key'] in DOCUMENT_ITEM_KEYS:validate_document_item(r,book,encoder,decoder)
        if r['key'] in range(34,147):
            from map_name_policy import validate as validate_original_map_name
            validate_original_map_name(r,book,encoder,decoder)
        if r['key'] in {54,55,56,59,63,64,65}:
            from map_places421 import validate as validate_map_place
            validate_map_place(r,book,encoder,decoder)
        if r['key'] in {2263,3001,766,776}:
            from names432 import validate as validate_bound_name
            validate_bound_name(r,book,encoder,decoder)
        if r['key'] in {61,74,75,76,77,83,2523,3198}:
            from repair_names474 import validate as validate_repair_name
            validate_repair_name(r,book,encoder,decoder)
        if r['key'] in {69,68,67,3041}:
            from threat_names517 import validate as validate_threat_name
            validate_threat_name(r,book,encoder,decoder)
        assert set(r)=={'key','source_text','text'} and type(r['key']) is int
        assert isinstance(r['source_text'],str) and isinstance(r['text'],str)
        assert r['text'] and '\0' not in r['text']
        tokens=lambda s:re.findall(r'\[[^\]\r\n]*\]|\{[^}\r\n]*\}|\$[A-Za-z]',s)
        if r['key'] in ITEM_FORM_KEYS:
            # Exact source-bound authored forms validated above, including token multiplicity.
            pass
        elif r['key']==LITERAL_KEY:
            # Exact source/draft pair validated above; brackets are fixed literal delimiters.
            assert r['source_text']=='[ Equipped ]' and r['text']=='[ 장착 중 ]'
        else:assert tokens(r['source_text'])==tokens(r['text'])
    out=bytearray(source[:4]);pos=4;found={};changes=[];records=[]
    while pos<len(source):
        key,length=struct.unpack_from('<IH',source,pos);raw=source[pos+6:pos+6+length]
        assert len(raw)==length
        if key in wanted:
            r=wanted[key];assert raw==r['source_text'].encode('utf-8')
            final=encoder(r['text'],book).encode('utf-8')
            assert decoder(final.decode('utf-8'),book)==r['text']
            check_template(final.decode('utf-8'),f'Static diagnostic{key}')
            found[key]=found.get(key,0)+1
            changes.append({'key':key,'source_offset':pos+6,'source_bytes':length,
                            'source_sha256':digest(raw),'new_bytes':len(final),'new_sha256':digest(final),
                            'diagnostic_text':r['text'],'encoded_hex':final.hex(),'tokens_preserved':True,
                            **({'fixed_bracket_literal_interior_translated':True} if key==3748 else {})})
        else:final=raw
        assert len(final)<=65535
        records.append((key,raw,final));out.extend(struct.pack('<IH',key,len(final))+final)
        pos+=6+length
    assert pos==len(source) and found=={k:1 for k in wanted}
    # An independent walk checks every output boundary and untouched record.
    pos=4
    for key,raw,final in records:
        k,n=struct.unpack_from('<IH',out,pos);assert (k,n)==(key,len(final))
        assert out[pos+6:pos+6+n]==final
        if key not in wanted:assert out[pos+6:pos+6+n]==raw
        pos+=6+n
    assert pos==len(out) and out[:4]==source[:4]
    return bytes(out),changes

def build_prx(source):
    profile=Profile()
    audit=json.loads((ROOT/'qa/reports/profile_stage020_audit.json').read_text(encoding='utf-8'))
    assert audit['status']=='PASS_DOCUMENTED_PROFILE' and audit['profile_sha256']==digest(profile.path.read_bytes())
    folder=ROOT/'workspace/analysis/single_unit_020'
    assert struct.unpack_from('<H',source,16)[0]==0xffa0
    old_phoff=struct.unpack_from('<I',source,28)[0]
    assert struct.unpack_from('<H',source,44)[0]==2
    phdrs=[struct.unpack_from('<8I',source,old_phoff+i*32) for i in range(2)]
    end=max(p[2]+p[5] for p in phdrs)
    origin=(end+63)&~63
    asm=(ROOT/'config/single_unit_draw.asm').read_text(encoding='utf-8')
    hook=profile.assemble(asm,origin,folder,'hook')
    decoded=profile.verify_roundtrip(hook,origin,folder,'hook_roundtrip')
    boundaries={i['pc'] for i in decoded};edges=[]
    for index,ins in enumerate(decoded):
        name=ins['name'];fields=ins['fields'];pc=ins['pc']
        if name in ['beq','bne']:
            offset=fields['offset'];offset=offset-65536 if offset&32768 else offset
            target=pc+4+offset*4
            assert target in boundaries
            edges.append({'pc':pc,'target':target,'kind':name})
        if name in ['beq','bne','jr','jalr']:
            delay=decoded[index+1]
            assert delay['name'] in ['nop','addiu']
            assert delay['name']=='nop' or delay['fields']['rs']==29 and delay['fields']['rt'] in [8,29]
        assert name not in ['j','jal','eret','mfc0','mtc0']
    assert [i['fields'] for i in decoded if i['name']=='jalr']==[{'rd':31,'rs':20}]*2
    # Original call relocation is R_MIPS_26, read/write and relative segment0.
    assert source[0x1ee738:0x1ee740]==struct.pack('<II',0xc9560,4)
    call_before=source[0xc95e0:0xc95e4]
    assert call_before==profile.assemble('jal 0xc9268',0xc9560,folder,'call_before')
    call=profile.assemble(f'jal 0x{origin:x}',0xc9560,folder,'call_after')
    patches=[(0xc95e0,call),(0xc965c,profile.assemble('slti a2,a1,14675',0xc95dc,folder,'bound')),
             (0xc9308,profile.assemble('lui a0,0x4400',0xc9288,folder,'dimension'))]
    assert source[0xc965c:0xc9660]==bytes.fromhex('0001a628')
    assert source[0xc9308:0xc930c]==bytes.fromhex('8043043c')
    phoff=(len(source)+15)&~15
    hookoff=(phoff+3*32+63)&~63
    newph=struct.pack('<8I',1,hookoff,origin,0,len(hook),len(hook),5,64)
    result=bytearray(source)
    struct.pack_into('<I',result,28,phoff);struct.pack_into('<H',result,44,3)
    for offset,data in patches:result[offset:offset+len(data)]=data
    result.extend(b'\0'*(phoff-len(result)))
    result.extend(source[old_phoff:old_phoff+64]+newph)
    result.extend(b'\0'*(hookoff-len(result)));result.extend(hook)
    # Source layout, BSS, sections and every old byte are protected except these spans.
    spans=[(28,4),(44,2)]+[(off,len(data)) for off,data in patches]
    changed={i for a,n in spans for i in range(a,a+n)}
    assert all(a==b or i in changed for i,(a,b) in enumerate(zip(source,result)))
    assert result[phoff:phoff+64]==source[old_phoff:old_phoff+64]
    # Placement recheck at both a real prior load base and a distinct valid base.
    relocation_checks=[]
    for base in [0x08804000,0x08904000]:
        word=struct.unpack('<I',call)[0]
        relocated=(word&0xfc000000)|(((word&0x3ffffff)+(base>>2))&0x3ffffff)
        ins=profile.verify_roundtrip(struct.pack('<I',relocated),base+0xc9560,folder,f'call_live_{base:x}')[0]
        assert ((ins['word']&0x3ffffff)<<2)==base+origin
        live=profile.verify_roundtrip(hook,base+origin,folder,f'hook_live_{base:x}')
        assert [i['word'] for i in live]==[i['word'] for i in decoded]
        assert base+0xc9568-768==base+0xc9268
        relocation_checks.append({'module_base':base,'hook_pc':base+origin,'return_pc':base+0xc9568,'quad_pc':base+0xc9268})
    info={'hook_vma':origin,'hook_file_offset':hookoff,'hook_bytes':len(hook),'hook_sha256':digest(hook),
          'old_memory_end':end,'program_header_offset':phoff,'program_header_count':3,
          'source_instructions_moved':False,'old_load_segments_identical':True,
          'callsite_relative':0xc9560,'callsite_before':call_before.hex(),'callsite_after':call.hex(),
          'retained_relocation_file_offset':0x1ee738,'retained_relocation_info':4,
          'relative_branch_edges':edges,'all_delay_slots_checked':True,
          'return_paths':['ordinary tail-call original quad, original RA unchanged','virtual restores s0..s6/ra/f0/f2/sp, returns to original caller'],
          'preserved_extra_live_state':['s0..s6','sp','ra','f0','f2'],
          'placement_checks':relocation_checks,'profile_sha256':audit['profile_sha256'],
          'scope':'Generated hook and original quad/caller/selector only; no whole-game reference completeness claim'}
    save_json(folder/'prx_layout.json',info)
    return bytes(result),info

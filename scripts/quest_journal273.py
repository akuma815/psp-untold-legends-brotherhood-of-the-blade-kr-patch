"""Exact2286/2287 journal policy;literal hint brackets observed on native257."""
import json,re,unicodedata
from survey import ROOT,digest,save_json
from text_limits import check_template
from unicode_codec042 import encode_unicode,decode_unicode
from catalog_survey034 import lines
from audit_translation138 import resolve
POLICY='rescue2286_2287_observed_book_literals_v1'
FIELDS={2286:'8c262ff23e667a092580390aca52b6640847fb493e9a5ee48a257fb915a3704e',
        2287:'becd564215f072cdf6cb73be0b157af5d1c6322b9026308c852361f95bc51f57'}
def validate(r,book,encoder=encode_unicode,decoder=decode_unicode):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    assert digest(r['source_text'].encode('utf-8'))==FIELDS[r['key']]
    for text in [r['source_text'],r['text']]:
        assert isinstance(text,str) and text and text==unicodedata.normalize('NFC',text)
        assert not any(c in text for c in '\0\t{}$#%&*+:<=>\\^~')
        assert '\r' not in text.replace('\r\n','') and '\n' not in text.replace('\r\n','')
        if r['key']==2286:assert not any(c in text for c in '\r\n[]')
        else:
            parts=text.split('\r\n\r\n');assert len(parts)==2 and all(parts)
            assert not any(c in parts[0] for c in '[]\r\n')
            assert parts[1].startswith('[') and parts[1].endswith(']') and text.count('[')==text.count(']')==1
            assert not any(c in parts[1][1:-1] for c in '[]\r\n') and not re.search(r'\[(?:i_|r_|c_)',parts[1])
    encoded=encoder(r['text'],book).encode('utf-8');assert decoder(encoded.decode('utf-8'),book)==r['text']
    check_template(r['text'],f'RescueBook{r["key"]};273 observed English source/2047 decoder bound;Korean layout pending')
    assert len(encoded)<=65535
    return encoded
def main():
    b=ROOT/'workspace/translation';es={e['id']:e for e in lines(b/'entries.jsonl')}
    ss={s['key']:s for s in lines(b/'baseline/source_entries.jsonl') if s['bank']=='trans'}
    ds={d['id']:d for p in [b/'diagnostic_decisions.jsonl',*b.glob('decisions_*.jsonl')] for d in lines(p)}
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();import struct
    assert struct.unpack_from('<I',db,342680+46*56+24)[0]==2287 and struct.unpack_from('<I',db,342680+46*56+40)[0]==2286
    rows=[];book={'mapping':{c:None for c in range(0xac00,0xd7a4)}}
    for key in FIELDS:
        s=ss[key];e=es[s['id']];did=e['development_diagnostic_selection'] or e.get('current_working_decision') or e['decision_ids'][-1]
        r=dict(key=key,source_text=s['source_text'],text=resolve(ds[did]),control_policy=POLICY);validate(r,book);rows.append(r)
    from copy import deepcopy
    bad=[]
    for field,value in [('key',999999),('control_policy','unobserved'),('source_text',rows[1]['source_text']+'x'),('text',rows[1]['text']+'$x'),
                        ('text',rows[1]['text'].replace(']','')),('text',rows[1]['text'].replace('\r\n','\n')),
                        ('text',rows[1]['text']+'\0'),('text',rows[1]['text']+'😀')]:
        r=deepcopy(rows[1]);r[field]=value;bad.append(r)
    for r in bad:
        try:validate(r,book)
        except (AssertionError,ValueError):pass
        else:raise AssertionError('Unsafe variant accepted')
    save_json(ROOT/'qa/reports/quest_stage273_policy.json',dict(status='PASS_273_EXACT_SOURCE_LITERAL_STRUCTURE_CODEC',keys=list(FIELDS),
        source_table15_row=46,changed_working_wordings=0,rejected_protected_input_variants=len(bad),native_original_literal_evidence='qa/reports/quest_stage272_source_runtime.json',
        human_approved=False,Korean_layout_pending=True,release_eligible=False))
    print('PASS273 exact2 journal entries;8 protected-input rejections;no wording or approval edits')
if __name__=='__main__':main()


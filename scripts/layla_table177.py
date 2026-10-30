"""Only two early row9 records; exact immutable source and portrait/paragraph policy."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

FIELDS={2274:36,2283:7}
POLICY='layla_table13_row9_early_portrait_v1'
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    offset,count=struct.unpack_from('<II',db,104);assert count==18
    row=struct.unpack_from('<65I',db,offset+9*260)
    assert row[0]==0xe2f77b6e and row[FIELDS[r['key']]]==r['key']
    source=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    assert r['source_text']==source['source_text']
    raw=(ROOT/'extracted/disc'/source['source_path']).read_bytes()[source['offset']:source['offset']+source['byte_length']]
    assert raw==r['source_text'].encode('utf8') and digest(raw)==source['source_sha256']
    tag={2274:'[i_PI_LaylaGoodmorrowConcerned]',2283:'[i_PI_LaylaGoodmorrow]'}[r['key']]
    assert r['source_text'].startswith(tag)
    text=r['text'];assert text==unicodedata.normalize('NFC',text) and text.startswith(tag)
    body=text[len(tag):];assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',r['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text
    check_template(text,'Layla early row9;common-wrapper capacity only;individual display pending')
    return encoded

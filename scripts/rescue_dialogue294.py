"""Source-backed two quest dialogue policies; portraits/paragraphs unchanged."""
import re,struct,unicodedata
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template
FIELDS={2291:(78,3,2,'PI_GoodKaylee'),2292:(77,0,7,'PI_DeanLysetta')}
POLICY='rescue_two_quest_dialogues_source292_queue293_v1'
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    row,index,kind,portrait=FIELDS[r['key']]
    assert struct.unpack_from('<h',db,340700+42*44+0x12+index*2)[0]==row
    assert struct.unpack_from('<I',db,342680+row*56+0x20)[0]==r['key'] and db[342680+row*56+0x34]==kind
    s=next(s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='trans' and s['key']==r['key'])
    raw=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']]
    assert r['source_text']==s['source_text'] and raw==r['source_text'].encode('utf8') and digest(raw)==s['source_sha256']
    tag='[i_'+portrait+']';text=r['text'];assert text.startswith(tag) and text==unicodedata.normalize('NFC',text)
    body=text[len(tag):];assert body and not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',r['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text and len(encoded)<=65535
    check_template(text,'RescueDialogue exact292/293 source portraits and normal quest queue;2047 common wrapper bound;Korean layout separately verified')
    return encoded

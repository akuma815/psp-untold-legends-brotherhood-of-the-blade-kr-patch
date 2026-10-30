"""Strict source-bound plain portrait policy for seven mapped Alice records."""
import re,struct,unicodedata
from survey import ROOT,digest
from text_limits import check_template

FIELDS={2329:1,2328:2,2338:3,2339:4,2279:7,2294:37,2307:39}
POLICY='alice_table13_row1_plain_portrait_v1'
def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in FIELDS and r['control_policy']==POLICY
    data=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes()
    assert digest(data)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    offset,count=struct.unpack_from('<II',data,13*8);assert count==18
    row=struct.unpack_from('<65I',data,offset+260);assert row[0]==0xe78cc3a6 and row[FIELDS[r['key']]]==r['key']
    tags=re.findall(r'\[i_[^\]\r\n]+\]',r['source_text']);assert len(tags)==1 and tags[0] in ['[i_PI_AliceMcKyntire]','[i_PI_AliceMcKyntireConcerned]']
    text=r['text'];assert text==unicodedata.normalize('NFC',text) and text.startswith(tags[0]) and len(text)>len(tags[0])
    body=text[len(tags[0]):]
    assert not any(c in body for c in '\0\t[]{}$#%&*+:<=>\\^~')
    assert re.findall(r'\r\n+',text)==re.findall(r'\r\n+',r['source_text'])
    assert '\r' not in body.replace('\r\n','') and '\n' not in body.replace('\r\n','')
    encoded=encoder(text,book).encode('utf8');assert decoder(encoded.decode('utf8'),book)==text
    check_template(text,'Mapped Alice row1 plain portrait;necessary common-wrapper guard,per-key layout pending')
    return encoded

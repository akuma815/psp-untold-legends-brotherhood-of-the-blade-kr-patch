"""Mechanical item-context guards for explicitly authored source-bound armor names."""
import re,struct,unicodedata,copy
from functools import lru_cache
from collections import defaultdict,Counter
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

class ArmorNames:
    def __init__(self,drafts,start,end,label,notes,allowed_categories=(4,5,6,7,8,9),expected_reference_counts=None):
        self.drafts=drafts;self.start=start;self.end=end;self.label=label;self.notes=notes;self.allowed_categories=tuple(allowed_categories);self.expected_reference_counts=expected_reference_counts or {}
    @lru_cache(maxsize=1)
    def population(self):
        db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
        off,n=struct.unpack_from('<II',db,40);assert (off,n)==(35748,2088);ss={s['key']:s for s in lines(ROOT/'workspace/translation/baseline/source_entries.jsonl') if s['bank']=='static'}
        counts=Counter(struct.unpack_from('<H',db,off+row*84)[0] for row in range(self.start,self.end));keys=set(counts)
        assert keys==set(self.drafts) and set(self.expected_reference_counts)<=keys
        assert all(counts[k]==self.expected_reference_counts.get(k,1) for k in keys)
        refs=defaultdict(list)
        for row in range(n):
            raw=db[off+row*84:off+(row+1)*84];k=struct.unpack_from('<H',raw)[0]
            if k in keys:
                assert raw[59] in self.allowed_categories
                refs[k].append(dict(table=5,row=row,field=0,width=2,stride=84,offset=off+row*84,complete_row_hex=raw.hex(),category=raw[59],effect_id=struct.unpack_from('<I',raw,32)[0]))
        assert set(refs)==keys and all(len(refs[k])==counts[k] for k in keys)
        return {k:dict(source=ss[k],references=v) for k,v in refs.items()}
    @lru_cache(maxsize=1)
    def context(self):
        from armor_ac_20261020 import context
        c=copy.deepcopy(context());c['cohort']=f'{self.label}, originaltable5rows{self.start}..{self.end-1}, complete source rows/classes, individually authored full names; no source-record merge.'
        c['semantic_notes']+=self.notes;return c
    def validate(self,r,book,encoder,decoder):
        assert set(r)=={'key','source_text','text'} and r['key'] in self.drafts;s=self.population()[r['key']]['source']
        b=(ROOT/'extracted/disc'/s['source_path']).read_bytes()[s['offset']:s['offset']+s['byte_length']];assert r['source_text']==s['source_text'] and b.hex()==s['source_hex'] and digest(b)==s['source_sha256']
        text=r['text'];assert text and text==unicodedata.normalize('NFC',text) and not any(c in text for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
        assert re.findall(r'\d+',text)==re.findall(r'\d+',s['source_text']);enc=encoder(text,book).encode('utf8');assert len(enc)+1<=250 and decoder(enc.decode('utf8'),book)==text
        check_template(text,'Original base item-name ownedUTF8slot250; composed-title geometry pending');return enc
    def negative_cases(self):
        k=next(iter(self.drafts));r=dict(key=k,source_text=self.population()[k]['source']['source_text'],text=self.drafts[k])
        return r,[('source',dict(source_text='wrong')),('outside_scope',dict(key=0)),('control',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'\u2603')),('owned_slot_overflow',dict(text='가'*84))]

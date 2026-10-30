"""Conditional common-key name lookup, source-bound proposals; no DB/code edits."""
import argparse,struct,unicodedata
from functools import lru_cache
from survey import ROOT,digest
from catalog_survey034 import lines
from text_limits import check_template

POLICY='common_key_trans_name_fallback_plain_250_v1'
DRAFTS={3929:'현자',3930:'조언자의 결계',3931:'대소용돌이',3933:'후려치는 자',3935:'아르콘',3936:'박학자',3937:'분노의 주먹',
        3003:'네크로시스 고서',3004:'맷 테스트 몬스터',3002:'즈라 장군',3009:'고르진 모독자',3010:'고르진 타락자',3011:'고르진 약탈자',3005:'맷 테스트 주문'}
EXPECTED={3929:(5,1878,0,2),3930:(5,1879,0,2),3931:(5,1880,0,2),3933:(5,1882,0,2),3935:(5,1884,0,2),3936:(5,1886,0,2),3937:(5,1887,0,2),
          3003:(5,2065,0,2),3004:(2,74,0,2),2726:(2,142,0,2),3002:(2,151,0,2),3009:(2,152,0,2),3010:(2,153,0,2),3011:(2,154,0,2),2801:(2,184,0,2),2836:(2,185,0,2),3005:(12,59,60,4)}
FIELDS={k:[EXPECTED[k][:3]] for k in DRAFTS}

@lru_cache(maxsize=1)
def population():
    db=(ROOT/'extracted/disc/PSP_GAME/USRDIR/res/gam_db_T4').read_bytes();assert digest(db)=='d852979a6a7b1166dc433281dae61b96494e359dee25d732698726959d0eaca2'
    ss=lines(ROOT/'workspace/translation/baseline/source_entries.jsonl');static={s['key'] for s in ss if s['bank']=='static'};trans={s['key']:s for s in ss if s['bank']=='trans'}
    found={};rows=[]
    for table,stride,field,width in [(5,84,0,2),(2,112,0,2),(12,92,60,4)]:
        off,n=struct.unpack_from('<II',db,table*8)
        for row in range(n):
            raw=db[off+row*stride:off+(row+1)*stride];k=int.from_bytes(raw[field:field+width],'little')
            if k in static or k not in trans:continue
            assert k not in found;found[k]=(table,row,field,width)
            rows.append(dict(key=k,table=table,row=row,field=field,width=width,stride=stride,offset=off+row*stride,complete_row_hex=raw.hex(),source=trans[k]))
    assert found==EXPECTED
    return rows

@lru_cache(maxsize=1)
def sources():
    src={r['key']:r['source'] for r in population() if r['key'] in DRAFTS};raw=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_trans.dat').read_bytes()
    directory=(ROOT/'extracted/disc/PSP_GAME/USRDIR/locale/en_us_dir.dat').read_bytes();keys={}
    for off in range(0,len(directory),20):
        r=struct.unpack_from('<IIIHHHH',directory,off);assert r[0] not in keys;keys[r[0]]=r
    for k,s in src.items():
        b=raw[s['offset']:s['offset']+s['byte_length']];assert b.hex()==s['source_hex'] and digest(b)==s['source_sha256'] and b==s['source_text'].encode('utf8')
        r=keys[k];assert r[2]==s['offset'] and r[4]==s['byte_length']
    return src

@lru_cache(maxsize=1)
def context():
    from allegrex_profile import Profile
    boot=(ROOT/'extracted/disc/PSP_GAME/SYSDIR/BOOT.BIN').read_bytes();assert digest(boot)=='b603934d7d1a938ae4d3f6cfdac83ef96cdbf12489f673f4079666eae447d1d1'
    calls={0xda684:0xd6d74,0xd6e08:0xdb20c,0xdb214:0xdb228,0xdb30c:0xdc548,0xdc55c:0xdc014,0xdc578:0xdc5c4,0xdc614:0xfa600,0xdc47c:0xfa404,0xfa414:0xfa7a0}
    for pc,target in calls.items():assert struct.unpack_from('<I',boot,pc+128)[0]==0x0c000000|(target>>2),(hex(pc),hex(target))
    for at,text in [(0x13e7e0,b'%s/%s_dir.dat\0'),(0x13e7f0,b'%s/%s_eng.dat\0'),(0x13e800,b'%s/%s_trans.dat\0')]:assert boot[at+128:at+128+len(text)]==text
    q=ROOT/'qa/static/20261021_common_key_fallback';q.mkdir(parents=True,exist_ok=True);p=Profile();windows=[]
    for name,a,z in [('wide_lookup',0xda634,0xda740),('formatter_lookup',0xd6d74,0xd6ecc),('cache_and_directory',0xdb20c,0xdb3a0),('directory_search',0xdc014,0xdc41c),('open_locale_files',0xdc41c,0xdc548),('trans_offset_length_read',0xdc548,0xdc6c0),('path_wrappers',0xfa3bc,0xfa428),('seek_read_terminate',0xfa600,0xfa6ac)]:
        raw=boot[a+128:z+128];d=p.verify_roundtrip(raw,a,q,name);windows.append(dict(name=name,start=hex(a),end_exclusive=hex(z),sha256=digest(raw),instructions=len(d)))
    return dict(complete_source_rows=population(),source_roundtrip_windows=windows,call_targets={hex(k):hex(v) for k,v in calls.items()},
        consumer_chain=['Known item/actor/ability name consumers reach DA634 -> D6D74 -> DB20C/DB228.',
        'DB228 checks enabled caches +4 then +0. Both misses select direct offset maps or DC548 directory lookup. Cache bank identity is not asserted.',
        'DC41C opens FA404 %s/%s_trans.dat into object+1C. DC548 obtains dir record via DC014, reads u32+8 trans offset/u16+E length, calls DC5C4.',
        'DC5C4 -> FA600 reads object+1C at exact offset/length and NUL terminates; DA634 converts formatted UTF8 to caller wide buffer.'],
        limitations=['Conditional source route, not evidence of a cache miss or bank choice during natural gameplay. No DB repair, duplicate static keys, runtime hook, or bank merge.',
        '14 manually authored names; 3 previously selected names unchanged. Debug names retain test meaning; Zsraah phonetics and all new terms provisional.',
        'Necrosis Tome matches existing trans3650 body 네크로시스 고서. No inferred acquisition, speaker identity, class/rank availability or layout QA.',
        'All proposed payloads conservatively <=250 UTF8 bytes including NUL and below2048 wide capacity.'])

def validate(r,book,encoder,decoder):
    assert set(r)=={'key','source_text','text','control_policy'} and r['key'] in DRAFTS and r['control_policy']==POLICY
    assert r['source_text']==sources()[r['key']]['source_text'];t=r['text']
    assert t and t==unicodedata.normalize('NFC',t) and not any(c in t for c in '\0\r\n\t[]{}$#%&*+:<=>\\^~')
    b=encoder(t,book).encode('utf8');assert len(b)+1<=250 and decoder(b.decode('utf8'),book)==t
    check_template(t,'Conditional common-key name lookup2048wide; item owned slot250 conservative bound')
    return b

def negative_cases(drafts):
    k=3003;r=dict(key=k,source_text=sources()[k]['source_text'],text=drafts[k],control_policy=POLICY)
    return r,[('wrong_source',dict(source_text='wrong')),('outside_scope',dict(key=617)),('tag',dict(text=r['text']+'[p]')),('NUL',dict(text=r['text']+'\0')),('unmapped',dict(text=r['text']+'☃')),('overflow',dict(text='가'*250))]

SPEC=dict(name='fallback_names_20261021',date='20261021',config='development_fallback_names_20261021.json',prior_name='weapons_ac_20261020',prior_config='development_weapons_ac_20261020.json',
          prior_config_sha256='80d7151917aef1c9da7e9037d8d5cdc696bdd79471a12d88333f9c3b797c4640',prior_artifact_sha256='352ea5c478553c15c08ef1806f8530acecb6da7ddfe6db0c97e11f5d0a135001',
          prior_decisions=2962,expected_decisions=2976,expected_states=dict(untranslated=1319,needs_human_review=2550,in_progress=104))
if __name__=='__main__':
    import quest_batch_pipeline as pipeline
    import sys
    policy=sys.modules[__name__];p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','apply','audit']);a=p.parse_args()
    if a.action=='preflight':pipeline.preflight(SPEC,policy,DRAFTS,{},context()['limitations'])
    elif a.action=='apply':pipeline.apply(SPEC,policy,DRAFTS,{},{},[])
    else:pipeline.audit(SPEC,policy,DRAFTS,{})

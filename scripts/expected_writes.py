"""Apply declared immutable-source range writes or one exact file replacement."""
import hashlib

def sha(data):return hashlib.sha256(data).hexdigest()

def apply_owned_writes(source,writes):
    writes=sorted(writes,key=lambda w:w['offset'])
    assert writes
    for w in writes:
        assert 0<=w['offset']<=len(source) and len(w['data'])==w['size']
        assert sha(source[w['offset']:w['offset']+w['expected_size']])==w['expected_sha256']
        assert sha(w['data'])==w['final_sha256']
    if any(w.get('kind')=='replace_file' for w in writes):
        assert len(writes)==1
        w=writes[0]
        assert w['offset']==0 and w['expected_size']==len(source)
        return bytes(w['data'])
    assert all('kind' not in w for w in writes)
    assert all(a['offset']+a['size']<=b['offset'] for a,b in zip(writes,writes[1:]))
    result=bytearray(source);cursor=0
    for w in writes:
        assert result[cursor:w['offset']]==source[cursor:w['offset']]
        result[w['offset']:w['offset']+w['size']]=w['data']
        assert sha(result[w['offset']:w['offset']+w['size']])==w['final_sha256']
        cursor=w['offset']+w['size']
    assert result[cursor:]==source[cursor:] and len(result)==max(len(source),cursor)
    return bytes(result)

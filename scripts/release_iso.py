"""Registered PSP ISO layout growth: preserve directories, path tables and gaps."""
import hashlib,struct
from pathlib import Path

BLOCK=2048
SOURCE_SIZE=407601152
SOURCE_SHA='27bdf09512f138ed40f76f4c575fd9d373a95026355e6c8d97e300c2d4a0c621'
def sha(b):return hashlib.sha256(b).hexdigest()
def check(ok,message):
    if not ok:raise ValueError('ISO 검증 실패: '+message)
def number(b,at):
    a=struct.unpack_from('<I',b,at)[0];z=struct.unpack_from('>I',b,at+4)[0];check(a==z,'양방향 정수');return a
def put_number(b,at,value):struct.pack_into('<I',b,at,value);struct.pack_into('>I',b,at+4,value)
def parse(raw):
    check(len(raw)%BLOCK==0,'섹터 정렬')
    pvd=16*BLOCK
    check(raw[pvd:pvd+7]==b'\x01CD001\x01' and raw[17*BLOCK:17*BLOCK+7]==b'\xffCD001\x01','볼륨 기술자')
    check(struct.unpack_from('<H',raw,pvd+128)[0]==struct.unpack_from('>H',raw,pvd+130)[0]==BLOCK,'블록 크기')
    check(number(raw,pvd+80)*BLOCK==len(raw),'볼륨 크기')
    files={};dirs=[];visited=set()
    def walk(rec,name):
        lba,n=number(rec,2),number(rec,10);check(lba not in visited and lba*BLOCK+n<=len(raw),'디렉터리 범위')
        visited.add(lba);dirs.append((name,lba,n));base=lba*BLOCK;b=raw[base:base+n];pos=0
        while pos<n:
            size=b[pos]
            if not size:pos=(pos//BLOCK+1)*BLOCK;continue
            at=pos;r=b[pos:pos+size];pos+=size
            check(size>=34 and len(r)==size and 33+r[32]<=size,'디렉터리 레코드')
            token=r[33:33+r[32]]
            if token in [b'\0',b'\1']:continue
            token=token.decode('ascii').removesuffix(';1');check(token and token not in ['.','..'] and not any(c in token for c in '/\\:'),'이름')
            path=name+'/'+token if name else token;check(not r[25]&128,'분할 레코드')
            if r[25]&2:walk(r,path)
            else:
                off=number(r,2)*BLOCK;length=number(r,10);check(path not in files and off+length<=len(raw),'파일 범위')
                files[path]=dict(lba=off//BLOCK,size=length,record_offset=base+at)
    walk(raw[pvd+156:pvd+190],'')
    first=min(v['lba'] for v in files.values())*BLOCK
    check(all(lba*BLOCK+n<=first for _,lba,n in dirs),'디렉터리는 데이터 앞에 유지')
    spans=sorted((v['lba']*BLOCK,((v['size']+BLOCK-1)//BLOCK)*BLOCK,n) for n,v in files.items())
    check(all(a+s<=z for (a,s,_),(z,_,_) in zip(spans,spans[1:])),'파일 할당 범위 중복')
    # All four source path-table copies reference unchanged directory extents.
    path_size=number(raw,pvd+132);tables=[]
    for pos,endian in [(140,'<'),(144,'<'),(148,'>'),(152,'>')]:
        lba=struct.unpack_from(endian+'I',raw,pvd+pos)[0]
        if not lba:continue
        check(lba*BLOCK+path_size<=first,'경로 테이블 범위');block=raw[lba*BLOCK:lba*BLOCK+path_size];at=0;rows=[]
        while at<len(block):
            length=block[at];check(length>0 and at+8+length<=len(block),'경로 테이블 레코드')
            extent=struct.unpack_from(endian+'I',block,at+2)[0];parent=struct.unpack_from(endian+'H',block,at+6)[0]
            rows.append((block[at+8:at+8+length],extent,parent));at+=8+length+(length&1)
        check(at==len(block) and {x[1] for x in rows}=={x[1] for x in dirs},'경로 테이블 디렉터리')
        tables.append(rows)
    check(len(tables)==4 and all(t==tables[0] for t in tables),'경로 테이블 사본')
    return files,dirs
def subtract(a,b,writers):
    p=a
    for x,y in writers:
        if y<=p:continue
        if x>=b:break
        if x>p:yield p,min(x,b)
        p=max(p,y)
        if p>=b:return
    if p<b:yield p,b
def build(source_iso,game_folder,output,source_files,target_files):
    check(not output.exists(),'기존 출력 거부');raw=source_iso.read_bytes()
    check(dict(size=len(raw),sha256=sha(raw))==dict(size=SOURCE_SIZE,sha256=SOURCE_SHA),'등록 원본 ISO')
    files,dirs=parse(raw);check(set(files)==set(source_files)==set(target_files),'80파일 구성')
    for n,v in files.items():
        payload=memoryview(raw)[v['lba']*BLOCK:v['lba']*BLOCK+v['size']]
        check(dict(size=len(payload),sha256=sha(payload))==source_files[n],'원본 파일 '+n)
    changed={n for n in files if source_files[n]!=target_files[n]};check(len(changed)==11,'변경 파일 개수')
    insertions=[]
    for n in changed:
        v=files[n];old_blocks=(v['size']+BLOCK-1)//BLOCK;new_blocks=(target_files[n]['size']+BLOCK-1)//BLOCK
        if new_blocks>old_blocks:insertions.append(((v['lba']+old_blocks)*BLOCK,(new_blocks-old_blocks)*BLOCK))
    insertions.sort();mapping=[];cursor=shift=0
    with output.open('xb') as out:
        for at,size in insertions:
            check(cursor<=at<=len(raw),'삽입 위치');out.write(memoryview(raw)[cursor:at]);mapping.append((cursor,at,cursor+shift))
            out.write(b'\0'*size);shift+=size;cursor=at
        out.write(memoryview(raw)[cursor:]);mapping.append((cursor,len(raw),cursor+shift))
    new_size=len(raw)+shift;metadata=bytearray(raw[:min(v['lba'] for v in files.values())*BLOCK]);writers=[(16*BLOCK+80,16*BLOCK+88)]
    put_number(metadata,16*BLOCK+80,new_size//BLOCK);placements={}
    with output.open('r+b') as out:
        for n,v in files.items():
            before=sum(size for at,size in insertions if at<=v['lba']*BLOCK);lba=v['lba']+before//BLOCK;at=v['record_offset']
            put_number(metadata,at+2,lba);put_number(metadata,at+10,target_files[n]['size']);writers.append((at+2,at+18))
            placements[n]=dict(lba=lba,size=target_files[n]['size'])
            if n in changed:
                payload=(game_folder/n).read_bytes();check(dict(size=len(payload),sha256=sha(payload))==target_files[n],'한글 파일 '+n)
                start=lba*BLOCK;out.seek(start);out.write(payload);writers.append((start,start+len(payload)));del payload
        out.seek(0);out.write(metadata)
    result=output.read_bytes();check(len(result)==new_size,'최종 ISO 크기');new_files,new_dirs=parse(result)
    check(new_dirs==dirs,'디렉터리 위치/크기 보존')
    for n,v in new_files.items():
        check(dict(lba=v['lba'],size=v['size'])==placements[n],'중복 파일 주소 '+n)
        b=memoryview(result)[v['lba']*BLOCK:v['lba']*BLOCK+v['size']];check(dict(size=len(b),sha256=sha(b))==target_files[n],'결과 파일 '+n)
    writers.sort();check(all(b<=c for (a,b),(c,d) in zip(writers,writers[1:])),'쓰기 범위 중복')
    preserved=0
    for a,b,target_at in mapping:
        for x,y in subtract(target_at,target_at+b-a,writers):
            source_at=a+x-target_at;check(result[x:y]==raw[source_at:source_at+y-x],'쓰기 밖의 원본/여백');preserved+=y-x
    running=0
    for at,n in insertions:
        start=at+running
        for x,y in subtract(start,start+n,writers):check(not any(result[x:y]),'새 정렬 여백')
        running+=n
    check(dict(size=source_iso.stat().st_size,sha256=sha(source_iso.read_bytes()))==dict(size=SOURCE_SIZE,sha256=SOURCE_SHA),'적용 중 원본 변경')
    return dict(status='PASS_SOURCE_LAYOUT_PSP_ISO',size=new_size,sha256=sha(result),files=80,
        changed_files=11,inserted_sectors=shift//BLOCK,directories_unchanged=len(dirs),path_table_copies_verified=4,
        original_bytes_preserved_outside_writers=preserved,ISO_output=True,source_unchanged=True)

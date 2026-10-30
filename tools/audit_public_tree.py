"""Audit the explicit publication set, not ignored local game or QA material."""
import ast,hashlib,json,re,subprocess,sys
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parent.parent
DENY={'.iso','.cso','.chd','.bin','.wad','.rsc','.dat','.prx','.sfo','.ppst','.sav','.exe','.dll','.zip','.xdelta','.vcdiff','.pgf','.pbp','.elf'}
SECRET=[re.compile(r'gh[opusr]_[A-Za-z0-9]{20,}'),re.compile(r'github_pat_[A-Za-z0-9_]{30,}'),re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
def main():
    m=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text(encoding='utf8'));names=[r['path'] for r in m['files']]+['SOURCE_MANIFEST.json'];problems=[]
    if (ROOT/'.git').exists():
        tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf8').split('\0');tracked=[n for n in tracked if n]
        if tracked and set(tracked)!=set(names):problems.append(dict(type='tracked_set_differs_from_manifest',extra=sorted(set(tracked)-set(names)),missing=sorted(set(names)-set(tracked))))
    for n in names:
        p=ROOT/n
        if p.suffix.lower() in DENY:problems.append(dict(type='forbidden_extension',path=n))
        if n.startswith(('original/','extracted/','build/','qa/','backups/','.github/workflows/')):problems.append(dict(type='forbidden_location',path=n))
        if p.stat().st_size>=50*2**20:problems.append(dict(type='oversize',path=n))
        if p.suffix.lower() in ['.png','.ttf']:
            if not (n.startswith('img/') or n.startswith('inputs/pinned/workspace/graphics/') or n.startswith('inputs/pinned/workspace/font/')):problems.append(dict(type='unexpected_binary',path=n))
            continue
        s=p.read_text(encoding='utf-8-sig')
        if '\ufffd' in s:problems.append(dict(type='replacement_character',path=n))
        if any(pattern.search(s) for pattern in SECRET):problems.append(dict(type='credential_pattern',path=n))
        if p.suffix=='.py':
            try:ast.parse(s,filename=n)
            except SyntaxError as e:problems.append(dict(type='python_syntax',path=n,line=e.lineno))
        if p.suffix=='.md':
            links=re.findall(r'\]\(([^)]+)\)',s)+re.findall(r'<img[^>]+src="([^"]+)"',s)
            for link in links:
                link=link.strip('<>').split('#')[0]
                if not link or '://' in link or link.startswith('mailto:'):continue
                if not (p.parent/unquote(link)).exists():problems.append(dict(type='broken_document_link',path=n,target=link))
    print(json.dumps(dict(status='PASS_PUBLICATION_AUDIT' if not problems else 'FAIL_PUBLICATION_AUDIT',files=len(names),problems=problems,
        no_release_workflows=True,no_game_image_save_or_executable_files=True,full_game_build_verified=False)))
    return 0 if not problems else 1
if __name__=='__main__':sys.exit(main())

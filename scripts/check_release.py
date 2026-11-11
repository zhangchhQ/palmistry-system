"""Check the exact Git candidate set; print paths/hashes, never matched secret text."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.py','.json','.md','.toml','.yaml','.yml'}
ALLOWED_DOTFILES = {'.gitignore'}
FORBIDDEN_PARTS = {'private','local-data','reports','source','work','node_modules','.venv'}
PATTERNS = [
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'gh[pousr]_[A-Za-z0-9]{25,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(r'sk-proj-[A-Za-z0-9_-]{20,}'),
    re.compile(r'/Users/[\w.-]+/|wxid_[A-Za-z0-9]{6,}'),
]


def inspect():
    process=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT,check=True,capture_output=True)
    names=sorted(set(x.decode() for x in process.stdout.split(b'\0') if x))
    manifest, violations=[],[]
    for name in names:
        relative=Path(name)
        path=ROOT/relative
        if relative.is_absolute() or '..' in relative.parts or path.is_symlink() or not path.is_file():
            violations.append({'path':name,'reason':'非仓库普通文件'})
            continue
        if relative.suffix not in ALLOWED_SUFFIXES and name not in ALLOWED_DOTFILES:
            violations.append({'path':name,'reason':'不在文本发布类型范围'})
            continue
        if FORBIDDEN_PARTS.intersection(relative.parts):
            violations.append({'path':name,'reason':'本地资料/生成物路径'})
        raw=path.read_bytes()
        try:
            text=raw.decode('utf-8')
        except UnicodeError:
            violations.append({'path':name,'reason':'非UTF-8文本'})
            continue
        for number,line in enumerate(text.splitlines(),1):
            if any(pattern.search(line) for pattern in PATTERNS):
                violations.append({'path':name,'line':number,'reason':'疑似凭据或本机私人路径，须复核'})
        manifest.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    return {'status':'PASS' if not violations else 'FAIL','file_count':len(manifest),
            'scope':'当前Git候选文件、类型、路径和所列秘密模式；不能证明不存在所有形式的隐私',
            'files':manifest,'violations':violations}


if __name__=='__main__':
    result=inspect()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    sys.exit(0 if result['status']=='PASS' else 1)

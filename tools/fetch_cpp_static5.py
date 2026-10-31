"""Fetch only the two hash-pinned organizer tools needed for C++ line counts."""
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/static-tools'
OUT.mkdir(parents=True,exist_ok=True)
ASSETS=[
 ('scc','https://github.com/boyter/scc/releases/download/v4.1.0/scc_Linux_x86_64.tar.gz','c7328436d3027f4357d3d7853f7dc3ac2bbcb4ca08f1adad91a27c593884079b'),
 ('clang-format','https://files.pythonhosted.org/packages/11/d1/658d3da4dcbca98620956868c7cf6f4ba19fccecbdfc30cc055e19c9d4a7/clang_format-23.1.3-py2.py3-none-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl','58bf1804216501669832a39f2415e14284337438a062ff564729792adec664ac')]
for name,url,expected in ASSETS:
    request=urllib.request.Request(url,headers={'User-Agent':'CodeScythe-local-validation/1.0'})
    with urllib.request.urlopen(request,timeout=45) as response: raw=response.read()
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected: raise RuntimeError(f'{name}: asset digest mismatch {actual}')
    if name=='scc':
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive: binary=archive.extractfile('scc').read()
    else:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive: binary=archive.read('clang_format/data/bin/clang-format')
    (OUT/name).write_bytes(binary)
    print(name,'verified organizer-pinned download',len(binary),flush=True)

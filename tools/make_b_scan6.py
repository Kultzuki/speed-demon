from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'research/prototypes/continuation6-profile-b.cpp').read_text()
variants = {}
# tokenize only: no key, hash or lookup
s = src.replace('        if (len > MAX_TERM) continue;\n        Key k;',
                '        if (len > MAX_TERM) continue;\n        emit(NONE);\n        continue;\n        Key k;')
variants['scan-classify'] = s
# key + hash + prefetch, no table lookup
s = src.replace('if (n > LAG) emit(terms.find(keys[slot], hashes[slot]));', 'if (n > LAG) emit(NONE);')
s = s.replace('for (size_t i = n > LAG ? n - LAG : 0; i < n; ++i) emit(terms.find(keys[i % LAG], hashes[i % LAG]));',
              'for (size_t i = n > LAG ? n - LAG : 0; i < n; ++i) emit(NONE);')
variants['scan-hash'] = s
# full lookup but no posting work
s = src.replace('if (n > LAG) emit(terms.find(keys[slot], hashes[slot]));',
                'if (n > LAG) { (void)terms.find(keys[slot], hashes[slot]); emit(NONE); }')
s = s.replace('for (size_t i = n > LAG ? n - LAG : 0; i < n; ++i) emit(terms.find(keys[i % LAG], hashes[i % LAG]));',
              'for (size_t i = n > LAG ? n - LAG : 0; i < n; ++i) { (void)terms.find(keys[i % LAG], hashes[i % LAG]); emit(NONE); }')
variants['scan-lookup'] = s
for name, text in variants.items():
    p = ROOT / f'research/prototypes/{name}6.cpp'
    p.write_text(text)
    subprocess.run(['docker', 'exec', 'codescythe-research', 'g++', '-std=c++20', '-O3', '-DNDEBUG',
                    '-march=x86-64-v3', '-pthread', '-static', '-s', '-I', '/work/track-b',
                    f'/work/{p.relative_to(ROOT).as_posix()}', '-o', f'/work/build/bench6/{name}'], check=True)
    print('built', name)

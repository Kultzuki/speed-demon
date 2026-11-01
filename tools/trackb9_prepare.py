"""Preserve incoming state and create Track B-only research candidates."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT / '.out/trackb9-incoming'
archive.mkdir(parents=True, exist_ok=False)
status = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=ROOT, text=True)
records = {}
for line in status.splitlines():
    relative = line[3:]
    path = ROOT / relative
    if path.is_file():
        dest = archive / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        records[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
for path in (ROOT / 'track-b').iterdir():
    if path.is_file():
        dest = archive / 'baseline-b' / path.name
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(path, dest)
        records['baseline-b/' + path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
(archive / 'state.json').write_text(json.dumps({'head': subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'status': status,
    'sha256': records}, indent=2) + '\n')

source = (ROOT / 'track-b/main.cpp').read_text()
proto = ROOT / 'research/prototypes'
(proto / 'trackb9-base.cpp').write_text(source)
old = '''        for (size_t i = 0; i < 4; ++i) {
            size_t b = len > 8 * i ? std::min<size_t>(len - 8 * i, 8) : 0;
            u64 w;
            memcpy(&w, s + 8 * i, 8);
            k.w[i] = (w | 0x2020202020202020ull) & (b == 8 ? ~0ull : (1ull << (8 * b)) - 1);
        }'''
new = '''        const __m256i index = _mm256_setr_epi8(0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
                                                   16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31);
        const __m256i raw = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(s));
        const __m256i keep = _mm256_cmpgt_epi8(_mm256_set1_epi8(char(len)), index);
        _mm256_store_si256(reinterpret_cast<__m256i*>(&k),
            _mm256_and_si256(_mm256_or_si256(raw, _mm256_set1_epi8(0x20)), keep));'''
assert source.count(old) == 1
simd = source.replace(old, new)
(proto / 'trackb9-simd.cpp').write_text(simd)
hash_start = simd.index('    u64 h = ', simd.index('inline u64 hash_key'))
hash_end = simd.index('\n}', hash_start)
crc = simd[:hash_start] + '''    u64 h = _mm_crc32_u64(0, k.w[0]);
    h = _mm_crc32_u64(h, k.w[1]);
    if (k.w[2] | k.w[3]) h = _mm_crc32_u64(_mm_crc32_u64(h, k.w[2]), k.w[3]);
    return h * 0x9E3779B97F4A7C15ull;''' + simd[hash_end:]
(proto / 'trackb9-crc.cpp').write_text(crc)
import continuation7_trials
(proto / 'trackb9-profile.cpp').write_text(continuation7_trials.profile(source, 'b'))
(proto / 'trackb9-profile-crc.cpp').write_text(continuation7_trials.profile(crc, 'b'))
print('Preserved incoming files; created isolated B SIMD/CRC and phase candidates.')

"""Use the full uint16 domain now that streams are no longer fixed at 24 bits."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label in ['bucket10', 'gapstream18']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    source = source.replace('sizeof(Doc)==2?15:32', 'sizeof(Doc)==2?16:32')
    source = source.replace('doc = x & 32767, term = x >> 15', 'doc = x & 65535, term = x >> 16')
    source = source.replace('pending << 15 | doc', 'pending << 16 | doc')
    source = source.replace('<< 15 | doc', '<< 16 | doc')
    source = source.replace('>32768)', '>65536)')
    # Query parallelism is independent of builder/segment count.
    start = source.rfind('    for (int t = 0; t < nthreads; ++t) {')
    source = source[:start] + source[start:].replace(
        '    for (int t = 0; t < nthreads; ++t) {',
        '    const unsigned query_threads = std::max(1u, std::min(12u, std::thread::hardware_concurrency()));\n    for (unsigned t = 0; t < query_threads; ++t) {', 1)
    for workers in [4, 6, 8, 10, 12]:
        text = source.replace('std::min(12u, std::thread::hardware_concurrency())',
            f'std::min({workers}u, std::thread::hardware_concurrency())', 1)
        (PROTO / f'trackb9-doc16-{workers}-{label}.cpp').write_text(text)
print('Created checked full-uint16 stream domains with independent query workers.')

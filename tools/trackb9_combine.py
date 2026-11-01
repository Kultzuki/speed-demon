from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label in ['crc', 'filter-base']:
    source = (PROTO / f'trackb9-boundary-{label}.cpp').read_text()
    other = (PROTO / 'trackb9-simdformat.cpp').read_text()
    start = other.index('// Four bitmap words at a time:')
    end = other.index('template<class Doc,class Offset> class Solver', start)
    helper = other[start:end]
    start = source.index('template<class Doc,class Offset> class Solver')
    source = source[:start] + helper + source[start:]
    start = source.index('    int format(char* out) const')
    end = source.index('    static char* put(', start)
    other_start = other.index('    int format(char* out) const')
    other_end = other.index('    static char* put(', other_start)
    source = source[:start] + other[other_start:other_end] + source[end:]
    (PROTO / f'trackb9-combined-{label}.cpp').write_text(source)
print('Combined window pairing with independently exact SIMD result aggregation.')

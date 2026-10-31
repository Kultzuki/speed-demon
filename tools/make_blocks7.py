"""Vary lazy anonymous posting block sizes without changing index semantics."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'continuation7-base-b.cpp').read_text()
for bits in [14, 16, 18]:
    path = PROTO / f'continuation7-block{bits}-b.cpp'
    assert not path.exists()
    assert source.count('static constexpr size_t BLOCK = 1 << 12;') == 1
    path.write_text(source.replace('static constexpr size_t BLOCK = 1 << 12;',
                                   f'static constexpr size_t BLOCK = 1 << {bits};'))
print('Created posting block-size trials; all offsets and fallback widths retained.')

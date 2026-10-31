"""Select only the established unsharded two-pass builder for a new Rust trial."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'track-d/main.rs'
text = path.read_text()
assert 'Parse once into width-derived u64 triples.' in text, 'One-shot experiment: current kernel is not the packed intermediate'
baseline = (ROOT / 'research/prototypes/rust8-compact/d/main.rs').read_text()
begin = 'struct Graph {'
end = '// Radix heap adapted'
left, right = baseline.index(begin), baseline.index(end)
trial = text[:text.index(begin)] + baseline[left:right] + text[text.index(end):]
path.write_text(trial)
print('Restored only the established two-pass CSR; new exact sparse-state work remains.')

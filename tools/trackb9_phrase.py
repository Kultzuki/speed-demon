"""Compare direct rare-anchor phrase verification with intersecting all terms."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
for label in ['base', 'dnf-simdformat']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    start = source.index('        order_.assign(q.terms.begin(), q.terms.end());')
    finish = source.index('        size_t kept = 0;', start)
    source = source[:start] + '''        size_t j = 0;
        for (size_t k = 1; k < q.terms.size(); ++k)
            if (ix_.df[q.terms[k]] < ix_.df[q.terms[j]]) j = k;
        assign(cur_, postings(q.terms[j]));
''' + source[finish:]
    (PROTO / f'trackb9-anchor-{label}.cpp').write_text(source)
print('Created direct exact rare-anchor phrase-verification candidates.')

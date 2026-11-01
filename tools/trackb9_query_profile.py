"""Per-query diagnostic only; do not promote the instrumented binary."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-hybrid-owner2.cpp').read_text()
source = '#include <chrono>\n#include <numeric>\n' + source
source = source.replace('    std::vector<uint8_t> lens(nq);',
    '    std::vector<uint8_t> lens(nq);\n    std::vector<double> elapsed(nq);')
old = '''                for (size_t j = i; j < std::min(nq, i + 16); ++j)
                    lens[j] = solver.answer(queries[j], &slots[j * SLOT]);'''
new = '''                for (size_t j = i; j < std::min(nq, i + 16); ++j) {
                    const auto start = std::chrono::steady_clock::now();
                    lens[j] = solver.answer(queries[j], &slots[j * SLOT]);
                    elapsed[j] = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
                }'''
assert old in source
source = source.replace(old, new)
source = source.replace('    std::string out;\n    out.reserve', '''    std::vector<size_t> ranked(nq);
    std::iota(ranked.begin(), ranked.end(), 0);
    std::partial_sort(ranked.begin(), ranked.begin() + std::min<size_t>(20, nq), ranked.end(),
        [&](size_t a, size_t b) { return elapsed[a] > elapsed[b]; });
    double boolean_s = 0, phrase_s = 0;
    for (size_t i = 0; i < nq; ++i) (queries[i].phrase ? phrase_s : boolean_s) += elapsed[i];
    fprintf(stderr, "QUERY_TIMES bool=%.6f phrase=%.6f\\n", boolean_s, phrase_s);
    for (size_t k = 0; k < std::min<size_t>(20, nq); ++k) {
        const size_t i = ranked[k];
        const Query q = queries[i];
        fprintf(stderr, "QUERY %zu %.6f %s", i, elapsed[i], q.phrase ? "PHRASE" : "BOOL");
        for (size_t j = 0; j < q.terms.size(); ++j)
            fprintf(stderr, " %.*s:%u", int(terms.length(q.terms[j])), terms.bytes(q.terms[j]), ix.df[q.terms[j]]);
        fputc('\\n', stderr);
    }
    std::string out;
    out.reserve''')
(PROTO / 'trackb9-query-profile.cpp').write_text(source)
print('Created per-query timing/term-frequency diagnostic.')

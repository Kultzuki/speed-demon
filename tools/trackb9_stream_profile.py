from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
source = (PROTO / 'trackb9-stream.cpp').read_text()
source = '#include <chrono>\n' + source
source = source.replace('        Matcher matcher(terms);', '''        using Clock = std::chrono::steady_clock;
        double parse_s = 0, query_s = 0;
        u64 evaluations = 0, phrase_candidates = 0;
        Matcher matcher(terms);''')
source = source.replace('        while (p < end) {\n            if (++epoch',
    '        while (p < end) {\n            const auto block_start = Clock::now();\n            if (++epoch')
source = source.replace('            auto word =', '''            const auto parse_end = Clock::now();
            parse_s += std::chrono::duration<double>(parse_end - block_start).count();
            auto word =''')
source = source.replace('                    const Query q = queries[qi];',
    '                    ++evaluations;\n                    const Query q = queries[qi];')
source = source.replace('                        u64 matches = 0;',
    '                        phrase_candidates += __builtin_popcountll(bits);\n                        u64 matches = 0;')
source = source.replace('        }\n    });\n    for (auto& thread', '''            query_s += std::chrono::duration<double>(Clock::now() - parse_end).count();
        }
        fprintf(stderr, "STREAM thread=%u nt=%u parse=%.6f query=%.6f evaluations=%llu phrase_candidates=%llu\\n",
            t, nt, parse_s, query_s, (unsigned long long)evaluations, (unsigned long long)phrase_candidates);
    });
    for (auto& thread''')
(PROTO / 'trackb9-stream-profile.cpp').write_text(source)
print('Created streaming phase/candidate-count diagnostic.')

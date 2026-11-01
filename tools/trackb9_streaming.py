"""Create a query-activated 64-document streaming evaluator for Track B."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
original = (PROTO / 'trackb9-base.cpp').read_text()
base = (PROTO / 'trackb9-boundary-base.cpp').read_text()
prefix = base[:base.index('// Doc-level postings for every query term.')]
match_start = original.index('    // Is the token text [p, p + len)')
match_end = original.index('    int format(char* out) const', match_start)
matcher = '''class Matcher {
public:
    explicit Matcher(const TermTable& terms) : terms_(terms) {}
''' + original[match_start:match_end] + '''private:
    const TermTable& terms_;
};

'''
sum_start = original.index('inline u64 position_sum(')
sum_end = original.index('template<class Doc,class Offset> class Solver', sum_start)
position_sum = original[sum_start:sum_end]
implementation = r'''
// Only the current block's documents are represented. Epochs make clearing
// independent of vocabulary size; an epoch wrap clears every stored tag.
struct TermState { u64 bits = 0; u32 epoch = 0; };
struct Totals { std::vector<u64> count, sum; };

// Counts/sums stay private to each worker. The ten global smallest ids need
// synchronization only while a block can improve the current tenth id.
struct Smallest {
    std::atomic_flag lock = ATOMIC_FLAG_INIT;
    std::atomic<u32> limit{NONE};
    u32 ids[10]{};
    size_t size = 0;
    void add(u64 bits, u32 base) {
        if (base >= limit.load(std::memory_order_relaxed)) return;
        while (lock.test_and_set(std::memory_order_acquire)) _mm_pause();
        while (bits) {
            const u32 doc = base + __builtin_ctzll(bits);
            bits &= bits - 1;
            if (size == 10 && doc >= ids[9]) break;
            size_t at = std::lower_bound(ids, ids + size, doc) - ids;
            const size_t end = std::min<size_t>(size, 9);
            for (size_t j = end; j > at; --j) ids[j] = ids[j - 1];
            ids[at] = doc;
            if (size < 10) ++size;
        }
        if (size == 10) limit.store(ids[9], std::memory_order_relaxed);
        lock.clear(std::memory_order_release);
    }
};

u32 document_id(const uint8_t* p) {
    u32 result = 0;
    while (*p >= '0' && *p <= '9') result = result * 10 + *p++ - '0';
    return result;
}

void stream_solve(const Paths& paths) {
    prctl(PR_SET_THP_DISABLE, 1, 0, 0, 0);
    mallopt(M_MMAP_THRESHOLD, 1 << 16);
    const File query_file = map_file(paths.data + "/queries.txt");
    const File corpus = map_file(paths.data + "/docs.txt");
    TermTable terms;
    Queries queries = parse_queries(query_file, terms);
    const u32 nt = terms.size();
    const size_t nq = queries.size();
    if (!nq) { write_output(paths.out + "/results.txt", ""); return; }

    // Frequency estimates choose anchors and state layout only. They never
    // suppress a possible match. All documents are evaluated in a complete pass.
    std::vector<u64> frequency(nt);
    constexpr size_t SAMPLES = 16, SAMPLE_BYTES = 32768;
    for (size_t sample = 0; sample < SAMPLES; ++sample) {
        size_t at = corpus.size * sample / SAMPLES;
        while (at && at < corpus.size && corpus.data[at - 1] != '\n') ++at;
        const uint8_t* p = corpus.data + at;
        const uint8_t* stop = p + std::min(SAMPLE_BYTES, corpus.size - at);
        const uint8_t* end = corpus.data + corpus.size;
        while (p < stop) {
            const uint8_t* nl = static_cast<const uint8_t*>(memchr(p, '\n', end - p));
            const uint8_t* text = static_cast<const uint8_t*>(memchr(p, '\t', nl - p)) + 1;
            for_each_token(text, nl, terms, [&](u32 id) { if (id != NONE) ++frequency[id]; });
            p = nl + 1;
        }
    }
    std::vector<u32> order(nt), new_id(nt);
    for (u32 i = 0; i < nt; ++i) order[i] = i;
    std::stable_sort(order.begin(), order.end(), [&](u32 a, u32 b) { return frequency[a] > frequency[b]; });
    std::vector<u64> ranked(nt);
    for (u32 i = 0; i < nt; ++i) new_id[order[i]] = i, ranked[i] = frequency[order[i]];
    terms.renumber(new_id);
    for (u32& id : queries.terms) id = new_id[id];
    frequency.swap(ranked);

    // Each OR starts a conjunction in the distributed form of a left fold.
    // Its anchor is a positive term, so any true document must contain an
    // anchor of at least one clause. Binary NOT never creates new candidates.
    std::vector<std::vector<u32>> watchers(nt);
    std::vector<uint8_t> phrase_anchor(nq);
    auto rarer = [&](u32 a, u32 b) {
        return frequency[a] < frequency[b] ||
            (frequency[a] == frequency[b] && terms.length(a) > terms.length(b));
    };
    for (u32 qi = 0; qi < nq; ++qi) {
        const Query q = queries[qi];
        if (q.phrase) {
            size_t best = 0;
            for (size_t j = 1; j < q.terms.size(); ++j) if (rarer(q.terms[j], q.terms[best])) best = j;
            phrase_anchor[qi] = best;
            watchers[q.terms[best]].push_back(qi);
        } else {
            u32 anchors[6];
            size_t used = 0;
            for (size_t root = 0; root < q.terms.size(); ++root) {
                if (root && q.ops[root - 1] != 'O') continue;
                size_t best = root;
                for (size_t j = root + 1; j < q.terms.size(); ++j)
                    if (q.ops[j - 1] == 'A' && rarer(q.terms[j], q.terms[best])) best = j;
                const u32 anchor = q.terms[best];
                if (std::find(anchors, anchors + used, anchor) == anchors + used) {
                    anchors[used++] = anchor;
                    watchers[anchor].push_back(qi);
                }
            }
        }
    }
    std::vector<u32> watch_first(nt + 1), watch_ids;
    for (u32 id = 0; id < nt; ++id) {
        watch_first[id] = watch_ids.size();
        watch_ids.insert(watch_ids.end(), watchers[id].begin(), watchers[id].end());
    }
    watch_first[nt] = watch_ids.size();
    watchers.clear(); watchers.shrink_to_fit();

    const unsigned workers = std::max(1u, std::min(12u, std::thread::hardware_concurrency()));
    std::vector<size_t> cuts(workers + 1);
    for (unsigned t = 0; t <= workers; ++t) {
        size_t at = corpus.size * t / workers;
        while (at && at < corpus.size && corpus.data[at - 1] != '\n') ++at;
        cuts[t] = at;
    }
    std::unique_ptr<Smallest[]> smallest(new Smallest[nq]);
    std::vector<Totals> totals(workers);
    std::vector<std::thread> pool;
    for (unsigned t = 0; t < workers; ++t) pool.emplace_back([&, t] {
        Matcher matcher(terms);
        std::vector<TermState> state(nt);
        std::vector<u32> active, visited(nq);
        active.reserve(8192);
        auto& count = totals[t].count;
        auto& sum = totals[t].sum;
        count.resize(nq); sum.resize(nq);
        const uint8_t* p = corpus.data + cuts[t];
        const uint8_t* end = corpus.data + cuts[t + 1];
        u32 doc = p < end ? document_id(p) : 0, epoch = 0;
        while (p < end) {
            if (++epoch == 0) {
                for (auto& s : state) s.epoch = 0;
                std::fill(visited.begin(), visited.end(), 0);
                epoch = 1;
            }
            const u32 base = doc;
            const uint8_t* begin_text[64];
            const uint8_t* end_text[64];
            active.clear();
            for (u32 local = 0; local < 64 && p < end; ++local, ++doc) {
                const uint8_t* nl = static_cast<const uint8_t*>(memchr(p, '\n', end - p));
                const uint8_t* text = static_cast<const uint8_t*>(memchr(p, '\t', nl - p)) + 1;
                begin_text[local] = text; end_text[local] = nl;
                const u64 bit = 1ull << local;
                for_each_token(text, nl, terms, [&](u32 id) {
                    if (id == NONE) return;
                    auto& s = state[id];
                    if (s.epoch != epoch) {
                        s.epoch = epoch; s.bits = bit;
                        if (watch_first[id] != watch_first[id + 1]) active.push_back(id);
                    } else s.bits |= bit;
                });
                p = nl + 1;
            }
            auto word = [&](u32 id) { return state[id].epoch == epoch ? state[id].bits : 0; };
            for (u32 anchor : active) {
                for (u32 k = watch_first[anchor]; k < watch_first[anchor + 1]; ++k) {
                    const u32 qi = watch_ids[k];
                    if (visited[qi] == epoch) continue;
                    visited[qi] = epoch;
                    const Query q = queries[qi];
                    u64 bits = word(q.terms[0]);
                    if (q.phrase) {
                        for (size_t j = 1; j < q.terms.size() && bits; ++j) bits &= word(q.terms[j]);
                        u64 matches = 0;
                        for (u64 todo = bits; todo; todo &= todo - 1) {
                            const u32 j = __builtin_ctzll(todo);
                            if (matcher.contains(begin_text[j], end_text[j], q.terms, phrase_anchor[qi])) matches |= 1ull << j;
                        }
                        bits = matches;
                    } else {
                        for (size_t j = 1; j < q.terms.size(); ++j) {
                            const u64 b = word(q.terms[j]);
                            if (q.ops[j - 1] == 'A') bits &= b;
                            else if (q.ops[j - 1] == 'O') bits |= b;
                            else bits &= ~b;
                        }
                    }
                    if (bits) {
                        const u64 c = __builtin_popcountll(bits);
                        count[qi] += c;
                        sum[qi] += c * base + position_sum(bits);
                        smallest[qi].add(bits, base);
                    }
                }
            }
        }
    });
    for (auto& thread : pool) thread.join();
    std::string output;
    output.reserve(nq * 32);
    for (size_t qi = 0; qi < nq; ++qi) {
        u64 count = 0, sum = 0;
        for (const auto& worker : totals) count += worker.count[qi], sum += worker.sum[qi];
        number(output, count); output += ' '; number(output, sum);
        for (size_t j = 0; j < smallest[qi].size; ++j) { output += ' '; number(output, smallest[qi].ids[j]); }
        output += '\n';
    }
    write_output(paths.out + "/results.txt", output);
}

} // namespace

int main(int argc, char** argv) {
    try { const Paths paths(argc, argv); stream_solve(paths); }
    catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}
'''
source = prefix + position_sum + matcher + implementation
(PROTO / 'trackb9-stream.cpp').write_text(source)
print('Created query-activated exact block-streaming evaluator.')

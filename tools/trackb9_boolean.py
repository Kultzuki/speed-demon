"""Distribute the exact left fold into rare-first conjunctions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
boolean = '''    void boolean(const Query& q) {
        // The left fold is an OR of conjunctions. Each OR starts a new
        // clause; each later AND/NOT constrains every earlier clause.
        // Start each conjunction at its rarest positive term, then union
        // the clauses. This avoids building a large intermediate set which
        // a later rare AND would immediately discard.
        accumulated_.clear();
        bool accumulated_dense = false, have_clause = false;
        for (size_t root = 0; root < q.terms.size(); ++root) {
            if (root && q.ops[root - 1] != 'O') continue;
            size_t best = root;
            for (size_t j = root + 1; j < q.terms.size(); ++j)
                if (q.ops[j - 1] == 'A' && ix_.df[q.terms[j]] < ix_.df[q.terms[best]]) best = j;
            if (!ix_.df[q.terms[best]]) continue;
            Postings first = postings(q.terms[best]);
            dense_ = first.bits != nullptr;
            if (dense_) bm_.assign(first.bits, first.bits + first.words);
            else cur_.assign(first.p, first.p + first.n);
            for (size_t j = root; j < q.terms.size(); ++j) {
                if (j == best || (j != root && q.ops[j - 1] == 'O')) continue;
                if (!dense_ && cur_.empty()) break;
                const char op = j == root ? 'A' : q.ops[j - 1];
                Postings b = postings(q.terms[j]);
                if (dense_) apply_dense(op, b);
                else {
                    if (op == 'A') op_and(cur_, b, tmp_);
                    else op_not(cur_, b, tmp_);
                    cur_.swap(tmp_);
                }
            }
            if (!have_clause) {
                if (dense_) accumulated_bits_.swap(bm_);
                else accumulated_.swap(cur_);
                accumulated_dense = dense_;
                have_clause = true;
            } else if (accumulated_dense) {
                if (dense_) for (size_t w = 0; w < bm_.size(); ++w) accumulated_bits_[w] |= bm_[w];
                else for (u32 doc : cur_) accumulated_bits_[doc / 64] |= 1ull << (doc % 64);
            } else if (dense_) {
                for (u32 doc : accumulated_) bm_[doc / 64] |= 1ull << (doc % 64);
                accumulated_bits_.swap(bm_);
                accumulated_dense = true;
            } else {
                tmp_.clear();
                std::set_union(accumulated_.begin(), accumulated_.end(), cur_.begin(), cur_.end(), std::back_inserter(tmp_));
                accumulated_.swap(tmp_);
            }
        }
        dense_ = accumulated_dense;
        if (dense_) bm_.swap(accumulated_bits_);
        else cur_.swap(accumulated_);
    }

'''
for label in ['base', 'simdformat']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    start = source.index('    void boolean(const Query& q) {')
    end = source.index('    void apply_dense(', start)
    source = source[:start] + boolean + source[end:]
    source = source.replace('    std::vector<u64> bm_;',
        '    std::vector<u32> accumulated_;\n    std::vector<u64> bm_, accumulated_bits_;')
    (PROTO / f'trackb9-dnf-{label}.cpp').write_text(source)
print('Created exact rare-first distributed Boolean query candidates.')

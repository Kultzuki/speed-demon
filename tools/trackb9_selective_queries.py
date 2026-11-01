"""Read compact segment memberships when a required term has few documents."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / 'research/prototypes'
helper = '''    // A mandatory rare term bounds every possible answer. Keep its compact
    // local ids and check the other operands in their existing segments;
    // this avoids decoding a long list merely to test a few documents.
    void selective(const Query& q, size_t anchor) {
        dense_ = false;
        cur_.clear();
        const u32 anchor_id = q.terms[anchor];
        u32 first = ix_.start[anchor_id];
        struct View { const Doc* begin; const Doc* end; const u64* bits; };
        for (int t = 0; t < ix_.threads; ++t) {
            const u32 end = ix_.seg_end[t][anchor_id];
            if (first == end) continue;
            View views[8];
            for (size_t j = 0; j < q.terms.size(); ++j) {
                const u32 id = q.terms[j], d = ix_.dense[id];
                if (d != NONE) views[j] = {nullptr, nullptr, &ix_.bits[d * ix_.words]};
                else views[j] = {ix_.post.get() + (t ? ix_.seg_end[t - 1][id] : ix_.start[id]),
                                 ix_.post.get() + ix_.seg_end[t][id], nullptr};
            }
            for (; first < end; ++first) {
                const Doc local = ix_.post[first];
                const u32 doc = ix_.first[t] + local;
                auto present = [&](size_t j) {
                    const View& v = views[j];
                    return q.terms[j] == anchor_id || (v.bits ? has(v.bits, doc) : std::binary_search(v.begin, v.end, local));
                };
                bool yes;
                if (q.phrase) {
                    yes = true;
                    for (size_t j = 0; j < q.terms.size() && yes; ++j) yes = present(j);
                    if (yes) yes = contains(docs_.data + ix_.text[2 * size_t(doc)],
                        docs_.data + ix_.text[2 * size_t(doc) + 1], q.terms, anchor);
                } else {
                    yes = present(0);
                    for (size_t j = 1; j < q.terms.size(); ++j) {
                        const bool b = present(j);
                        if (q.ops[j - 1] == 'A') yes &= b;
                        else if (q.ops[j - 1] == 'O') yes |= b;
                        else yes &= !b;
                    }
                }
                if (yes) cur_.push_back(doc);
            }
        }
    }

'''
boolean = '''        // A positive AND after the last OR is required by the entire left
        // fold. With no OR, the first term and every AND term are required.
        int last_or = -1;
        u64 cost = 0;
        for (size_t j = 0; j < q.ops.size(); ++j) if (q.ops[j] == 'O') last_or = j;
        size_t anchor = last_or < 0 ? 0 : q.terms.size();
        for (size_t j = size_t(last_or + 2); j < q.terms.size(); ++j)
            if (q.ops[j - 1] == 'A' && (anchor == q.terms.size() || ix_.df[q.terms[j]] < ix_.df[q.terms[anchor]])) anchor = j;
        for (u32 id : q.terms) cost += ix_.dense[id] != NONE ? ix_.words : ix_.df[id];
        if (anchor < q.terms.size()) {
            const u32 id = q.terms[anchor];
            if (!ix_.df[id]) { dense_ = false; cur_.clear(); return; }
            if (ix_.dense[id] == NONE && ix_.df[id] <= 256 && u64(ix_.df[id]) * 16 < cost) {
                selective(q, anchor);
                return;
            }
        }
'''
phrase = '''        if (q.terms.size() <= 8) {
            size_t anchor = 0;
            for (size_t j = 1; j < q.terms.size(); ++j)
                if (ix_.df[q.terms[j]] < ix_.df[q.terms[anchor]]) anchor = j;
            if (ix_.dense[q.terms[anchor]] == NONE && ix_.df[q.terms[anchor]] <= 256) {
                selective(q, anchor);
                return;
            }
        }
'''
for label in ['gapstream18', 'owner-bucket12']:
    source = (PROTO / f'trackb9-{label}.cpp').read_text()
    start = source.index('    void boolean(const Query& q) {')
    source = source[:start] + helper + source[start:]
    source = source.replace('    void boolean(const Query& q) {\n', '    void boolean(const Query& q) {\n' + boolean)
    source = source.replace('    void phrase(const Query& q) {\n', '    void phrase(const Query& q) {\n' + phrase)
    (PROTO / f'trackb9-selective-{label}.cpp').write_text(source)
print('Created selective exact segment-membership query candidates.')

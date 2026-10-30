"""Test the supplied B document-filtering idea with exact unbounded scanning."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'research/prototypes/b-small-posting.cpp').read_text()
s=s.replace('if (!q.phrase && term.boolean == NONE)', 'if (term.boolean == NONE)')
start=s.index('        // Sampling affects only anchor choice;')
stop=s.index('        unsigned workers =',start)
s=s[:start]+s[stop:]
s=s.replace('block.postings.resize(boolean_count); block.occurrences.resize(anchor_count);','block.postings.resize(boolean_count);')
s=s.replace('std::vector<Block<Doc>> blocks(workers);', 'std::vector<uint64_t> doc_starts(size_t(document_count)+1);\n        std::vector<Block<Doc>> blocks(workers);')
s=s.replace('uint32_t doc = integer(current); ++current;', 'uint32_t doc = integer(current); ++current;doc_starts[doc]=current-corpus.data;')
start=s.index('                    if (term.anchor != NONE) {')
stop=s.index('\n                    }',start)+len('\n                    }')
s=s[:start]+s[stop:]
start=s.index('                            const auto& occurrences = block.occurrences[terms[q.terms[q.anchor]].anchor];')
stop=s.index('\n                        }',start)
s=s[:start]+r'''
                            uint32_t anchor=q.terms[0];
                            for (uint32_t id:q.terms) {
                                auto estimate=[&](uint32_t term) {
                                    const auto& p=block.postings[terms[term].boolean];
                                    return p.dense()?block.count:p.count;
                                };
                                if (estimate(id)<estimate(anchor)) anchor=id;
                            }
                            const auto& postings=block.postings[terms[anchor].boolean];
                            auto probe=[&](uint32_t local) {
                                for (uint32_t id:q.terms) if (id!=anchor) {
                                    const auto& other=block.postings[terms[id].boolean];
                                    if (other.dense()) {
                                        if (!(other.storage.bits[local/64]&(uint64_t(1)<<(local%64)))) return;
                                    } else if (!std::binary_search(other.data(),other.data()+other.count,local)) return;
                                }
                                uint32_t doc=block.base+local;
                                if (matches_doc(corpus.data+doc_starts[doc],corpus.end(),q,terms)) answer.add(doc);
                            };
                            if (postings.dense()) {
                                for (size_t w=0;w<(size_t(block.count)+63)/64;++w) {
                                    uint64_t bits=postings.storage.bits[w];
                                    while (bits) {probe(w*64+std::countr_zero(bits));bits&=bits-1;}
                                }
                            } else for (uint32_t i=0;i<postings.count;++i) probe(postings.data()[i]);
''' +s[stop:]
start=s.index('bool matches(')
stop=s.index('template<class Doc> void solve(',start)
match=r'''
bool matches_doc(const char* p,const char* end,const Query& q,const std::vector<Term>& terms) {
    // Streaming KMP has no token-count cap and preserves repeated words.
    std::array<unsigned,8> prefix{};
    for (unsigned i=1,j=0;i<q.terms.size();++i) {
        while (j && q.terms[i]!=q.terms[j]) j=prefix[j-1];
        if (q.terms[i]==q.terms[j]) ++j;
        prefix[i]=j;
    }
    unsigned matched=0;
    while (p<end && *p!='\n') {
        if (!raw_token(*p)) {++p;continue;}
        const char* start=p;
        while (p<end && raw_token(*p)) ++p;
        auto equal=[&](unsigned i) {
            auto word=terms[q.terms[i]].word;
            if (size_t(p-start)!=word.size()) return false;
            for (size_t at=0;at<word.size();++at) if (normalized(start[at])!=static_cast<unsigned char>(word[at])) return false;
            return true;
        };
        while (matched && !equal(matched)) matched=prefix[matched-1];
        if (equal(matched) && ++matched==q.terms.size()) return true;
    }
    return false;
}

'''
s=s[:start]+match+s[stop:]
(root/'research/prototypes/b-docfilter.cpp').write_text(s)

#include "common.hpp"
#include <unordered_map>
#include <thread>

struct Term {
    std::vector<uint32_t> documents, positions;
    bool phrase = false;
};
struct Query {
    bool phrase;
    std::vector<uint32_t> terms;
    std::vector<char> operators;
};

// A contiguous read-only table avoids a node allocation and pointer chase for
// every dictionary probe. Full bytes are still compared after matching hashes.
struct Lookup {
    struct Slot { size_t hash = 0; std::string_view word; uint32_t id = 0x7fffffff; };
    std::vector<Slot> slots;
    size_t mask;
    explicit Lookup(const std::unordered_map<std::string_view, uint32_t>& dictionary) {
        size_t capacity = 1;
        while (capacity < dictionary.size() * 2) capacity *= 2;
        slots.resize(capacity); mask = capacity - 1;
        for (auto [word, id] : dictionary) {
            size_t hash = std::hash<std::string_view>()(word), at = hash & mask;
            while (slots[at].id != 0x7fffffff) at = (at + 1) & mask;
            slots[at] = {hash, word, id};
        }
    }
    uint32_t find(std::string_view word) const {
        size_t hash = std::hash<std::string_view>()(word), at = hash & mask;
        for (;;) {
            const auto& slot = slots[at];
            if (slot.id == 0x7fffffff) return 0x7fffffff;
            if (slot.hash == hash && slot.word == word) return slot.id;
            at = (at + 1) & mask;
        }
    }
};

inline unsigned normalized(unsigned char ch) {
    return ch >= 'A' && ch <= 'Z' ? ch + ('a' - 'A') : ch;
}
inline bool token_byte(unsigned c) {
    return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9');
}

void result_line(std::string& output, const std::vector<uint32_t>& documents) {
    uint64_t sum = 0;
    for (auto id : documents) sum += id;
    number(output, documents.size()); output += ' '; number(output, sum);
    for (size_t i = 0; i < std::min(size_t(10), documents.size()); ++i) {
        output += ' '; number(output, documents[i]);
    }
    output += '\n';
}

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        MappedFile query_file(paths.data + "/queries.txt");
        std::unordered_map<std::string_view, uint32_t> dictionary;
        dictionary.reserve(131072);
        std::vector<Term> terms;
        std::vector<Query> queries;
        const char* p = query_file.data;
        while (p < query_file.end()) {
            Query q;
            q.phrase = *p == 'P';
            p += q.phrase ? 8 : 5;
            for (;;) {
                const char* start = p;
                while (token_byte(static_cast<unsigned char>(*p))) ++p;
                auto [it, inserted] = dictionary.try_emplace(std::string_view(start, p - start), terms.size());
                if (inserted) terms.emplace_back();
                q.terms.push_back(it->second);
                terms[it->second].phrase |= q.phrase;
                if (q.phrase && *p == '"') { p += 2; break; }
                if (*p == '\n') { ++p; break; }
                ++p;
                if (!q.phrase) {
                    q.operators.push_back(*p);
                    while (*p++ != ' ') {}
                }
            }
            queries.push_back(std::move(q));
        }
        Lookup lookup(dictionary);
        struct Block {
            std::vector<Term> terms;
            std::vector<uint32_t> tokens, starts;
        };
        std::vector<uint32_t> tokens, document_starts;
        {
            MappedFile corpus(paths.data + "/docs.txt");
            unsigned workers = std::min(6u, std::max(1u, std::thread::hardware_concurrency()));
            if (corpus.size < 2 * 1024 * 1024) workers = 1;
            std::vector<const char*> boundaries(workers + 1);
            boundaries[0] = corpus.data;
            boundaries[workers] = corpus.end();
            for (unsigned i = 1; i < workers; ++i) {
                const char* at = corpus.data + corpus.size * i / workers;
                while (at < corpus.end() && at[-1] != '\n') ++at;
                boundaries[i] = at;
            }
            std::vector<Block> blocks(workers);
            std::vector<std::thread> threads;
            for (unsigned worker = 0; worker < workers; ++worker) threads.emplace_back([&, worker] {
                auto& block = blocks[worker];
                block.terms.resize(terms.size());
                block.tokens.reserve((boundaries[worker + 1] - boundaries[worker]) / 6);
                const char* current = boundaries[worker];
                char word[33];
                while (current < boundaries[worker + 1]) {
                    uint32_t doc = integer(current); ++current;
                    block.starts.push_back(block.tokens.size());
                    while (*current != '\n') {
                        if (!token_byte(normalized(*current))) { ++current; continue; }
                        unsigned length = 0;
                        do { word[length++] = char(normalized(*current++)); }
                        while (token_byte(normalized(*current)));
                        uint32_t id = lookup.find(std::string_view(word, length));
                        if (id != 0x7fffffff) {
                            auto& term = block.terms[id];
                            if (term.documents.empty() || term.documents.back() != doc) term.documents.push_back(doc);
                            if (terms[id].phrase) term.positions.push_back(block.tokens.size());
                        }
                        block.tokens.push_back(id);
                    }
                    if (block.tokens.size() > block.starts.back()) block.tokens.back() |= 0x80000000u;
                    ++current;
                }
            });
            for (auto& thread : threads) thread.join();
            size_t token_count = 0, document_count = 0;
            for (const auto& block : blocks) { token_count += block.tokens.size(); document_count += block.starts.size(); }
            tokens.reserve(token_count);
            document_starts.reserve(document_count + 1);
            std::vector<uint32_t> bases;
            for (auto& block : blocks) {
                uint32_t base = tokens.size();
                bases.push_back(base);
                for (auto start : block.starts) document_starts.push_back(base + start);
                tokens.insert(tokens.end(), block.tokens.begin(), block.tokens.end());
                std::vector<uint32_t>().swap(block.tokens);
            }
            // Blocks follow corpus order, so concatenating their lists preserves
            // sorted unique document IDs and sorted global occurrence positions.
            for (size_t id = 0; id < terms.size(); ++id) {
                size_t docs = 0, positions = 0;
                for (auto& block : blocks) { docs += block.terms[id].documents.size(); positions += block.terms[id].positions.size(); }
                terms[id].documents.reserve(docs);
                terms[id].positions.reserve(positions);
                for (unsigned worker = 0; worker < workers; ++worker) {
                    auto& local = blocks[worker].terms[id];
                    terms[id].documents.insert(terms[id].documents.end(), local.documents.begin(), local.documents.end());
                    for (auto position : local.positions) terms[id].positions.push_back(bases[worker] + position);
                    std::vector<uint32_t>().swap(local.documents);
                    std::vector<uint32_t>().swap(local.positions);
                }
            }
        }
        document_starts.push_back(tokens.size());
        std::vector<uint32_t> result, scratch;
        std::string output;
        output.reserve(2 * 1024 * 1024);
        for (const auto& q : queries) {
            result.clear();
            if (!q.phrase) {
                result = terms[q.terms[0]].documents;
                for (size_t i = 1; i < q.terms.size(); ++i) {
                    const auto& other = terms[q.terms[i]].documents;
                    scratch.clear();
                    scratch.reserve(result.size() + (q.operators[i - 1] == 'O' ? other.size() : 0));
                    auto dest = std::back_inserter(scratch);
                    if (q.operators[i - 1] == 'A') std::set_intersection(result.begin(), result.end(), other.begin(), other.end(), dest);
                    else if (q.operators[i - 1] == 'O') std::set_union(result.begin(), result.end(), other.begin(), other.end(), dest);
                    else std::set_difference(result.begin(), result.end(), other.begin(), other.end(), dest);
                    result.swap(scratch);
                }
            } else {
                size_t anchor = 0;
                for (size_t i = 1; i < q.terms.size(); ++i)
                    if (terms[q.terms[i]].positions.size() < terms[q.terms[anchor]].positions.size()) anchor = i;
                uint32_t skip_until = 0;
                for (uint32_t position : terms[q.terms[anchor]].positions) {
                    if (position < skip_until || position < anchor) continue;
                    size_t start = position - anchor;
                    if (start + q.terms.size() > tokens.size()) continue;
                    bool match = true;
                    for (size_t i = 0; i < q.terms.size(); ++i) {
                        uint32_t value = tokens[start + i];
                        if (i + 1 == q.terms.size()) value &= 0x7fffffffu;
                        if (value != q.terms[i]) { match = false; break; }
                    }
                    if (match) {
                        auto boundary = std::upper_bound(document_starts.begin(), document_starts.end(), start);
                        uint32_t doc = boundary - document_starts.begin() - 1;
                        result.push_back(doc);
                        skip_until = document_starts[doc + 1];
                    }
                }
            }
            result_line(output, result);
        }
        write_output(paths.out + "/results.txt", output);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}

#include "common.hpp"
#include <unordered_map>

struct Term {
    std::vector<uint32_t> documents, positions;
    bool phrase = false;
};
struct Query {
    bool phrase;
    std::vector<uint32_t> terms;
    std::vector<char> operators;
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
        std::vector<uint32_t> tokens, document_starts;
        // Reserve from input size, not a fixed answer or a particular seed.
        {
            MappedFile corpus(paths.data + "/docs.txt");
            tokens.reserve(corpus.size / 6);
            document_starts.reserve(corpus.size / 512);
            p = corpus.data;
            char word[33];
            while (p < corpus.end()) {
                uint32_t doc = integer(p); ++p;
                document_starts.push_back(tokens.size());
                while (*p != '\n') {
                    if (!token_byte(normalized(*p))) { ++p; continue; }
                    unsigned length = 0;
                    do { word[length++] = char(normalized(*p++)); }
                    while (token_byte(normalized(*p)));
                    auto it = dictionary.find(std::string_view(word, length));
                    uint32_t id = it == dictionary.end() ? 0x7fffffff : it->second;
                    if (it != dictionary.end()) {
                        auto& term = terms[id];
                        if (term.documents.empty() || term.documents.back() != doc) term.documents.push_back(doc);
                        if (term.phrase) term.positions.push_back(tokens.size());
                    }
                    tokens.push_back(id);
                }
                // A boundary bit forbids phrase matches across two documents.
                if (tokens.size() > document_starts.back()) tokens.back() |= 0x80000000u;
                ++p;
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

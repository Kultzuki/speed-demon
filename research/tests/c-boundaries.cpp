#define main candidate_main
#ifndef CANDIDATE_SOURCE
#define CANDIDATE_SOURCE "../prototypes/c-parallel.cpp"
#endif
#include CANDIDATE_SOURCE
#undef main
#include <cstdlib>

int main() {
    for (size_t shift = 0; shift < 64; ++shift) {
        std::string input;
        std::vector<size_t> safe{0};
        for (unsigned i = 0; i < 73; ++i) {
            input += (i % 7 == 0 ? "\xef\xbb\xbf" : "");
            input += "1,\"A \"\"name\"\"\",\"" + std::string(shift + i % 19, 'x');
            input += "\"\"first\nsecond\"\"\",1,-0.01";
            if (i != 72 || shift % 2) input += i % 2 ? "\r\n" : "\n";
            safe.push_back(input.size());
        }
        for (unsigned workers = 1; workers <= 12; ++workers) {
            auto cuts = boundaries(input.data(), input.data() + input.size(), workers);
            if (cuts.front() != input.data() || cuts.back() != input.data() + input.size()) std::abort();
            for (unsigned i = 1; i <= workers; ++i) {
                size_t offset = cuts[i] - input.data();
                if (cuts[i] < cuts[i-1] || !std::binary_search(safe.begin(), safe.end(), offset)) std::abort();
            }
        }
    }
    puts("PASS C quote boundaries: 64 alignments, 1-12 workers, LF/CRLF, BOM, EOF");
}

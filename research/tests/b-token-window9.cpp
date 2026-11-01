#define main track_b_candidate_main
#include CANDIDATE_SOURCE
#undef main
#include <unordered_map>

int main() {
    TermTable terms;
    std::vector<Key> keys;
    uint64_t rng = 0x728ae51b994d3e61ull;
    auto next = [&] { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng; };
    std::unordered_map<u64, Key> hashes;
    Key collision_a{}, collision_b{};
    bool collided = false;
    for (u32 i = 0; i < 500000 && (!collided || keys.size() < 40000); ++i) {
        char word[32];
        for (char& c : word) c = char('a' + next() % 26);
        Key key = make_key(reinterpret_cast<const uint8_t*>(word), sizeof(word));
        const u64 hash = hash_key(key);
        auto [it, inserted] = hashes.emplace(hash, key);
        if (!inserted && !same(it->second, key)) {
            collided = true; collision_a = it->second; collision_b = key;
        }
        if (keys.size() < 40000) { keys.push_back(key); terms.insert(key); }
    }
    if (!collided) { fputs("No deterministic CRC collision found\n", stderr); return 1; }
    const u32 a = terms.insert(collision_a), b = terms.insert(collision_b);
    if (a == b || terms.find(collision_a, hash_key(collision_a)) != a ||
        terms.find(collision_b, hash_key(collision_b)) != b) return 2;
    std::vector<u32> reverse(terms.size());
    for (u32 i = 0; i < reverse.size(); ++i) reverse[i] = reverse.size() - 1 - i;
    terms.renumber(reverse);
    if (terms.find(collision_a, hash_key(collision_a)) != reverse[a] ||
        terms.find(collision_b, hash_key(collision_b)) != reverse[b]) return 3;
    for (u32 i = 0; i < keys.size(); ++i)
        if (terms.find(keys[i], hash_key(keys[i])) != reverse[i]) return 4;

    TermTable windows;
    for (size_t length = 1; length <= 32; ++length) {
        const std::string word(length, 'a');
        windows.insert(make_key(reinterpret_cast<const uint8_t*>(word.data()), length));
    }
    size_t cases = 0;
    for (size_t length = 1; length <= 32; ++length) {
        for (size_t shift = 0; shift < 128; ++shift) {
            alignas(64) uint8_t bytes[512]{};
            memset(bytes, '.', shift);
            memset(bytes + shift, 'A', length);
            const size_t end = shift + length;
            std::vector<u32> actual;
            for_each_token(bytes, bytes + end, windows, [&](u32 id) { if (id != NONE) actual.push_back(id); });
            if (actual != std::vector<u32>{u32(length - 1)}) return 5;
            ++cases;
        }
    }
    BlockList<uint16_t> list;
    std::vector<u32> expected, actual;
    for (u32 i = 0; i < BlockList<uint16_t>::BLOCK - 1; ++i) expected.push_back((i % 512) << 15);
    expected.push_back((511u << 15) | 1000);
    expected.push_back((3u << 15) | 1050);
    expected.push_back((22u << 15) | 10000);
    expected.push_back((511u << 15) | 32767);
    for (u32 x : expected) list.push(x);
    list.drain([&](u32 x) { actual.push_back(x); });
    if (actual != expected) return 6;
    BlockList<uint32_t> wide;
    const std::vector<u64> wide_values{0, (511ull << 32) | 32768, (511ull << 32) | UINT32_MAX};
    std::vector<u64> wide_actual;
    for (u64 x : wide_values) wide.push(x);
    wide.drain([&](u64 x) { wide_actual.push_back(x); });
    if (wide_actual != wide_values) return 7;
    printf("PASS %zu tokenizer alignments, real CRC collision, table growth/renumbering, posting escape boundary and full uint32 domain\n", cases);
}

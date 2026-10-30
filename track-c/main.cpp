#include "common.hpp"
#include <array>
#include <limits>
#include <unordered_map>

struct Field {
    std::string_view value;
    size_t bytes;
};

// memchr jumps between quotes. Embedded LF and commas are ordinary bytes here.
Field text_field(const char*& p, const char* end, std::string* decoded) {
    const char* start = p;
    if (*p != '"') {
        while (p < end && *p != ',') ++p;
        return {std::string_view(start, p - start), size_t(p - start)};
    }
    start = ++p;
    const char* segment = p;
    size_t escaped = 0;
    if (decoded) decoded->clear();
    for (;;) {
        p = static_cast<const char*>(memchr(p, '"', end - p));
        if (!p) throw std::runtime_error("Unclosed CSV quote");
        if (p + 1 < end && p[1] == '"') {
            if (decoded) decoded->append(segment, p + 1);
            ++escaped;
            p += 2;
            segment = p;
        } else {
            size_t bytes = p - start - escaped;
            std::string_view value(start, p - start);
            if (escaped && decoded) { decoded->append(segment, p); value = *decoded; }
            ++p;
            return {value, bytes};
        }
    }
}


// Compact names use arena offsets, so arena growth cannot invalidate keys.
// At most 240 country codes plus _UNMATCHED need four membership words.
struct NameTable {
    struct Slot { size_t hash = 0; uint32_t id = UINT32_MAX, length = 0; };
    std::vector<Slot> slots = std::vector<Slot>(1 << 18);
    std::vector<uint32_t> offsets;
    std::vector<std::array<uint64_t, 4>> membership;
    std::vector<char> arena;
    NameTable() { offsets.reserve(131072); membership.reserve(131072); arena.reserve(4 * 1024 * 1024); }
    bool add(std::string_view name, uint16_t country) {
        if (offsets.size() * 2 >= slots.size()) {
            std::vector<Slot> grown(slots.size() * 2);
            for (const auto& slot : slots) if (slot.id != UINT32_MAX) {
                size_t at = slot.hash & (grown.size() - 1);
                while (grown[at].id != UINT32_MAX) at = (at + 1) & (grown.size() - 1);
                grown[at] = slot;
            }
            slots.swap(grown);
        }
        size_t hash = std::hash<std::string_view>()(name), at = hash & (slots.size() - 1);
        while (slots[at].id != UINT32_MAX) {
            const auto& slot = slots[at];
            if (slot.hash == hash && slot.length == name.size() &&
                name == std::string_view(arena.data() + offsets[slot.id], slot.length)) break;
            at = (at + 1) & (slots.size() - 1);
        }
        auto& slot = slots[at];
        if (slot.id == UINT32_MAX) {
            slot = {hash, static_cast<uint32_t>(offsets.size()), static_cast<uint32_t>(name.size())};
            offsets.push_back(arena.size());
            arena.insert(arena.end(), name.begin(), name.end());
            membership.push_back({});
        }
        uint64_t& bits = membership[slot.id][country / 64];
        uint64_t bit = uint64_t(1) << (country % 64);
        bool fresh = !(bits & bit); bits |= bit; return fresh;
    }
};

struct Country {
    std::string key;
    uint64_t count = 0, id_sum = 0, distinct = 0, name_bytes = 0, note_bytes = 0;
    int64_t sum = 0, minimum = INT64_MAX, maximum = INT64_MIN;
};

void money(std::string& out, int64_t value) {
    if (value < 0) { out += '-'; value = -value; }
    number(out, value / 100);
    out += '.';
    out += char('0' + value % 100 / 10);
    out += char('0' + value % 10);
}

int main(int argc, char** argv) {
    try {
        Paths paths(argc, argv);
        MappedFile regions(paths.data + "/regions.csv"), records(paths.data + "/records.csv");
        std::vector<Country> countries(1);
        countries[0].key = "_UNMATCHED";
        std::unordered_map<std::string_view, uint16_t> country_ids;
        // The lookup has IDs <= 999999. Out-of-range record IDs are unmatched.
        std::vector<uint16_t> lookup(1000000);
        const char* p = regions.data;
        while (p < regions.end() && *p++ != '\n') {}
        while (p < regions.end()) {
            uint32_t region = integer(p);
            ++p;
            std::string_view key(p, 3);
            auto [it, inserted] = country_ids.try_emplace(key, countries.size());
            if (inserted) { countries.emplace_back(); countries.back().key = key; }
            if (region >= lookup.size()) lookup.resize(size_t(region) + 1);
            lookup[region] = it->second;
            p += 4;
        }
        // Exact names are interned once; full byte equality resolves collisions.
        NameTable names;
        std::string scratch;
        p = records.data;
        while (p < records.end() && *p++ != '\n') {}
        while (p < records.end()) {
            if (static_cast<unsigned char>(*p) == 0xef) p += 3;
            uint64_t id = integer(p);
            ++p;
            Field name = text_field(p, records.end(), &scratch);
            ++p;
            Field note = text_field(p, records.end(), nullptr);
            ++p;
            uint32_t region = integer(p);
            ++p;
            bool negative = *p == '-';
            p += negative;
            int64_t amount = integer(p) * 100;
            ++p;
            amount += (p[0] - '0') * 10 + p[1] - '0';
            p += 2;
            if (p < records.end() && *p == '\r') ++p;
            if (p < records.end() && *p == '\n') ++p;
            if (negative) amount = -amount;
            uint16_t country = region < lookup.size() ? lookup[region] : 0;
            auto& group = countries[country];
            group.distinct += names.add(name.value, country);
            ++group.count;
            group.id_sum += id;
            group.sum += amount;
            group.minimum = std::min(group.minimum, amount);
            group.maximum = std::max(group.maximum, amount);
            group.name_bytes += name.bytes;
            group.note_bytes += note.bytes;
        }
        std::sort(countries.begin(), countries.end(), [](auto& a, auto& b) { return a.key < b.key; });
        std::string output;
        for (const auto& g : countries) {
            if (!g.count) continue;
            output += g.key;
            for (auto value : {g.count, g.id_sum}) { output += ' '; number(output, value); }
            for (auto value : {g.sum, g.minimum, g.maximum}) { output += ' '; money(output, value); }
            for (auto value : {g.distinct, g.name_bytes, g.note_bytes}) { output += ' '; number(output, value); }
            output += '\n';
        }
        write_output(paths.out + "/aggregates.txt", output);
    } catch (const std::exception& e) { fprintf(stderr, "%s\n", e.what()); return 1; }
}

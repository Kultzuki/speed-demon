#pragma once
#include <algorithm>
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

// The mapping stays alive until every string_view referring to it is destroyed.
struct MappedFile {
    const char* data = "";
    size_t size = 0;
    explicit MappedFile(const std::string& path) {
        int fd = open(path.c_str(), O_RDONLY);
        if (fd < 0) throw std::runtime_error("Cannot open " + path);
        struct stat st {};
        if (fstat(fd, &st) != 0) { close(fd); throw std::runtime_error("Cannot stat " + path); }
        size = static_cast<size_t>(st.st_size);
        if (size) {
            void* p = mmap(nullptr, size, PROT_READ, MAP_PRIVATE, fd, 0);
            if (p == MAP_FAILED) { close(fd); throw std::runtime_error("Cannot map " + path); }
            data = static_cast<const char*>(p);
        }
        close(fd);
    }
    ~MappedFile() { if (size) munmap(const_cast<char*>(data), size); }
    MappedFile(const MappedFile&) = delete;
    MappedFile& operator=(const MappedFile&) = delete;
    const char* end() const { return data + size; }
};

inline uint64_t integer(const char*& p) {
    uint64_t value = 0;
    while (static_cast<unsigned>(*p - '0') < 10) value = value * 10 + (*p++ - '0');
    return value;
}

struct Paths {
    std::string data = "/data", out = "/out";
    Paths(int argc, char** argv) {
        for (int i = 1; i < argc; i += 2) {
            if (i + 1 == argc) throw std::runtime_error("Missing option value");
            if (std::string_view(argv[i]) == "--data") data = argv[i + 1];
            else if (std::string_view(argv[i]) == "--out") out = argv[i + 1];
            else throw std::runtime_error("Unknown argument");
        }
    }
};

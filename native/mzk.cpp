#include "mzk.h"
#include <iostream>
#include <vector>

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cout << "pakai: mzk <file>\n";
        return 1;
    }
    FILE *f = std::fopen(argv[1], "rb");
    if (!f) { std::cerr << "gagal buka\n"; return 1; }
    std::vector<unsigned char> buf(1 << 16);
    uint64_t h = 1469598103934665603ULL;
    size_t n;
    while ((n = std::fread(buf.data(), 1, buf.size(), f)) > 0) {
        for (size_t i = 0; i < n; i++) {
            h ^= buf[i];
            h *= 1099511628211ULL;
        }
    }
    std::fclose(f);
    std::cout << "sha-fnv: " << std::hex << h << std::dec << "\n";
    return 0;
}

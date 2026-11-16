#include "mzk.h"

uint64_t mzk_hash(const void *data, size_t len) {
    const unsigned char *p = (const unsigned char *)data;
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < len; i++) {
        h ^= (uint64_t)p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

int mzk_is_zip(const unsigned char *buf, size_t len) {
    if (len < 4) return 0;
    return buf[0] == 'P' && buf[1] == 'K' && buf[2] == 3 && buf[3] == 4;
}

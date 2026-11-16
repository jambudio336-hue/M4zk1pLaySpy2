#ifndef MZK_H
#define MZK_H

#include <stddef.h>
#include <stdint.h>

/* FNV-1a 64-bit untuk checksum artefak APK */
uint64_t mzk_hash(const void *data, size_t len);

/* Cek signature ZIP lokal (PK\x03\x04) */
int mzk_is_zip(const unsigned char *buf, size_t len);

#endif

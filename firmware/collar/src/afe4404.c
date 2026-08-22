#include "afe4404.h"

#include <stddef.h>

int32_t afe4404_sample_from_be24(const uint8_t b[3]) {
    if (b == NULL) {
        return 0;
    }
    int32_t v = ((int32_t)b[0] << 16) | ((int32_t)b[1] << 8) | (int32_t)b[2];
    if (v & 0x800000) {
        v |= ~0xFFFFFF;
    }
    return v;
}

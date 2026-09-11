#include "ble_tx.h"

#include <string.h>

int collar_ble_pack(const uint8_t *frame, int n, uint8_t *out, size_t cap, int mtu) {
    if (frame == NULL || out == NULL || n <= 0 || mtu < 6) {
        return -1;
    }
    int maxp = mtu - 3;
    if (n > maxp) {
        n = maxp;
    }
    if ((size_t)n > cap) {
        return -1;
    }
    memcpy(out, frame, (size_t)n);
    return n;
}

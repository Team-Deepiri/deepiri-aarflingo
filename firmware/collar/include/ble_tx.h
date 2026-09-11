#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

#include "ble_link.h"

/* Copy frame into a notify payload. Truncates to mtu-3. Returns length or -1. */
int collar_ble_pack(const uint8_t *frame, int n, uint8_t *out, size_t cap, int mtu);

#ifdef __cplusplus
}
#endif

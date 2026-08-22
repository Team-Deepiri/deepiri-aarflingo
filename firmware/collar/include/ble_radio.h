#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

void collar_ble_begin(void);
void collar_ble_notify(const uint8_t *p, int n);
int collar_ble_subscribed(void);

#ifdef __cplusplus
}
#endif

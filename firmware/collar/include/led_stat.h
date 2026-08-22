#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* 10 ms healthy tick, 500 ms slow blink, 0 = solid (vbat empty). */
uint32_t collar_led_period_ms(const char *fault);

#ifdef __cplusplus
}
#endif

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

typedef struct {
    int ok;
    int hr_bpm;
    int rmssd_ms;
} PpgHr;

/* IR samples, fs_hz typically 50. ok=0 if fewer than 3 peaks. */
PpgHr ppg_hr_from_ir(const int32_t *ir, size_t n, int fs_hz);

#ifdef __cplusplus
}
#endif

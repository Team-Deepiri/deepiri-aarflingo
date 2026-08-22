#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include "frame.h"

#include <stddef.h>
#include <stdint.h>

typedef enum {
    COLLAR_IDLE = 0,
    COLLAR_SAMPLE,
    COLLAR_TRANSMIT
} CollarState;

typedef struct {
    CollarState state;
    uint32_t ts_ms;
    CollarSample last;
    uint8_t tx[256];
    int tx_len;
} CollarLoop;

void collar_loop_init(CollarLoop *L);

/* One SAMPLE→TRANSMIT step. ir[0..n-1] is the last 1 s of AFE4404 IR. */
int collar_loop_step(CollarLoop *L, const int32_t *ir, size_t n, int fs_hz,
                     float imu_rms, float imu_peak, float audio_rms, int bark,
                     float vbat_v);

#define COLLAR_VBAT_EMPTY_V 3.10f

#ifdef __cplusplus
}
#endif

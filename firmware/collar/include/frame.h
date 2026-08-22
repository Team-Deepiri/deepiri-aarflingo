#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

typedef struct {
    int v;
    uint32_t ts_ms;
    float imu_rms;
    float imu_peak;
    float audio_rms;
    int bark;
    float vbat_v;
    int hr_bpm;
    int rmssd_ms;
    int ppg_ok;
    const char *fault; /* NULL or static string */
} CollarSample;

/* Compact diagnostic map (JSON text, Phase-2 keys). Fits BLE MTU-3. */
int collar_frame_encode(const CollarSample *s, uint8_t *buf, size_t cap);

int collar_frame_contains(const uint8_t *buf, int n, const char *key);

#ifdef __cplusplus
}
#endif

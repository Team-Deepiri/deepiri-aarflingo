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
    int still;
    int shake;
    int pant;
    float pitch;
    int rr_bpm;
    float pi;
    float arousal;
} CollarSample;

/* Compact CBOR map (Phase-2 keys). Fits BLE MTU-3. */
int collar_frame_encode(const CollarSample *s, uint8_t *buf, size_t cap);

int collar_frame_contains(const uint8_t *buf, int n, const char *key);

/* Decode our Phase-2 map. fault is copied into fault_buf (may be empty). */
int collar_frame_decode(const uint8_t *buf, int n, CollarSample *out, char *fault_buf,
                        size_t fault_cap);

#ifdef __cplusplus
}
#endif

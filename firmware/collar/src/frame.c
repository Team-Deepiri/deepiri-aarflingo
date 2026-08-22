#include "frame.h"

#include <stdio.h>
#include <string.h>

int collar_frame_encode(const CollarSample *s, uint8_t *buf, size_t cap) {
    if (s == NULL || buf == NULL || cap < 32) {
        return -1;
    }
    const char *fault = s->fault ? s->fault : "null";
    int n = snprintf(
        (char *)buf,
        cap,
        "{\"v\":%d,\"ts_ms\":%lu,\"imu_rms\":%.3f,\"imu_peak\":%.3f,"
        "\"audio_rms\":%.3f,\"bark\":%s,\"vbat_v\":%.2f,"
        "\"hr_bpm\":%d,\"rmssd_ms\":%d,\"ppg_ok\":%s,\"fault\":%s%s%s}",
        s->v,
        (unsigned long)s->ts_ms,
        (double)s->imu_rms,
        (double)s->imu_peak,
        (double)s->audio_rms,
        s->bark ? "true" : "false",
        (double)s->vbat_v,
        s->hr_bpm,
        s->rmssd_ms,
        s->ppg_ok ? "true" : "false",
        (s->fault && s->fault[0]) ? "\"" : "",
        (s->fault && s->fault[0]) ? fault : "null",
        (s->fault && s->fault[0]) ? "\"" : "");
    if (n < 0 || (size_t)n >= cap) {
        return -1;
    }
    return n;
}

int collar_frame_contains(const uint8_t *buf, int n, const char *key) {
    if (buf == NULL || key == NULL || n <= 0) {
        return 0;
    }
    size_t klen = strlen(key);
    for (int i = 0; i + (int)klen <= n; i++) {
        if (memcmp(buf + i, key, klen) == 0) {
            return 1;
        }
    }
    return 0;
}

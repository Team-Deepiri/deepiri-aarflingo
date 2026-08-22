#include "frame.h"

#include <string.h>

static int put(uint8_t *buf, size_t cap, int *n, uint8_t b) {
    if (*n < 0 || (size_t)*n >= cap) {
        *n = -1;
        return -1;
    }
    buf[(*n)++] = b;
    return 0;
}

static int put_bytes(uint8_t *buf, size_t cap, int *n, const uint8_t *p, size_t k) {
    for (size_t i = 0; i < k; i++) {
        if (put(buf, cap, n, p[i]) != 0) {
            return -1;
        }
    }
    return 0;
}

static int put_uint(uint8_t *buf, size_t cap, int *n, uint32_t v) {
    if (v < 24) {
        return put(buf, cap, n, (uint8_t)v);
    }
    if (v < 256) {
        return put(buf, cap, n, 0x18) || put(buf, cap, n, (uint8_t)v);
    }
    if (v < 65536) {
        return put(buf, cap, n, 0x19) || put(buf, cap, n, (uint8_t)(v >> 8)) ||
               put(buf, cap, n, (uint8_t)v);
    }
    return put(buf, cap, n, 0x1A) || put(buf, cap, n, (uint8_t)(v >> 24)) ||
           put(buf, cap, n, (uint8_t)(v >> 16)) || put(buf, cap, n, (uint8_t)(v >> 8)) ||
           put(buf, cap, n, (uint8_t)v);
}

static int put_text(uint8_t *buf, size_t cap, int *n, const char *s) {
    size_t k = strlen(s);
    if (k >= 24) {
        return -1;
    }
    if (put(buf, cap, n, (uint8_t)(0x60 + k)) != 0) {
        return -1;
    }
    return put_bytes(buf, cap, n, (const uint8_t *)s, k);
}

static int put_f32(uint8_t *buf, size_t cap, int *n, float f) {
    union {
        float f;
        uint32_t u;
    } conv;
    conv.f = f;
    if (put(buf, cap, n, 0xFA) != 0) {
        return -1;
    }
    return put(buf, cap, n, (uint8_t)(conv.u >> 24)) || put(buf, cap, n, (uint8_t)(conv.u >> 16)) ||
           put(buf, cap, n, (uint8_t)(conv.u >> 8)) || put(buf, cap, n, (uint8_t)conv.u);
}

int collar_frame_encode(const CollarSample *s, uint8_t *buf, size_t cap) {
    if (s == NULL || buf == NULL || cap < 32) {
        return -1;
    }
    int n = 0;
    /* 12-key map */
    if (put(buf, cap, &n, 0xAC) != 0) {
        return -1;
    }
    if (put_text(buf, cap, &n, "source") || put_text(buf, cap, &n, "sensors")) {
        return -1;
    }
    if (put_text(buf, cap, &n, "v") || put_uint(buf, cap, &n, (uint32_t)s->v)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "ts_ms") || put_uint(buf, cap, &n, s->ts_ms)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "imu_rms") || put_f32(buf, cap, &n, s->imu_rms)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "imu_peak") || put_f32(buf, cap, &n, s->imu_peak)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "audio_rms") || put_f32(buf, cap, &n, s->audio_rms)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "bark") || put(buf, cap, &n, s->bark ? 0xF5 : 0xF4)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "vbat_v") || put_f32(buf, cap, &n, s->vbat_v)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "hr_bpm") || put_uint(buf, cap, &n, (uint32_t)s->hr_bpm)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "rmssd_ms") || put_uint(buf, cap, &n, (uint32_t)s->rmssd_ms)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "ppg_ok") || put(buf, cap, &n, s->ppg_ok ? 0xF5 : 0xF4)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "fault") != 0) {
        return -1;
    }
    if (s->fault && s->fault[0]) {
        if (put_text(buf, cap, &n, s->fault) != 0) {
            return -1;
        }
    } else if (put(buf, cap, &n, 0xF6) != 0) {
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

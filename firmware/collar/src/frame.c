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
    /* 19-key map: sensors + ethogram/autonomic proxies */
    if (put(buf, cap, &n, 0xB3) != 0) {
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
    if (put_text(buf, cap, &n, "still") || put(buf, cap, &n, s->still ? 0xF5 : 0xF4)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "shake") || put(buf, cap, &n, s->shake ? 0xF5 : 0xF4)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "pant") || put(buf, cap, &n, s->pant ? 0xF5 : 0xF4)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "pitch") || put_f32(buf, cap, &n, s->pitch)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "rr_bpm") || put_uint(buf, cap, &n, (uint32_t)s->rr_bpm)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "pi") || put_f32(buf, cap, &n, s->pi)) {
        return -1;
    }
    if (put_text(buf, cap, &n, "arousal") || put_f32(buf, cap, &n, s->arousal)) {
        return -1;
    }
    return n;
}

static int take(const uint8_t *b, int n, int *i, uint8_t *out) {
    if (*i < 0 || *i >= n) {
        return -1;
    }
    *out = b[(*i)++];
    return 0;
}

static int parse_uint(const uint8_t *b, int n, int *i, uint32_t *out) {
    uint8_t t;
    if (take(b, n, i, &t) != 0) {
        return -1;
    }
    if ((t >> 5) != 0) {
        return -1;
    }
    unsigned ai = (unsigned)(t & 0x1F);
    if (ai < 24) {
        *out = ai;
        return 0;
    }
    if (ai == 24) {
        uint8_t v;
        if (take(b, n, i, &v) != 0) {
            return -1;
        }
        *out = v;
        return 0;
    }
    if (ai == 25) {
        uint8_t hi, lo;
        if (take(b, n, i, &hi) != 0 || take(b, n, i, &lo) != 0) {
            return -1;
        }
        *out = ((uint32_t)hi << 8) | lo;
        return 0;
    }
    if (ai == 26) {
        uint8_t a, c, d, e;
        if (take(b, n, i, &a) || take(b, n, i, &c) || take(b, n, i, &d) || take(b, n, i, &e)) {
            return -1;
        }
        *out = ((uint32_t)a << 24) | ((uint32_t)c << 16) | ((uint32_t)d << 8) | e;
        return 0;
    }
    return -1;
}

static int parse_text(const uint8_t *b, int n, int *i, char *out, size_t cap) {
    uint8_t t;
    if (take(b, n, i, &t) != 0) {
        return -1;
    }
    if ((t >> 5) != 3) {
        return -1;
    }
    unsigned len = (unsigned)(t & 0x1F);
    if (len >= 24 || len + 1 > cap || *i + (int)len > n) {
        return -1;
    }
    memcpy(out, b + *i, len);
    out[len] = '\0';
    *i += (int)len;
    return 0;
}

static int skip_value(const uint8_t *b, int n, int *i) {
    if (*i >= n) {
        return -1;
    }
    uint8_t t = b[*i];
    unsigned mt = (unsigned)(t >> 5);
    unsigned ai = (unsigned)(t & 0x1F);
    if (t == 0xF4 || t == 0xF5 || t == 0xF6) {
        (*i)++;
        return 0;
    }
    if (t == 0xFA) {
        *i += 5;
        return *i <= n ? 0 : -1;
    }
    if (mt == 0 || mt == 3) {
        (*i)++;
        if (ai < 24) {
            *i += (int)ai;
            return *i <= n ? 0 : -1;
        }
        if (ai == 24) {
            if (*i >= n) {
                return -1;
            }
            unsigned extra = b[(*i)++];
            *i += (int)extra;
            return *i <= n ? 0 : -1;
        }
    }
    return -1;
}

int collar_frame_decode(const uint8_t *buf, int n, CollarSample *out, char *fault_buf,
                        size_t fault_cap) {
    if (buf == NULL || out == NULL || n < 2 || (buf[0] & 0xE0) != 0xA0) {
        return -1;
    }
    memset(out, 0, sizeof *out);
    if (fault_buf && fault_cap) {
        fault_buf[0] = '\0';
    }
    int pairs = buf[0] & 0x1F;
    int i = 1;
    for (int p = 0; p < pairs; p++) {
        char key[24];
        if (parse_text(buf, n, &i, key, sizeof key) != 0) {
            return -1;
        }
        if (strcmp(key, "v") == 0 || strcmp(key, "ts_ms") == 0 || strcmp(key, "hr_bpm") == 0 ||
            strcmp(key, "rmssd_ms") == 0 || strcmp(key, "rr_bpm") == 0) {
            uint32_t v = 0;
            if (parse_uint(buf, n, &i, &v) != 0) {
                return -1;
            }
            if (key[0] == 'v' && key[1] == '\0') {
                out->v = (int)v;
            } else if (key[0] == 't') {
                out->ts_ms = v;
            } else if (key[0] == 'h') {
                out->hr_bpm = (int)v;
            } else if (key[0] == 'r' && key[1] == 'r') {
                out->rr_bpm = (int)v;
            } else {
                out->rmssd_ms = (int)v;
            }
        } else if (strcmp(key, "bark") == 0 || strcmp(key, "ppg_ok") == 0 ||
                   strcmp(key, "still") == 0 || strcmp(key, "shake") == 0 ||
                   strcmp(key, "pant") == 0) {
            uint8_t t;
            if (take(buf, n, &i, &t) != 0) {
                return -1;
            }
            int on = (t == 0xF5);
            if (key[0] == 'b') {
                out->bark = on;
            } else if (key[0] == 'p' && key[1] == 'p') {
                out->ppg_ok = on;
            } else if (key[0] == 's' && key[1] == 't') {
                out->still = on;
            } else if (key[0] == 's') {
                out->shake = on;
            } else {
                out->pant = on;
            }
        } else if (strcmp(key, "imu_rms") == 0 || strcmp(key, "imu_peak") == 0 ||
                   strcmp(key, "audio_rms") == 0 || strcmp(key, "vbat_v") == 0 ||
                   strcmp(key, "pitch") == 0 || strcmp(key, "pi") == 0 ||
                   strcmp(key, "arousal") == 0) {
            uint8_t t;
            if (take(buf, n, &i, &t) != 0 || t != 0xFA || i + 4 > n) {
                return -1;
            }
            uint32_t u = ((uint32_t)buf[i] << 24) | ((uint32_t)buf[i + 1] << 16) |
                         ((uint32_t)buf[i + 2] << 8) | (uint32_t)buf[i + 3];
            i += 4;
            union {
                float f;
                uint32_t u;
            } conv;
            conv.u = u;
            if (key[0] == 'v') {
                out->vbat_v = conv.f;
            } else if (key[0] == 'p' && key[1] == 'i' && key[2] == '\0') {
                out->pi = conv.f;
            } else if (key[0] == 'p') {
                out->pitch = conv.f;
            } else if (key[0] == 'a' && key[1] == 'r') {
                out->arousal = conv.f;
            } else if (key[4] == 'r') {
                out->imu_rms = conv.f;
            } else if (key[4] == 'p') {
                out->imu_peak = conv.f;
            } else {
                out->audio_rms = conv.f;
            }
        } else if (strcmp(key, "fault") == 0) {
            if (i < n && buf[i] == 0xF6) {
                i++;
            } else if (fault_buf && fault_cap) {
                if (parse_text(buf, n, &i, fault_buf, fault_cap) != 0) {
                    return -1;
                }
                out->fault = fault_buf;
            } else if (skip_value(buf, n, &i) != 0) {
                return -1;
            }
        } else if (skip_value(buf, n, &i) != 0) {
            return -1;
        }
    }
    return 0;
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

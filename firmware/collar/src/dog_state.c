#include "dog_state.h"

#include "audio_feat.h"
#include "imu_feat.h"

#include <math.h>

static float clampf(float x, float lo, float hi) {
    if (x < lo) {
        return lo;
    }
    if (x > hi) {
        return hi;
    }
    return x;
}

int dog_still(float dyn_g, float peak_g, int have_xyz) {
    if (have_xyz) {
        return dyn_g < 0.08f && peak_g < 1.35f;
    }
    return dyn_g < 0.35f && peak_g < 0.60f;
}

int dog_shake(float peak_g) {
    return peak_g > 2.60f;
}

int dog_pant(float audio_rms, int bark, float zcr) {
    if (bark) {
        return 0;
    }
    return audio_rms > 0.015f && zcr > 0.45f;
}

int dog_rr_from_ir(const int32_t *ir, size_t n, int fs_hz, int still) {
    if (!still || ir == NULL || n < 16 || fs_hz < 10) {
        return 0;
    }
    int64_t sum = 0;
    for (size_t i = 0; i < n; i++) {
        sum += ir[i];
    }
    int32_t mean = (int32_t)(sum / (int64_t)n);
    int crossings = 0;
    int prev = 0;
    for (size_t i = 1; i < n; i++) {
        int cur = ir[i] > mean ? 1 : -1;
        if (prev != 0 && cur != prev) {
            crossings++;
        }
        prev = cur;
    }
    float sec = (float)n / (float)fs_hz;
    if (sec < 0.4f) {
        return 0;
    }
    int rr = (int)lround((float)crossings / 2.0f / sec * 60.0f);
    if (rr < 8 || rr > 80) {
        return 0;
    }
    return rr;
}

float dog_perfusion(const int32_t *ir, size_t n) {
    if (ir == NULL || n < 8) {
        return 0.0f;
    }
    int32_t mn = ir[0];
    int32_t mx = ir[0];
    int64_t sum = 0;
    for (size_t i = 0; i < n; i++) {
        if (ir[i] < mn) {
            mn = ir[i];
        }
        if (ir[i] > mx) {
            mx = ir[i];
        }
        sum += ir[i];
    }
    float mean = (float)sum / (float)n;
    if (mean < 1.0f && mean > -1.0f) {
        return 0.0f;
    }
    return clampf((float)(mx - mn) / fabsf(mean), 0.0f, 2.0f);
}

float dog_arousal(int hr_bpm, int rmssd_ms, int still, int pant, int bark, float dyn_g) {
    float a = 0.0f;
    if (hr_bpm > 0) {
        a += 0.35f * clampf((float)(hr_bpm - 50) / 100.0f, 0.0f, 1.0f);
    }
    if (rmssd_ms > 0) {
        a += 0.25f * clampf(1.0f - (float)rmssd_ms / 100.0f, 0.0f, 1.0f);
    }
    if (pant) {
        a += 0.15f;
    }
    if (bark) {
        a += 0.15f;
    }
    if (!still) {
        a += 0.10f * clampf(dyn_g / 0.40f, 0.0f, 1.0f);
    }
    return clampf(a, 0.0f, 1.0f);
}

void dog_state_fill(CollarSample *s, const float *xyz, size_t nimu, const int32_t *pcm, size_t npcm,
                    const int32_t *ir, size_t nir, const int32_t *red, size_t nred, int fs_hz) {
    if (s == NULL) {
        return;
    }
    int have_xyz = xyz != NULL && nimu > 0;
    float dyn = have_xyz ? imu_dyn_g(xyz, nimu) : s->imu_rms;
    float peak = have_xyz ? imu_peak_g(xyz, nimu) : s->imu_peak;
    s->still = dog_still(dyn, peak, have_xyz);
    s->shake = dog_shake(peak);
    s->pitch = have_xyz ? imu_pitch_deg(xyz, nimu) : 0.0f;
    float zcr = audio_zcr(pcm, npcm);
    s->pant = dog_pant(s->audio_rms, s->bark, zcr);
    s->rr_bpm = dog_rr_from_ir(ir, nir, fs_hz, s->still);
    s->pi = dog_perfusion(ir, nir);
    s->red = dog_perfusion(red, nred);
    s->arousal = dog_arousal(s->hr_bpm, s->rmssd_ms, s->still, s->pant, s->bark, dyn);
}

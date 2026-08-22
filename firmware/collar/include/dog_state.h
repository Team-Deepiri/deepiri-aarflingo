#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include "frame.h"

#include <stddef.h>
#include <stdint.h>

/* Neck-measurable ethogram + autonomic proxies. Not blood chemistry. */
int dog_still(float dyn_g, float peak_g, int have_xyz);
int dog_shake(float peak_g);
int dog_pant(float audio_rms, int bark, float zcr);
int dog_rr_from_ir(const int32_t *ir, size_t n, int fs_hz, int still);
float dog_perfusion(const int32_t *ir, size_t n);
float dog_arousal(int hr_bpm, int rmssd_ms, int still, int pant, int bark, float dyn_g);
void dog_state_fill(CollarSample *s, const float *xyz, size_t nimu, const int32_t *pcm, size_t npcm,
                    const int32_t *ir, size_t nir, int fs_hz);

#ifdef __cplusplus
}
#endif

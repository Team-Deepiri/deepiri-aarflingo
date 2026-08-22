#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

float audio_rms(const int32_t *s, size_t n);
int audio_bark(float rms, float thresh);

#ifdef __cplusplus
}
#endif

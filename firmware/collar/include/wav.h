#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

/* Mono PCM16 WAV. Returns bytes written or -1. */
int collar_wav_pcm16(uint8_t *out, size_t cap, const int16_t *pcm, size_t n, int fs);

#ifdef __cplusplus
}
#endif

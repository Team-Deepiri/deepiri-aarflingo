#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

/* Existing runtime contract: POST /infer/audio JSON. */
int collar_clip_should_upload(int bark, int wifi_ok);
int collar_audio_body(char *buf, size_t cap, float arousal, float valence, float bark_prob);

#ifdef __cplusplus
}
#endif

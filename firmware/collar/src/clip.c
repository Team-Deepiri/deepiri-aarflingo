#include "clip.h"

#include <stdio.h>

int collar_clip_should_upload(int bark, int wifi_ok) {
    return bark && wifi_ok;
}

int collar_audio_body(char *buf, size_t cap, float arousal, float valence, float bark_prob) {
    if (buf == NULL || cap < 32) {
        return -1;
    }
    int n = snprintf(
        buf,
        cap,
        "{\"audio_arousal\":%.3f,\"audio_valence\":%.3f,\"audio_bark_prob\":%.3f}",
        (double)arousal,
        (double)valence,
        (double)bark_prob);
    if (n < 0 || (size_t)n >= cap) {
        return -1;
    }
    return n;
}

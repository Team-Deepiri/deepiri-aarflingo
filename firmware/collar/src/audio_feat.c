#include "audio_feat.h"

#include <math.h>

float audio_rms(const int32_t *s, size_t n) {
    if (s == NULL || n == 0) {
        return 0.0f;
    }
    double acc = 0.0;
    for (size_t i = 0; i < n; i++) {
        double v = (double)s[i];
        acc += v * v;
    }
    return (float)sqrt(acc / (double)n);
}

int audio_bark(float rms, float thresh) {
    return rms > thresh ? 1 : 0;
}

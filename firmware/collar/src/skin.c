#include "skin.h"

#include <math.h>

float skin_c_from_raw(int raw, int fullscale) {
    if (raw <= 0 || fullscale <= raw) {
        return 0.0f;
    }
    float vfrac = (float)raw / (float)fullscale;
    float r = SKIN_R_FIXED_OHMS * vfrac / (1.0f - vfrac);
    if (r <= 0.0f) {
        return 0.0f;
    }
    float inv = (1.0f / SKIN_T25_K) + (1.0f / SKIN_BETA) * logf(r / SKIN_R25_OHMS);
    return (1.0f / inv) - 273.15f;
}

#include "vbat.h"

float vbat_from_raw(int raw, int full_scale, float vref, float scale, float offset) {
    if (full_scale <= 0 || vref <= 0.0f) {
        return 0.0f;
    }
    if (raw < 0) {
        raw = 0;
    }
    if (raw > full_scale) {
        raw = full_scale;
    }
    float vadc = ((float)raw / (float)full_scale) * vref;
    return 2.0f * vadc * scale + offset;
}

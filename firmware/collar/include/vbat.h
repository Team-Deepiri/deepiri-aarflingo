#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float scale;
    float offset;
} VbatCal;

#define VBAT_CAL_DEFAULT_SCALE 1.0f
#define VBAT_CAL_DEFAULT_OFFSET 0.0f

/* Equal 100k/100k divider: Vbat = 2 * Vadc * scale + offset. */
float vbat_from_raw(int raw, int full_scale, float vref, float scale, float offset);

VbatCal vbat_cal_default(void);

#ifdef __cplusplus
}
#endif

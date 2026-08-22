#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Equal 100k/100k divider: Vbat = 2 * Vadc * scale + offset. */
float vbat_from_raw(int raw, int full_scale, float vref, float scale, float offset);

#ifdef __cplusplus
}
#endif

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* 10 kΩ NTC β=3950, 10 kΩ to 3V3, GPIO10 ADC1. Neck contact, not core temp. */
#define SKIN_ADC_GPIO 10
#define SKIN_R_FIXED_OHMS 10000.0f
#define SKIN_R25_OHMS 10000.0f
#define SKIN_BETA 3950.0f
#define SKIN_T25_K 298.15f

float skin_c_from_raw(int raw, int fullscale);

#ifdef __cplusplus
}
#endif

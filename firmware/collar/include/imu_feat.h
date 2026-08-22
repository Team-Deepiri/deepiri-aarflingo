#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

/* xyz is n_samples * 3 floats in g. Returns RMS of vector magnitude. */
float imu_rms_g(const float *xyz, size_t n_samples);
float imu_peak_g(const float *xyz, size_t n_samples);

#ifdef __cplusplus
}
#endif

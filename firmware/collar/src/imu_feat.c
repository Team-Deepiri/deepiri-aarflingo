#include "imu_feat.h"

#include <math.h>

float imu_rms_g(const float *xyz, size_t n_samples) {
    if (xyz == NULL || n_samples == 0) {
        return 0.0f;
    }
    double acc = 0.0;
    for (size_t i = 0; i < n_samples; i++) {
        double x = (double)xyz[3 * i];
        double y = (double)xyz[3 * i + 1];
        double z = (double)xyz[3 * i + 2];
        acc += x * x + y * y + z * z;
    }
    return (float)sqrt(acc / (double)n_samples);
}

float imu_peak_g(const float *xyz, size_t n_samples) {
    if (xyz == NULL || n_samples == 0) {
        return 0.0f;
    }
    double peak = 0.0;
    for (size_t i = 0; i < n_samples; i++) {
        double x = (double)xyz[3 * i];
        double y = (double)xyz[3 * i + 1];
        double z = (double)xyz[3 * i + 2];
        double mag = sqrt(x * x + y * y + z * z);
        if (mag > peak) {
            peak = mag;
        }
    }
    return (float)peak;
}

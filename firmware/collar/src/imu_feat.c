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

float imu_dyn_g(const float *xyz, size_t n_samples) {
    if (xyz == NULL || n_samples == 0) {
        return 0.0f;
    }
    double acc = 0.0;
    for (size_t i = 0; i < n_samples; i++) {
        double x = (double)xyz[3 * i];
        double y = (double)xyz[3 * i + 1];
        double z = (double)xyz[3 * i + 2];
        double mag = sqrt(x * x + y * y + z * z);
        double d = mag - 1.0;
        acc += d * d;
    }
    return (float)sqrt(acc / (double)n_samples);
}

float imu_pitch_deg(const float *xyz, size_t n_samples) {
    if (xyz == NULL || n_samples == 0) {
        return 0.0f;
    }
    double mx = 0.0, my = 0.0, mz = 0.0;
    for (size_t i = 0; i < n_samples; i++) {
        mx += (double)xyz[3 * i];
        my += (double)xyz[3 * i + 1];
        mz += (double)xyz[3 * i + 2];
    }
    mx /= (double)n_samples;
    my /= (double)n_samples;
    mz /= (double)n_samples;
    return (float)(atan2(-mx, sqrt(my * my + mz * mz)) * (180.0 / 3.141592653589793));
}

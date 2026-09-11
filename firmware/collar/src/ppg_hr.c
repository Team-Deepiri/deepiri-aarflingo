#include "ppg_hr.h"

#include <math.h>
#include <stdlib.h>

#define MAX_PEAKS 32

PpgHr ppg_hr_from_ir(const int32_t *ir, size_t n, int fs_hz) {
    PpgHr out = {0, 0, 0};
    if (ir == NULL || n < 8 || fs_hz < 10) {
        return out;
    }

    int64_t sum = 0;
    for (size_t i = 0; i < n; i++) {
        sum += ir[i];
    }
    int32_t mean = (int32_t)(sum / (int64_t)n);

    double var = 0.0;
    for (size_t i = 0; i < n; i++) {
        double d = (double)(ir[i] - mean);
        var += d * d;
    }
    double sd = sqrt(var / (double)n);
    int32_t thresh = mean + (int32_t)(0.25 * sd);
    if (thresh <= mean) {
        thresh = mean + 1;
    }

    int min_gap = fs_hz / 4; /* 240 bpm cap */
    if (min_gap < 2) {
        min_gap = 2;
    }

    int peaks[MAX_PEAKS];
    int np = 0;
    int last = -min_gap;
    for (size_t i = 1; i + 1 < n && np < MAX_PEAKS; i++) {
        if (ir[i] >= ir[i - 1] && ir[i] > ir[i + 1] && ir[i] > thresh) {
            if ((int)i - last >= min_gap) {
                peaks[np++] = (int)i;
                last = (int)i;
            }
        }
    }
    if (np < 3) {
        return out;
    }

    double rr_ms[MAX_PEAKS];
    int nrr = np - 1;
    double rr_sum = 0.0;
    for (int k = 0; k < nrr; k++) {
        rr_ms[k] = 1000.0 * (double)(peaks[k + 1] - peaks[k]) / (double)fs_hz;
        rr_sum += rr_ms[k];
    }
    double rr_mean = rr_sum / (double)nrr;
    if (rr_mean < 250.0 || rr_mean > 2000.0) {
        return out;
    }

    double sdsum = 0.0;
    if (nrr >= 2) {
        for (int k = 1; k < nrr; k++) {
            double d = rr_ms[k] - rr_ms[k - 1];
            sdsum += d * d;
        }
        out.rmssd_ms = (int)lround(sqrt(sdsum / (double)(nrr - 1)));
    }
    out.hr_bpm = (int)lround(60000.0 / rr_mean);
    out.ok = 1;
    return out;
}

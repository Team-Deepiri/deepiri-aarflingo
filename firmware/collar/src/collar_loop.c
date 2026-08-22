#include "collar_loop.h"

#include "dog_state.h"
#include "ppg_hr.h"

#include <string.h>

void collar_loop_init(CollarLoop *L) {
    if (L == NULL) {
        return;
    }
    memset(L, 0, sizeof *L);
    L->state = COLLAR_IDLE;
    L->last.v = 1;
}

int collar_loop_step(CollarLoop *L, const int32_t *ir, size_t n, int fs_hz,
                     float imu_rms, float imu_peak, float audio_rms, int bark,
                     float vbat_v, int imu_ok, int mic_ok, const float *xyz, size_t nimu,
                     const int32_t *pcm, size_t npcm) {
    if (L == NULL) {
        return -1;
    }
    L->state = COLLAR_SAMPLE;
    L->last.v = 1;
    L->last.imu_rms = imu_rms;
    L->last.imu_peak = imu_peak;
    L->last.audio_rms = audio_rms;
    L->last.bark = bark;
    L->last.vbat_v = vbat_v;
    L->last.fault = NULL;

    PpgHr hr = ppg_hr_from_ir(ir, n, fs_hz);
    L->last.ppg_ok = hr.ok;
    L->last.hr_bpm = hr.ok ? hr.hr_bpm : 0;
    L->last.rmssd_ms = hr.ok ? hr.rmssd_ms : 0;
    if (vbat_v < COLLAR_VBAT_EMPTY_V) {
        L->last.fault = "vbat";
    } else if (!imu_ok) {
        L->last.fault = "imu";
    } else if (!mic_ok) {
        L->last.fault = "mic";
    } else if (!hr.ok) {
        L->last.fault = "ppg";
    }

    dog_state_fill(&L->last, xyz, nimu, pcm, npcm, ir, n, fs_hz);

    L->state = COLLAR_TRANSMIT;
    L->tx_len = collar_frame_encode(&L->last, L->tx, sizeof L->tx);
    L->state = COLLAR_IDLE;
    return L->tx_len;
}

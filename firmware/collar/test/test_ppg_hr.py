"""Host tests for collar DSP — written first (TDD)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

COLLAR = Path(__file__).resolve().parents[1]
SRC = COLLAR / "src"


def _compile_and_run(sources: list[Path], extra_c: str, bin_name: str, tmp_path: Path) -> str:
    driver = tmp_path / "driver.c"
    driver.write_text(extra_c, encoding="utf-8")
    out = tmp_path / bin_name
    cmd = [
        "gcc",
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-I",
        str(COLLAR / "include"),
        "-o",
        str(out),
        str(driver),
        *[str(p) for p in sources],
        "-lm",
    ]
    built = subprocess.run(cmd, capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    ran = subprocess.run([str(out)], capture_output=True, text=True)
    assert ran.returncode == 0, ran.stderr + ran.stdout
    return ran.stdout


def test_ppg_hr_near_120bpm_on_synthetic_sine(tmp_path):
    src = SRC / "ppg_hr.c"
    if not src.is_file():
        pytest.fail("ppg_hr.c missing — implement after this red test")
    extra = r"""
#include "ppg_hr.h"
#include <math.h>
#include <stdio.h>
int main(void) {
    enum { N = 500, FS = 50 };
    int32_t ir[N];
    for (int i = 0; i < N; i++) {
        double t = (double)i / FS;
        ir[i] = (int32_t)(10000.0 + 2000.0 * sin(2.0 * 3.141592653589793 * 2.0 * t));
    }
    PpgHr out = ppg_hr_from_ir(ir, N, FS);
    printf("%d %d %d\n", out.ok, out.hr_bpm, out.rmssd_ms);
    return (out.ok && out.hr_bpm >= 110 && out.hr_bpm <= 130) ? 0 : 2;
}
"""
    _compile_and_run([src], extra, "test_ppg", tmp_path)


def test_cbor_frame_contains_required_keys_and_hr(tmp_path):
    src = SRC / "frame.c"
    if not src.is_file():
        pytest.fail("frame.c missing — implement after this red test")
    extra = r"""
#include "frame.h"
#include <stdio.h>
#include <string.h>
int main(void) {
    CollarSample s = {0};
    s.v = 1;
    s.ts_ms = 1000;
    s.imu_rms = 0.12f;
    s.imu_peak = 0.40f;
    s.audio_rms = 0.01f;
    s.bark = 0;
    s.vbat_v = 3.80f;
    s.hr_bpm = 96;
    s.rmssd_ms = 42;
    s.ppg_ok = 1;
    uint8_t buf[256];
    int n = collar_frame_encode(&s, buf, sizeof buf);
    if (n < 20) return 2;
    if ((buf[0] & 0xE0) != 0xA0) return 7;
    if (!collar_frame_contains(buf, n, "hr_bpm")) return 3;
    if (!collar_frame_contains(buf, n, "rmssd_ms")) return 4;
    if (!collar_frame_contains(buf, n, "vbat_v")) return 5;
    if (n > 200) return 6;
    printf("%d\n", n);
    return 0;
}
"""
    _compile_and_run([src], extra, "test_frame", tmp_path)


def test_pins_h_has_ppg_rdy_and_rst():
    pins = Path(__file__).resolve().parents[3] / "hardware" / "collar-reva" / "pins.h"
    text = pins.read_text(encoding="utf-8")
    assert "#define PIN_PPG_RDY" in text
    assert "#define PIN_PPG_RST" in text


def test_afe4404_be24_twos_complement(tmp_path):
    src = SRC / "afe4404.c"
    extra = r"""
#include "afe4404.h"
#include <stdint.h>
int main(void) {
    uint8_t pos[3] = {0x00, 0x00, 0x64};
    uint8_t neg[3] = {0xFF, 0xFF, 0xFF};
    if (afe4404_sample_from_be24(pos) != 100) return 2;
    if (afe4404_sample_from_be24(neg) != -1) return 3;
    if (AFE4404_I2C_ADDR != 0x58) return 4;
    return 0;
}
"""
    _compile_and_run([src], extra, "test_afe", tmp_path)


def test_collar_loop_emits_hr_and_returns_to_idle(tmp_path):
    extra = r"""
#include "collar_loop.h"
#include <math.h>
int main(void) {
    enum { N = 500, FS = 50 };
    int32_t ir[N];
    for (int i = 0; i < N; i++) {
        double t = (double)i / FS;
        ir[i] = (int32_t)(10000.0 + 2000.0 * sin(2.0 * 3.141592653589793 * 2.0 * t));
    }
    CollarLoop L;
    collar_loop_init(&L);
    int n = collar_loop_step(&L, ir, N, FS, 0.1f, 0.2f, 0.01f, 0, 3.8f, 1, 1);
    if (n < 20) return 2;
    if (L.state != COLLAR_IDLE) return 3;
    if (!L.last.ppg_ok) return 4;
    if (L.last.hr_bpm < 110 || L.last.hr_bpm > 130) return 5;
    if (!collar_frame_contains(L.tx, n, "hr_bpm")) return 6;
    return 0;
}
"""
    _compile_and_run(
        [SRC / "ppg_hr.c", SRC / "frame.c", SRC / "collar_loop.c"],
        extra,
        "test_loop",
        tmp_path,
    )


def test_imu_rms_and_peak_on_unit_vector(tmp_path):
    extra = r"""
#include "imu_feat.h"
int main(void) {
    float xyz[6] = {1.f, 0.f, 0.f, 0.f, 0.f, 1.f};
    float rms = imu_rms_g(xyz, 2);
    float peak = imu_peak_g(xyz, 2);
    if (rms < 0.99f || rms > 1.01f) return 2;
    if (peak < 0.99f || peak > 1.01f) return 3;
    return 0;
}
"""
    _compile_and_run([SRC / "imu_feat.c"], extra, "test_imu", tmp_path)


def test_bmi270_lsb_to_g_full_scale(tmp_path):
    extra = r"""
#include "bmi270.h"
int main(void) {
    if (BMI270_I2C_ADDR != 0x68) return 2;
    if (BMI270_CHIP_ID != 0x24) return 3;
    float g = bmi270_lsb_to_g(32767);
    if (g < 7.99f || g > 8.01f) return 4;
    if (bmi270_lsb_to_g(0) != 0.f) return 5;
    if (!bmi270_chip_ok(0x24)) return 6;
    if (bmi270_chip_ok(0x00)) return 7;
    if (BMI270_ACC_RANGE_8G != 0x02) return 8;
    if (BMI270_PWR_ACC_EN != 0x04) return 9;
    return 0;
}
"""
    _compile_and_run([SRC / "bmi270.c"], extra, "test_bmi", tmp_path)


def test_audio_rms_and_bark(tmp_path):
    extra = r"""
#include "audio_feat.h"
int main(void) {
    int32_t s[4] = {3, 0, -4, 0};
    float r = audio_rms(s, 4);
    if (r < 2.49f || r > 2.51f) return 2;
    if (!audio_bark(0.05f, 0.02f)) return 3;
    if (audio_bark(0.01f, 0.02f)) return 4;
    return 0;
}
"""
    _compile_and_run([SRC / "audio_feat.c"], extra, "test_audio", tmp_path)


def test_collar_loop_vbat_fault_wins_over_ppg(tmp_path):
    extra = r"""
#include "collar_loop.h"
#include <string.h>
int main(void) {
    int32_t ir[8] = {0};
    CollarLoop L;
    collar_loop_init(&L);
    int n = collar_loop_step(&L, ir, 8, 50, 0.1f, 0.2f, 0.01f, 0, 3.00f, 1, 1);
    if (n < 10) return 2;
    if (L.last.fault == NULL || strcmp(L.last.fault, "vbat") != 0) return 3;
    return 0;
}
"""
    _compile_and_run(
        [SRC / "ppg_hr.c", SRC / "frame.c", SRC / "collar_loop.c"],
        extra,
        "test_vbat_fault",
        tmp_path,
    )


def test_vbat_midscale_is_3v1_times_two(tmp_path):
    extra = r"""
#include "vbat.h"
int main(void) {
    float v = vbat_from_raw(2048, 4095, 3.10f, 1.0f, 0.0f);
    if (v < 3.09f || v > 3.11f) return 2;
    VbatCal c = vbat_cal_default();
    if (c.scale != 1.0f || c.offset != 0.0f) return 3;
    return 0;
}
"""
    _compile_and_run([SRC / "vbat.c"], extra, "test_vbat", tmp_path)


def test_ble_pack_fits_mtu_minus_three(tmp_path):
    extra = r"""
#include "ble_tx.h"
#include <string.h>
int main(void) {
    uint8_t in[40];
    uint8_t out[40];
    memset(in, 0xAB, sizeof in);
    int n = collar_ble_pack(in, 40, out, sizeof out, 23);
    if (n != 20) return 2;
    int m = collar_ble_pack(in, 10, out, sizeof out, COLLAR_BLE_MTU);
    if (m != 10) return 3;
    return 0;
}
"""
    _compile_and_run([SRC / "ble_tx.c"], extra, "test_ble_tx", tmp_path)


def test_ble_gatt_is_notify_only_and_named(tmp_path):
    extra = r"""
#include "ble_link.h"
#include <string.h>
int main(void) {
    if (strcmp(COLLAR_BLE_ADV_NAME, "aarf-collar") != 0) return 2;
    if (COLLAR_GATT_NOTIFY_PROPS != 0x10) return 3;
    if (COLLAR_GATT_WRITE_PROPS != 0) return 4;
    if (COLLAR_BLE_MTU != 247) return 5;
    return 0;
}
"""
    _compile_and_run([], extra, "test_gatt", tmp_path)


def test_ble_radio_source_has_no_write_char():
    radio = COLLAR / "src" / "ble_radio.cpp"
    if not radio.is_file():
        pytest.fail("ble_radio.cpp missing — implement after this red test")
    text = radio.read_text(encoding="utf-8")
    assert "NOTIFY" in text
    assert "setMTU" in text
    assert "WRITE" not in text
    assert "SHOCK" not in text


def test_led_period_matches_fault_table(tmp_path):
    src = SRC / "led_stat.c"
    if not src.is_file():
        pytest.fail("led_stat.c missing — implement after this red test")
    extra = r"""
#include "led_stat.h"
#include <stddef.h>
int main(void) {
    if (collar_led_period_ms(NULL) != 10) return 2;
    if (collar_led_period_ms("ppg") != 500) return 3;
    if (collar_led_period_ms("imu") != 500) return 4;
    if (collar_led_period_ms("mic") != 500) return 5;
    if (collar_led_period_ms("vbat") != 0) return 6;
    return 0;
}
"""
    _compile_and_run([src], extra, "test_led", tmp_path)


def test_wdt_is_longer_than_clip(tmp_path):
    extra = r"""
#include "wdt.h"
int main(void) {
    if (COLLAR_CLIP_BUDGET_S >= COLLAR_WDT_S) return 2;
    if (COLLAR_WDT_S < 20) return 3;
    return 0;
}
"""
    _compile_and_run([], extra, "test_wdt", tmp_path)


def test_collar_loop_imu_fault_beats_ppg(tmp_path):
    extra = r"""
#include "collar_loop.h"
#include <string.h>
int main(void) {
    int32_t ir[8] = {0};
    CollarLoop L;
    collar_loop_init(&L);
    int n = collar_loop_step(&L, ir, 8, 50, 0.f, 0.f, 0.01f, 0, 3.80f, 0, 1);
    if (n < 10) return 2;
    if (L.last.fault == NULL || strcmp(L.last.fault, "imu") != 0) return 3;
    return 0;
}
"""
    _compile_and_run(
        [SRC / "ppg_hr.c", SRC / "frame.c", SRC / "collar_loop.c"],
        extra,
        "test_imu_fault",
        tmp_path,
    )


def test_ble_link_is_notify_only():
    text = (COLLAR / "include" / "ble_link.h").read_text(encoding="utf-8")
    assert "COLLAR_BLE_NOTIFY_UUID" in text
    assert "COLLAR_BLE_MTU" in text
    assert "COLLAR_GATT_WRITE_PROPS" in text
    assert "SHOCK" not in text


def test_firmware_has_no_actuator_drivers():
    banned = ("SHOCK", "STIM", "VIBE", "HAPTIC", "SOLENOID", "MOTOR", "STRIKE", "PUNISH")
    for path in (COLLAR / "src").rglob("*"):
        if path.suffix not in {".c", ".cpp", ".h"}:
            continue
        text = path.read_text(encoding="utf-8")
        for word in banned:
            assert word not in text, f"{path.name} mentions {word}"

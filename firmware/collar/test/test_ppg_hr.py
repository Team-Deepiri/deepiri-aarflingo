"""Host tests for collar DSP — written first (TDD)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

COLLAR = Path(__file__).resolve().parents[1]
SRC = COLLAR / "src"


def _compile(sources: list[Path], extra_c: str, bin_name: str, tmp_path: Path) -> Path:
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
    return out


def _compile_and_run(sources: list[Path], extra_c: str, bin_name: str, tmp_path: Path) -> str:
    out = _compile(sources, extra_c, bin_name, tmp_path)
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
    if (n > 244) return 6;
    if (!collar_frame_contains(buf, n, "still")) return 8;
    if (!collar_frame_contains(buf, n, "arousal")) return 9;
    if (!collar_frame_contains(buf, n, "gyro")) return 10;
    if (!collar_frame_contains(buf, n, "puck_c")) return 11;
    if (!collar_frame_contains(buf, n, "skin_c")) return 12;
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
    assert "#define PIN_SKIN_SENSE" in text


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
    int n = collar_loop_step(&L, ir, N, FS, 0.1f, 0.2f, 0.01f, 0, 3.8f, 1, 1, NULL, 0, NULL, 0, 0.f, 0.f, 0.f);
    if (n < 20) return 2;
    if (L.state != COLLAR_IDLE) return 3;
    if (!L.last.ppg_ok) return 4;
    if (L.last.hr_bpm < 110 || L.last.hr_bpm > 130) return 5;
    if (!collar_frame_contains(L.tx, n, "hr_bpm")) return 6;
    return 0;
}
"""
    _compile_and_run(
        [SRC / "ppg_hr.c", SRC / "frame.c", SRC / "collar_loop.c", SRC / "dog_state.c", SRC / "imu_feat.c", SRC / "audio_feat.c"],
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
    if (BMI270_REG_INT1_IO_CTRL != 0x53) return 10;
    if (BMI270_REG_INT_MAP_DATA != 0x58) return 11;
    if (BMI270_PWR_ACC_GYR_TEMP != 0x0E) return 12;
    float dps = bmi270_lsb_to_dps(32767);
    if (dps < 1999.0f || dps > 2001.0f) return 13;
    if (bmi270_temp_c(0) < 22.9f || bmi270_temp_c(0) > 23.1f) return 14;
    return 0;
}
"""
    _compile_and_run([SRC / "bmi270.c"], extra, "test_bmi", tmp_path)


def test_skin_ntc_midscale_is_25c(tmp_path):
    extra = r"""
#include "skin.h"
int main(void) {
    float t = skin_c_from_raw(2048, 4095);
    if (t < 24.0f || t > 26.0f) return 2;
    if (SKIN_ADC_GPIO == 0 || SKIN_ADC_GPIO == 3) return 3;
    return 0;
}
"""
    src = SRC / "skin.c"
    if not src.is_file():
        pytest.fail("skin.c missing — implement after this red test")
    _compile_and_run([src], extra, "test_skin", tmp_path)


def test_dog_state_still_shake_pant_and_arousal(tmp_path):
    extra = r"""
#include "dog_state.h"
#include "imu_feat.h"
int main(void) {
    float rest[6] = {0.f, 0.f, 1.f, 0.f, 0.f, 1.f};
    if (!dog_still(imu_dyn_g(rest, 2), imu_peak_g(rest, 2), 1)) return 2;
    float shake[3] = {3.2f, 0.1f, 0.2f};
    if (!dog_shake(imu_peak_g(shake, 1))) return 3;
    if (dog_pant(0.04f, 0, 0.35f)) return 4;
    if (!dog_pant(0.04f, 0, 0.55f)) return 5;
    if (dog_pant(0.04f, 1, 0.55f)) return 6;
    float a = dog_arousal(140, 15, 0, 1, 1, 0.3f);
    if (a < 0.4f || a > 1.0f) return 7;
    float calm = dog_arousal(55, 90, 1, 0, 0, 0.02f);
    if (calm > 0.35f) return 8;
    return 0;
}
"""
    src = SRC / "dog_state.c"
    if not src.is_file():
        pytest.fail("dog_state.c missing — implement after this red test")
    _compile_and_run([src, SRC / "imu_feat.c", SRC / "audio_feat.c"], extra, "test_dog", tmp_path)


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
    int n = collar_loop_step(&L, ir, 8, 50, 0.1f, 0.2f, 0.01f, 0, 3.00f, 1, 1, NULL, 0, NULL, 0, 0.f, 0.f, 0.f);
    if (n < 10) return 2;
    if (L.last.fault == NULL || strcmp(L.last.fault, "vbat") != 0) return 3;
    return 0;
}
"""
    _compile_and_run(
        [SRC / "ppg_hr.c", SRC / "frame.c", SRC / "collar_loop.c", SRC / "dog_state.c", SRC / "imu_feat.c", SRC / "audio_feat.c"],
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
    int n = collar_loop_step(&L, ir, 8, 50, 0.f, 0.f, 0.01f, 0, 3.80f, 0, 1, NULL, 0, NULL, 0, 0.f, 0.f, 0.f);
    if (n < 10) return 2;
    if (L.last.fault == NULL || strcmp(L.last.fault, "imu") != 0) return 3;
    return 0;
}
"""
    _compile_and_run(
        [SRC / "ppg_hr.c", SRC / "frame.c", SRC / "collar_loop.c", SRC / "dog_state.c", SRC / "imu_feat.c", SRC / "audio_feat.c"],
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


def test_wav_pcm16_riff_header(tmp_path):
    src = SRC / "wav.c"
    if not src.is_file():
        pytest.fail("wav.c missing — implement after this red test")
    extra = r"""
#include "wav.h"
#include <string.h>
int main(void) {
    int16_t pcm[4] = {1, -1, 2, -2};
    uint8_t buf[128];
    int n = collar_wav_pcm16(buf, sizeof buf, pcm, 4, 16000);
    if (n != 44 + 8) return 2;
    if (memcmp(buf, "RIFF", 4) != 0) return 3;
    if (memcmp(buf + 8, "WAVE", 4) != 0) return 4;
    if (memcmp(buf + 12, "fmt ", 4) != 0) return 5;
    return 0;
}
"""
    _compile_and_run([src], extra, "test_wav", tmp_path)


def test_infer_audio_body_matches_runtime_contract(tmp_path):
    src = SRC / "clip.c"
    if not src.is_file():
        pytest.fail("clip.c missing — implement after this red test")
    extra = r"""
#include "clip.h"
#include <string.h>
int main(void) {
    if (collar_clip_should_upload(0, 1)) return 2;
    if (collar_clip_should_upload(1, 0)) return 3;
    if (!collar_clip_should_upload(1, 1)) return 4;
    char buf[128];
    int n = collar_audio_body(buf, sizeof buf, 0.80f, 0.50f, 0.95f);
    if (n < 20) return 5;
    if (!strstr(buf, "\"audio_arousal\":")) return 6;
    if (!strstr(buf, "\"audio_valence\":")) return 7;
    if (!strstr(buf, "\"audio_bark_prob\":")) return 8;
    if (strstr(buf, "SHOCK")) return 9;
    return 0;
}
"""
    _compile_and_run([src], extra, "test_clip", tmp_path)


def test_afe4404_init_table_is_4ma_class(tmp_path):
    extra = r"""
#include "afe4404.h"
int main(void) {
    if (AFE4404_INIT_COUNT < 3) return 2;
    if (afe4404_init[0].reg != AFE4404_REG_CONTROL0) return 3;
    if (AFE4404_LED_STEP_UA != 800) return 4;
    if (afe4404_led_code_4ma() != 5) return 5;
    return 0;
}
"""
    _compile_and_run([SRC / "afe4404.c"], extra, "test_afe_init", tmp_path)


def test_cbor_roundtrip_hr_bpm(tmp_path):
    extra = r"""
#include "frame.h"
#include <stdio.h>
int main(void) {
    CollarSample s = {0};
    s.v = 1;
    s.ts_ms = 42;
    s.hr_bpm = 96;
    s.ppg_ok = 1;
    s.vbat_v = 3.8f;
    uint8_t buf[256];
    int n = collar_frame_encode(&s, buf, sizeof buf);
    if (n < 20) return 2;
    fwrite(buf, 1, (size_t)n, stdout);
    return 0;
}
"""
    dump = _compile([SRC / "frame.c"], extra, "dump_frame", tmp_path)
    dumped = subprocess.run([str(dump)], capture_output=True)
    assert dumped.returncode == 0
    payload = dumped.stdout
    assert b"hr_bpm" in payload
    assert b"source" in payload
    assert b"sensors" in payload
    assert len(payload) <= 244
    assert b"still" in payload
    assert b"arousal" in payload


def test_cbor_decode_roundtrip_hr_and_fault(tmp_path):
    extra = r"""
#include "frame.h"
#include <string.h>
int main(void) {
    CollarSample s = {0};
    s.v = 1;
    s.ts_ms = 42;
    s.hr_bpm = 96;
    s.rmssd_ms = 30;
    s.ppg_ok = 1;
    s.bark = 1;
    s.vbat_v = 3.80f;
    s.imu_rms = 0.12f;
    s.fault = "ppg";
    uint8_t buf[256];
    int n = collar_frame_encode(&s, buf, sizeof buf);
    CollarSample out = {0};
    char fault[16] = {0};
    if (collar_frame_decode(buf, n, &out, fault, sizeof fault) != 0) return 2;
    if (out.hr_bpm != 96) return 3;
    if (out.bark != 1) return 4;
    if (out.ts_ms != 42) return 5;
    if (strcmp(fault, "ppg") != 0) return 6;
    if (out.vbat_v < 3.79f || out.vbat_v > 3.81f) return 7;
    s.gyro_rms = 4.0f;
    s.puck_c = 23.0f;
    s.skin_c = 31.0f;
    s.pitch = 10.0f;
    n = collar_frame_encode(&s, buf, sizeof buf);
    if (collar_frame_decode(buf, n, &out, fault, sizeof fault) != 0) return 8;
    if (out.gyro_rms < 3.9f || out.gyro_rms > 4.1f) return 9;
    if (out.puck_c < 22.9f || out.puck_c > 23.1f) return 10;
    if (out.skin_c < 30.9f || out.skin_c > 31.1f) return 11;
    if (out.pitch < 9.9f || out.pitch > 10.1f) return 12;
    return 0;
}
"""
    _compile_and_run([SRC / "frame.c"], extra, "test_decode", tmp_path)


def test_python_decoder_matches_c_encoder(tmp_path):
    extra = r"""
#include "frame.h"
#include <stdio.h>
int main(void) {
    CollarSample s = {0};
    s.v = 1;
    s.ts_ms = 99;
    s.hr_bpm = 88;
    s.ppg_ok = 1;
    s.vbat_v = 3.7f;
    s.imu_rms = 0.2f;
    uint8_t buf[256];
    int n = collar_frame_encode(&s, buf, sizeof buf);
    if (n < 20) return 2;
    fwrite(buf, 1, (size_t)n, stdout);
    return 0;
}
"""
    dump = _compile([SRC / "frame.c"], extra, "dump_cbor", tmp_path)
    payload = subprocess.run([str(dump)], capture_output=True).stdout
    import sys

    sys.path.insert(0, str(COLLAR / "host"))
    from decode import decode_collar_cbor  # noqa: E402

    frame = decode_collar_cbor(payload)
    assert frame["hr_bpm"] == 88
    assert frame["ts_ms"] == 99
    assert frame["source"] == "sensors"
    assert frame["v"] == 1
    assert "gyro" in frame
    assert "puck_c" in frame
    assert "skin_c" in frame


def test_imu_isr_only_sets_flag(tmp_path):
    extra = r"""
#include "imu_isr.h"
int main(void) {
    volatile int flag = 0;
    collar_imu_isr(&flag);
    if (flag != 1) return 2;
    if (!collar_imu_take(&flag)) return 3;
    if (flag != 0) return 4;
    if (collar_imu_take(&flag)) return 5;
    return 0;
}
"""
    src = SRC / "imu_isr.c"
    if not src.is_file():
        pytest.fail("imu_isr.c missing — implement after this red test")
    _compile_and_run([src], extra, "test_isr", tmp_path)


def test_product_version_is_rev_a():
    text = (COLLAR / "include" / "product.h").read_text(encoding="utf-8")
    assert "0.2.0" in text
    assert "aarf-collar" in text
    flash = Path(__file__).resolve().parents[3] / "scripts" / "flash_collar.sh"
    assert flash.is_file()
    assert "platformio run -t upload" in flash.read_text(encoding="utf-8")


def test_android_enables_notify_cccd():
    repo = Path(__file__).resolve().parents[3]
    kt = (
        repo
        / "apps"
        / "aarf-pocket-android"
        / "app"
        / "src"
        / "main"
        / "java"
        / "dev"
        / "deepiri"
        / "aarflingo"
        / "data"
        / "CollarBleClient.kt"
    )
    text = kt.read_text(encoding="utf-8")
    assert "00002902-0000-1000-8000-00805f9b34fb" in text
    assert "ENABLE_NOTIFICATION_VALUE" in text


def test_pocket_gatt_matches_firmware_uuids():
    repo = Path(__file__).resolve().parents[3]
    header = (repo / "firmware" / "collar" / "include" / "ble_link.h").read_text(encoding="utf-8")
    assert "aarf-collar" in header
    assert "6e400001-b5a3-f393-e0a9-e50e24dcca9e" in header.lower()
    assert "6e400003-b5a3-f393-e0a9-e50e24dcca9e" in header.lower()
    ios = repo / "apps" / "aarf-pocket-ios" / "AarflingoPocket" / "Models" / "CollarCbor.swift"
    droid = (
        repo
        / "apps"
        / "aarf-pocket-android"
        / "app"
        / "src"
        / "main"
        / "java"
        / "dev"
        / "deepiri"
        / "aarflingo"
        / "data"
        / "CollarCbor.kt"
    )
    if not ios.is_file():
        pytest.fail("CollarCbor.swift missing — implement after this red test")
    if not droid.is_file():
        pytest.fail("CollarCbor.kt missing — implement after this red test")
    for path in (ios, droid):
        text = path.read_text(encoding="utf-8")
        assert "aarf-collar" in text
        assert "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" in text.upper()
        assert "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" in text.upper()
        assert "hr_bpm" in text
        assert "arousal" in text
        assert "still" in text
        assert "skin_c" in text
        assert "gyro" in text
        assert "puck_c" in text
        assert "SHOCK" not in text


def test_firmware_has_no_actuator_drivers():
    banned = ("SHOCK", "STIM", "VIBE", "HAPTIC", "SOLENOID", "MOTOR", "STRIKE", "PUNISH")
    for path in (COLLAR / "src").rglob("*"):
        if path.suffix not in {".c", ".cpp", ".h"}:
            continue
        text = path.read_text(encoding="utf-8")
        for word in banned:
            assert word not in text, f"{path.name} mentions {word}"

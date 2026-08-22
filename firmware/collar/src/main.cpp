#include "afe4404.h"
#include "audio_feat.h"
#include "ble_link.h"
#include "ble_radio.h"
#include "ble_tx.h"
#include "bmi270.h"
#include "clip.h"
#include "clip_wifi.h"
#include "collar_loop.h"
#include "imu_feat.h"
#include "imu_isr.h"
#include "led_stat.h"
#include "pins.h"
#include "product.h"
#include "skin.h"
#include "vbat.h"
#include "wdt.h"

#include <Arduino.h>
#include <math.h>
#include <Preferences.h>
#include <Wire.h>
#include <driver/i2s.h>
#include <esp_task_wdt.h>
#include <stdint.h>

static CollarLoop g_loop;
static int32_t g_ir[50];
static size_t g_nir;
static float g_xyz[100 * 3];
static size_t g_nimu;
static float g_gyro_ss;
static size_t g_ngyro;
static int32_t g_pcm[64];
static size_t g_npcm;
static int g_imu_ok;
static VbatCal g_vbat_cal;
static char g_runtime_url[96];
static volatile int g_imu_flag;

static void IRAM_ATTR on_imu_int(void) {
    collar_imu_isr(&g_imu_flag);
}

static int i2c_write8(uint8_t addr, uint8_t reg, uint8_t val) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    Wire.write(val);
    return Wire.endTransmission() == 0;
}

static int16_t i2c_read_le16(uint8_t addr, uint8_t reg) {
    Wire.beginTransmission(addr);
    Wire.write(reg);
    if (Wire.endTransmission(false) != 0) {
        return 0;
    }
    if (Wire.requestFrom((int)addr, 2) != 2) {
        return 0;
    }
    uint8_t lo = (uint8_t)Wire.read();
    uint8_t hi = (uint8_t)Wire.read();
    return (int16_t)((uint16_t)lo | ((uint16_t)hi << 8));
}

static int32_t afe4404_read_led1(void) {
    Wire.beginTransmission(AFE4404_I2C_ADDR);
    Wire.write(AFE4404_REG_LED1VAL);
    if (Wire.endTransmission(false) != 0) {
        return INT32_MIN;
    }
    if (Wire.requestFrom((int)AFE4404_I2C_ADDR, 3) != 3) {
        return INT32_MIN;
    }
    uint8_t b[3] = {0, 0, 0};
    b[0] = (uint8_t)Wire.read();
    b[1] = (uint8_t)Wire.read();
    b[2] = (uint8_t)Wire.read();
    return afe4404_sample_from_be24(b);
}

static void afe4404_write24(uint8_t reg, uint32_t val) {
    Wire.beginTransmission(AFE4404_I2C_ADDR);
    Wire.write(reg);
    Wire.write((uint8_t)(val >> 16));
    Wire.write((uint8_t)(val >> 8));
    Wire.write((uint8_t)val);
    Wire.endTransmission();
}

static void sample_imu_once(void) {
    if (!g_imu_ok || g_nimu >= 100) {
        return;
    }
    int16_t x = i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_ACC_X_LSB);
    int16_t y = i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_ACC_X_LSB + 2);
    int16_t z = i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_ACC_X_LSB + 4);
    g_xyz[3 * g_nimu] = bmi270_lsb_to_g(x);
    g_xyz[3 * g_nimu + 1] = bmi270_lsb_to_g(y);
    g_xyz[3 * g_nimu + 2] = bmi270_lsb_to_g(z);
    g_nimu++;
    float gx = bmi270_lsb_to_dps(i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_GYR_X_LSB));
    float gy = bmi270_lsb_to_dps(i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_GYR_X_LSB + 2));
    float gz = bmi270_lsb_to_dps(i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_GYR_X_LSB + 4));
    g_gyro_ss += gx * gx + gy * gy + gz * gz;
    g_ngyro++;
}

static void drive_led(uint32_t now) {
    static uint32_t last;
    uint32_t period = collar_led_period_ms(g_loop.last.fault);
    if (period == 0) {
        digitalWrite(PIN_LED_STAT, LOW);
        return;
    }
    if (now - last >= period) {
        last = now;
        digitalWrite(PIN_LED_STAT, !digitalRead(PIN_LED_STAT));
    }
}

void setup() {
    Serial.begin(115200);
    pinMode(PIN_LED_STAT, OUTPUT);
    pinMode(PIN_CHG_STAT, INPUT_PULLUP);
    pinMode(PIN_IMU_INT, INPUT);
    pinMode(PIN_PPG_RDY, INPUT);
    pinMode(PIN_PPG_RST, OUTPUT);
    digitalWrite(PIN_PPG_RST, LOW);
    delay(10);
    digitalWrite(PIN_PPG_RST, HIGH);
    delay(10);

    Wire.begin(PIN_SDA, PIN_SCL);
    for (uint8_t addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.print("i2c 0x");
            Serial.println(addr, HEX);
        }
    }
    for (size_t i = 0; i < AFE4404_INIT_COUNT; i++) {
        afe4404_write24(afe4404_init[i].reg, afe4404_init[i].val);
    }
    Wire.beginTransmission(BMI270_I2C_ADDR);
    Wire.write(BMI270_REG_CHIP_ID);
    uint8_t chip = 0;
    if (Wire.endTransmission(false) == 0 && Wire.requestFrom((int)BMI270_I2C_ADDR, 1) == 1) {
        chip = (uint8_t)Wire.read();
    }
    g_imu_ok = bmi270_chip_ok(chip);
    if (g_imu_ok) {
        i2c_write8(BMI270_I2C_ADDR, BMI270_REG_CMD, BMI270_CMD_SOFTRESET);
        delay(2);
        i2c_write8(BMI270_I2C_ADDR, BMI270_REG_PWR_CONF, BMI270_PWR_CONF_DISABLE_APS);
        i2c_write8(BMI270_I2C_ADDR, BMI270_REG_PWR_CTRL, BMI270_PWR_ACC_GYR_TEMP);
        i2c_write8(BMI270_I2C_ADDR, BMI270_REG_ACC_RANGE, BMI270_ACC_RANGE_8G);
        i2c_write8(BMI270_I2C_ADDR, BMI270_REG_INT1_IO_CTRL, BMI270_INT1_IO_OUT_AH);
        i2c_write8(BMI270_I2C_ADDR, BMI270_REG_INT_MAP_DATA, BMI270_INT_MAP_DRDY_INT1);
        attachInterrupt(digitalPinToInterrupt(PIN_IMU_INT), on_imu_int, RISING);
    }

    Preferences prefs;
    prefs.begin("collar", true);
    g_vbat_cal = vbat_cal_default();
    g_vbat_cal.scale = prefs.getFloat("vbat_s", VBAT_CAL_DEFAULT_SCALE);
    g_vbat_cal.offset = prefs.getFloat("vbat_o", VBAT_CAL_DEFAULT_OFFSET);
    char ssid[33] = {0};
    char pass[65] = {0};
    prefs.getString("wifi_ssid", ssid, sizeof ssid);
    prefs.getString("wifi_pass", pass, sizeof pass);
    prefs.getString("runtime", g_runtime_url, sizeof g_runtime_url);
    prefs.end();
    collar_wifi_begin(ssid, pass);

    collar_loop_init(&g_loop);
    analogReadResolution(12);

    i2s_config_t i2s_cfg = {};
    i2s_cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX);
    i2s_cfg.sample_rate = 16000;
    i2s_cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT;
    i2s_cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
    i2s_cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
    i2s_cfg.dma_buf_count = 4;
    i2s_cfg.dma_buf_len = 64;
    i2s_pin_config_t i2s_pins = {};
    i2s_pins.mck_io_num = I2S_PIN_NO_CHANGE;
    i2s_pins.bck_io_num = PIN_I2S_SCK;
    i2s_pins.ws_io_num = PIN_I2S_WS;
    i2s_pins.data_in_num = PIN_I2S_SD;
    i2s_pins.data_out_num = I2S_PIN_NO_CHANGE;
    i2s_driver_install(I2S_NUM_0, &i2s_cfg, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &i2s_pins);

    collar_ble_begin();
    esp_task_wdt_init(COLLAR_WDT_S, true);
    esp_task_wdt_add(NULL);

    Serial.print(COLLAR_PRODUCT_NAME);
    Serial.print(" rev-");
    Serial.print(COLLAR_PRODUCT_REV);
    Serial.print(" fw ");
    Serial.println(COLLAR_FW_VERSION);
}

void loop() {
    esp_task_wdt_reset();
    uint32_t now = millis();
    static uint32_t last_imu;
    if (collar_imu_take(&g_imu_flag) || (now - last_imu >= 10)) {
        last_imu = now;
        sample_imu_once();
    }

    int32_t hop[16];
    size_t got = 0;
    if (i2s_read(I2S_NUM_0, hop, sizeof hop, &got, 0) == ESP_OK && got > 0) {
        size_t ns = got / sizeof(int32_t);
        for (size_t i = 0; i < ns && g_npcm < (sizeof g_pcm / sizeof g_pcm[0]); i++) {
            g_pcm[g_npcm++] = hop[i] >> 8;
        }
    }

    int32_t s = afe4404_read_led1();
    if (s != INT32_MIN && g_nir < (sizeof g_ir / sizeof g_ir[0])) {
        g_ir[g_nir++] = s;
    }

    drive_led(now);

    static uint32_t last;
    if (now - last < 1000) {
        delay(10);
        return;
    }
    last = now;
    g_loop.last.ts_ms = now;

    float imu_rms = imu_rms_g(g_xyz, g_nimu);
    float imu_peak = imu_peak_g(g_xyz, g_nimu);
    float ar = audio_rms(g_pcm, g_npcm);
    int bark = audio_bark(ar, 500.0f);
    float vbat = vbat_from_raw(analogRead(PIN_VBAT_SENSE), 4095, 3.10f, g_vbat_cal.scale,
                                g_vbat_cal.offset);
    int mic_ok = g_npcm > 0;
    float gyro_rms = (g_ngyro > 0) ? sqrtf(g_gyro_ss / (float)g_ngyro) : 0.0f;
    float puck_c = g_imu_ok ? bmi270_temp_c(i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_TEMP_LSB))
                            : 0.0f;
    float skin_c = skin_c_from_raw(analogRead(PIN_SKIN_SENSE), 4095);

    int n = collar_loop_step(&g_loop, g_ir, g_nir, 50, imu_rms, imu_peak, ar, bark, vbat,
                             g_imu_ok, mic_ok, g_xyz, g_nimu, g_pcm, g_npcm, gyro_rms, puck_c,
                             skin_c);
    g_nir = 0;
    g_nimu = 0;
    g_npcm = 0;
    g_gyro_ss = 0.0f;
    g_ngyro = 0;
    if (n > 0) {
        uint8_t notify[256];
        int pn = collar_ble_pack(g_loop.tx, n, notify, sizeof notify, COLLAR_BLE_MTU);
        if (pn > 0) {
            collar_ble_notify(notify, pn);
        }
        if (collar_clip_should_upload(bark, collar_wifi_ok())) {
            char body[128];
            float bark_p = bark ? 0.95f : 0.0f;
            if (collar_audio_body(body, sizeof body, ar > 1.0f ? 1.0f : ar, 0.50f, bark_p) > 0) {
                esp_task_wdt_reset();
                collar_clip_post(g_runtime_url, body);
                esp_task_wdt_reset();
            }
        }
    }
}

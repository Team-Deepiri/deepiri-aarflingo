#include "afe4404.h"
#include "audio_feat.h"
#include "ble_link.h"
#include "bmi270.h"
#include "collar_loop.h"
#include "imu_feat.h"
#include "pins.h"
#include "vbat.h"

#include <Arduino.h>
#include <Wire.h>
#include <stdint.h>

static CollarLoop g_loop;
static int32_t g_ir[50];
static size_t g_nir;
static float g_xyz[100 * 3];
static size_t g_nimu;
static int32_t g_pcm[64];

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

static void sample_imu_once(void) {
    if (g_nimu >= 100) {
        return;
    }
    int16_t x = i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_ACC_X_LSB);
    int16_t y = i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_ACC_X_LSB + 2);
    int16_t z = i2c_read_le16(BMI270_I2C_ADDR, BMI270_REG_ACC_X_LSB + 4);
    g_xyz[3 * g_nimu] = bmi270_lsb_to_g(x);
    g_xyz[3 * g_nimu + 1] = bmi270_lsb_to_g(y);
    g_xyz[3 * g_nimu + 2] = bmi270_lsb_to_g(z);
    g_nimu++;
}

void setup() {
    Serial.begin(115200);
    pinMode(PIN_LED_STAT, OUTPUT);
    pinMode(PIN_CHG_STAT, INPUT_PULLUP);
    pinMode(PIN_IMU_INT, INPUT);
    pinMode(PIN_PPG_RDY, INPUT);
    pinMode(PIN_PPG_RST, OUTPUT);
    digitalWrite(PIN_PPG_RST, HIGH);
    Wire.begin(PIN_SDA, PIN_SCL);
    collar_loop_init(&g_loop);
    analogReadResolution(12);
    Serial.print("collar notify ");
    Serial.println(COLLAR_BLE_NOTIFY_UUID);
}

void loop() {
    sample_imu_once();

    int32_t s = afe4404_read_led1();
    if (s != INT32_MIN && g_nir < (sizeof g_ir / sizeof g_ir[0])) {
        g_ir[g_nir++] = s;
    }

    static uint32_t last = 0;
    uint32_t now = millis();
    if (now - last < 1000) {
        delay(10);
        return;
    }
    last = now;
    g_loop.last.ts_ms = now;

    float imu_rms = imu_rms_g(g_xyz, g_nimu);
    float imu_peak = imu_peak_g(g_xyz, g_nimu);
    float ar = audio_rms(g_pcm, sizeof g_pcm / sizeof g_pcm[0]);
    int bark = audio_bark(ar, 500.0f);
    float vbat = vbat_from_raw(analogRead(PIN_VBAT_SENSE), 4095, 3.10f, 1.0f, 0.0f);

    int n = collar_loop_step(&g_loop, g_ir, g_nir, 50, imu_rms, imu_peak, ar, bark, vbat);
    g_nir = 0;
    g_nimu = 0;
    if (n > 0) {
        Serial.write(g_loop.tx, (size_t)n);
        Serial.write('\n');
    }
    digitalWrite(PIN_LED_STAT, !digitalRead(PIN_LED_STAT));
}

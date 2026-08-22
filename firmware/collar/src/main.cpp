#include "afe4404.h"
#include "collar_loop.h"
#include "pins.h"

#include <Arduino.h>
#include <Wire.h>

static CollarLoop g_loop;
static int32_t g_ir[50];
static size_t g_nir;

static float imu_rms_stub(void) { return 0.05f; }
static float audio_rms_stub(void) { return 0.01f; }

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

void setup() {
    Serial.begin(115200);
    pinMode(PIN_LED_STAT, OUTPUT);
    pinMode(PIN_CHG_STAT, INPUT_PULLUP);
    pinMode(PIN_PPG_RDY, INPUT);
    pinMode(PIN_PPG_RST, OUTPUT);
    digitalWrite(PIN_PPG_RST, HIGH);
    Wire.begin(PIN_SDA, PIN_SCL);
    collar_loop_init(&g_loop);
    analogReadResolution(12);
}

void loop() {
    int32_t s = afe4404_read_led1();
    if (s != INT32_MIN && g_nir < (sizeof g_ir / sizeof g_ir[0])) {
        g_ir[g_nir++] = s;
    }

    static uint32_t last = 0;
    uint32_t now = millis();
    if (now - last < 1000) {
        delay(20);
        return;
    }
    last = now;
    g_loop.last.ts_ms = now;

    int raw = analogRead(PIN_VBAT_SENSE);
    float vadc = (raw / 4095.0f) * 3.10f;
    float vbat = 2.0f * vadc;

    int n = collar_loop_step(&g_loop, g_ir, g_nir, 50, imu_rms_stub(), 0.10f,
                             audio_rms_stub(), 0, vbat);
    g_nir = 0;
    if (n > 0) {
        Serial.write(g_loop.tx, (size_t)n);
        Serial.write('\n');
    }
    digitalWrite(PIN_LED_STAT, !digitalRead(PIN_LED_STAT));
}

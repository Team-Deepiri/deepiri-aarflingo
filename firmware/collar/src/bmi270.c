#include "bmi270.h"

float bmi270_lsb_to_g(int16_t lsb) {
    return ((float)lsb) * (8.0f / 32768.0f);
}

float bmi270_lsb_to_dps(int16_t lsb) {
    return ((float)lsb) * (2000.0f / 32768.0f);
}

float bmi270_temp_c(int16_t lsb) {
    return 23.0f + ((float)lsb) / 512.0f;
}

int bmi270_chip_ok(uint8_t chip_id) {
    return chip_id == BMI270_CHIP_ID;
}

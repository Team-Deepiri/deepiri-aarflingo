#include "bmi270.h"

float bmi270_lsb_to_g(int16_t lsb) {
    return ((float)lsb) * (8.0f / 32768.0f);
}

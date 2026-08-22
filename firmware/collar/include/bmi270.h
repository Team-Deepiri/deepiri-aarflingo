#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

#define BMI270_I2C_ADDR 0x68
#define BMI270_REG_CHIP_ID 0x00
#define BMI270_CHIP_ID 0x24
#define BMI270_REG_ACC_X_LSB 0x0C

/* ±8 g, 16-bit two's complement. */
float bmi270_lsb_to_g(int16_t lsb);

#ifdef __cplusplus
}
#endif

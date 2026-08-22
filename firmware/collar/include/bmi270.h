#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

#define BMI270_I2C_ADDR 0x68
#define BMI270_REG_CHIP_ID 0x00
#define BMI270_CHIP_ID 0x24
#define BMI270_REG_ACC_X_LSB 0x0C
#define BMI270_REG_ACC_RANGE 0x41
#define BMI270_ACC_RANGE_8G 0x02
#define BMI270_REG_PWR_CTRL 0x7D
#define BMI270_PWR_ACC_EN 0x04
#define BMI270_REG_CMD 0x7E
#define BMI270_CMD_SOFTRESET 0xB6
#define BMI270_REG_INT1_IO_CTRL 0x53
#define BMI270_INT1_IO_OUT_AH 0x0A
#define BMI270_REG_INT_MAP_DATA 0x58
#define BMI270_INT_MAP_DRDY_INT1 0x04

/* ±8 g, 16-bit two's complement. */
float bmi270_lsb_to_g(int16_t lsb);

int bmi270_chip_ok(uint8_t chip_id);

#ifdef __cplusplus
}
#endif

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* TI AFE4404 7-bit I2C address (ADDR_SEL = 0). */
#define AFE4404_I2C_ADDR 0x58

#define AFE4404_REG_CONTROL1 0x00
#define AFE4404_REG_LED2VAL 0x2A
#define AFE4404_REG_ALED2VAL 0x2B
#define AFE4404_REG_LED1VAL 0x2C
#define AFE4404_REG_ALED1VAL 0x2D

/* 24-bit two's complement IR sample from LED1VAL (red/IR slot). */
int32_t afe4404_sample_from_be24(const uint8_t b[3]);

#ifdef __cplusplus
}
#endif

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

/* TI AFE4404 7-bit I2C address (ADDR_SEL = 0). */
#define AFE4404_I2C_ADDR 0x58

#define AFE4404_REG_CONTROL0 0x00
#define AFE4404_REG_CONTROL1 0x01
#define AFE4404_REG_TIA_AMB_GAIN 0x21
#define AFE4404_REG_LEDCNTRL 0x22
#define AFE4404_REG_LED2VAL 0x2A
#define AFE4404_REG_ALED2VAL 0x2B
#define AFE4404_REG_LED1VAL 0x2C
#define AFE4404_REG_ALED1VAL 0x2D

#define AFE4404_LED_STEP_UA 800

typedef struct {
    uint8_t reg;
    uint32_t val;
} Afe4404Init;

extern const Afe4404Init afe4404_init[];
extern const size_t AFE4404_INIT_COUNT;

/* 24-bit two's complement IR sample from LED1VAL (red/IR slot). */
int32_t afe4404_sample_from_be24(const uint8_t b[3]);
int afe4404_led_code_4ma(void);

#ifdef __cplusplus
}
#endif

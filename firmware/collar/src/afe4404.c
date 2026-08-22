#include "afe4404.h"

int32_t afe4404_sample_from_be24(const uint8_t b[3]) {
    if (b == NULL) {
        return 0;
    }
    int32_t v = ((int32_t)b[0] << 16) | ((int32_t)b[1] << 8) | (int32_t)b[2];
    if (v & 0x800000) {
        v |= ~0xFFFFFF;
    }
    return v;
}

int afe4404_led_code_4ma(void) {
    return 4000 / AFE4404_LED_STEP_UA;
}

const Afe4404Init afe4404_init[] = {
    {AFE4404_REG_CONTROL0, 0x000000},
    {AFE4404_REG_TIA_AMB_GAIN, 0x000003},
    {AFE4404_REG_LEDCNTRL, (uint32_t)((5 << 6) | 5)},
};

const size_t AFE4404_INIT_COUNT = sizeof afe4404_init / sizeof afe4404_init[0];

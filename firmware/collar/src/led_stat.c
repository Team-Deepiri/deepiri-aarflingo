#include "led_stat.h"

#include <stddef.h>
#include <string.h>

uint32_t collar_led_period_ms(const char *fault) {
    if (fault == NULL || fault[0] == '\0') {
        return 10;
    }
    if (strcmp(fault, "vbat") == 0) {
        return 0;
    }
    return 500;
}

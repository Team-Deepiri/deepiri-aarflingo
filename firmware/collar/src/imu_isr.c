#include "imu_isr.h"

void collar_imu_isr(volatile int *flag) {
    if (flag != 0) {
        *flag = 1;
    }
}

int collar_imu_take(volatile int *flag) {
    if (flag == 0 || *flag == 0) {
        return 0;
    }
    *flag = 0;
    return 1;
}

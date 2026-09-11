#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* ISR body: set a flag only. Main loop calls take(). */
void collar_imu_isr(volatile int *flag);
int collar_imu_take(volatile int *flag);

#ifdef __cplusplus
}
#endif

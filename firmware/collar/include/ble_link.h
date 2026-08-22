#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Observational notify only. Never a write-char for actuation. */
#define COLLAR_BLE_SERVICE_UUID "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define COLLAR_BLE_NOTIFY_UUID "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
#define COLLAR_BLE_MTU 247

#ifdef __cplusplus
}
#endif

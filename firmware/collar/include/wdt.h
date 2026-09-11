#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* CLIP (Wi-Fi upload) is the slowest legal path. WDT must outlast it. */
#define COLLAR_CLIP_BUDGET_S 8
#define COLLAR_WDT_S 30

#ifdef __cplusplus
}
#endif

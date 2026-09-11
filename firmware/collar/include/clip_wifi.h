#pragma once

#ifdef __cplusplus
extern "C" {
#endif

void collar_wifi_begin(const char *ssid, const char *pass);
int collar_wifi_ok(void);
int collar_clip_post(const char *runtime_url, const char *json_body);

#ifdef __cplusplus
}
#endif

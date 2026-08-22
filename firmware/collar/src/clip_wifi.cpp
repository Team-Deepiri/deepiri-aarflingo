#include "clip_wifi.h"

#include <HTTPClient.h>
#include <WiFi.h>
#include <stdio.h>

void collar_wifi_begin(const char *ssid, const char *pass) {
    if (ssid == nullptr || ssid[0] == '\0') {
        return;
    }
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, pass ? pass : "");
}

int collar_wifi_ok(void) {
    return WiFi.status() == WL_CONNECTED;
}

int collar_clip_post(const char *runtime_url, const char *json_body) {
    if (runtime_url == nullptr || runtime_url[0] == '\0' || json_body == nullptr) {
        return -1;
    }
    if (!collar_wifi_ok()) {
        return -1;
    }
    char dest[192];
    int n = snprintf(dest, sizeof dest, "%s/infer/audio", runtime_url);
    if (n < 0 || (size_t)n >= sizeof dest) {
        return -1;
    }
    HTTPClient http;
    if (!http.begin(dest)) {
        return -1;
    }
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(json_body);
    http.end();
    return code;
}

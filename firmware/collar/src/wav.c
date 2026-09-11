#include "wav.h"

#include <string.h>

static void put_le16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void put_le32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

int collar_wav_pcm16(uint8_t *out, size_t cap, const int16_t *pcm, size_t n, int fs) {
    if (out == NULL || pcm == NULL || fs <= 0) {
        return -1;
    }
    uint32_t data_bytes = (uint32_t)(n * 2);
    uint32_t total = 44 + data_bytes;
    if (cap < total) {
        return -1;
    }
    memcpy(out, "RIFF", 4);
    put_le32(out + 4, total - 8);
    memcpy(out + 8, "WAVE", 4);
    memcpy(out + 12, "fmt ", 4);
    put_le32(out + 16, 16);
    put_le16(out + 20, 1);
    put_le16(out + 22, 1);
    put_le32(out + 24, (uint32_t)fs);
    put_le32(out + 28, (uint32_t)fs * 2);
    put_le16(out + 32, 2);
    put_le16(out + 34, 16);
    memcpy(out + 36, "data", 4);
    put_le32(out + 40, data_bytes);
    memcpy(out + 44, pcm, data_bytes);
    return (int)total;
}

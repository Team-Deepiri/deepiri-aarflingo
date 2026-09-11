#include "ble_radio.h"

#include "ble_link.h"

#include <NimBLEDevice.h>

class CollarServerCbs : public NimBLEServerCallbacks {
    void onDisconnect(NimBLEServer *server) {
        (void)server;
        NimBLEDevice::startAdvertising();
    }
};

static NimBLECharacteristic *g_tx;
static CollarServerCbs g_cbs;

void collar_ble_begin(void) {
    NimBLEDevice::init(COLLAR_BLE_ADV_NAME);
    NimBLEDevice::setMTU(COLLAR_BLE_MTU);
    NimBLEServer *server = NimBLEDevice::createServer();
    server->setCallbacks(&g_cbs);
    NimBLEService *svc = server->createService(COLLAR_BLE_SERVICE_UUID);
    g_tx = svc->createCharacteristic(COLLAR_BLE_NOTIFY_UUID, NIMBLE_PROPERTY::NOTIFY);
    svc->start();
    NimBLEAdvertising *adv = NimBLEDevice::getAdvertising();
    adv->addServiceUUID(COLLAR_BLE_SERVICE_UUID);
    adv->setScanResponse(true);
    adv->start();
}

void collar_ble_notify(const uint8_t *p, int n) {
    if (g_tx == nullptr || p == nullptr || n <= 0) {
        return;
    }
    g_tx->setValue(p, (size_t)n);
    g_tx->notify();
}

int collar_ble_subscribed(void) {
    if (g_tx == nullptr) {
        return 0;
    }
    return (int)g_tx->getSubscribedCount();
}

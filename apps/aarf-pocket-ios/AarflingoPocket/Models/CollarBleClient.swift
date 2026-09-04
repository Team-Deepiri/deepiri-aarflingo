import Combine
import CoreBluetooth
import Foundation

/// Observational subscriber for aarf-collar. No writable GATT chars.
@MainActor
final class CollarBleClient: NSObject, ObservableObject {
    @Published var vitals: CollarVitals?
    @Published var connected = false
    @Published var scanning = false
    @Published var lastError: String?

    private var central: CBCentralManager?
    private var peripheral: CBPeripheral?
    private var wantScan = false

    func start() {
        lastError = nil
        wantScan = true
        if central == nil {
            central = CBCentralManager(delegate: self, queue: .main)
        } else {
            beginScan()
        }
    }

    func stop() {
        wantScan = false
        scanning = false
        if let p = peripheral {
            central?.cancelPeripheralConnection(p)
        }
        central?.stopScan()
        connected = false
    }

    private func beginScan() {
        guard let central, central.state == .poweredOn else { return }
        scanning = true
        central.scanForPeripherals(withServices: nil, options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
    }
}

extension CollarBleClient: CBCentralManagerDelegate, CBPeripheralDelegate {
    nonisolated func centralManagerDidUpdateState(_ central: CBCentralManager) {
        Task { @MainActor in
            if central.state == .poweredOn, self.wantScan {
                self.beginScan()
            } else if central.state != .poweredOn {
                self.lastError = "bluetooth off"
            }
        }
    }

    nonisolated func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        let name = peripheral.name ?? (advertisementData[CBAdvertisementDataLocalNameKey] as? String)
        guard name == CollarGatt.advName else { return }
        Task { @MainActor in
            self.central?.stopScan()
            self.scanning = false
            self.peripheral = peripheral
            peripheral.delegate = self
            self.central?.connect(peripheral)
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        peripheral.discoverServices([CBUUID(string: CollarGatt.serviceUUID)])
        Task { @MainActor in self.connected = true }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        Task { @MainActor in
            self.connected = false
            if self.wantScan { self.beginScan() }
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        peripheral.services?.forEach { peripheral.discoverCharacteristics([CBUUID(string: CollarGatt.notifyUUID)], for: $0) }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        service.characteristics?.forEach { ch in
            if ch.uuid == CBUUID(string: CollarGatt.notifyUUID) {
                peripheral.setNotifyValue(true, for: ch)
            }
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard let data = characteristic.value, let vitals = CollarCbor.decode(data) else { return }
        Task { @MainActor in self.vitals = vitals }
    }
}

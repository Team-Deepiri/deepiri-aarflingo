package dev.deepiri.aarflingo.data

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.Looper
import java.util.UUID

/** Observational subscriber. Does not write any GATT characteristic. */
class CollarBleClient(
    private val context: Context,
    private val onVitals: (CollarVitals) -> Unit,
    private val onStatus: (Boolean, String?) -> Unit,
) {
    private val adapter: BluetoothAdapter? =
        (context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager)?.adapter
    private var gatt: BluetoothGatt? = null
    private val main = Handler(Looper.getMainLooper())

    @SuppressLint("MissingPermission")
    fun start() {
        val scanner = adapter?.bluetoothLeScanner
        if (scanner == null) {
            onStatus(false, "bluetooth off")
            return
        }
        onStatus(false, "scanning")
        scanner.startScan(scanCb)
        main.postDelayed({ scanner.stopScan(scanCb) }, 12_000)
    }

    @SuppressLint("MissingPermission")
    fun stop() {
        adapter?.bluetoothLeScanner?.stopScan(scanCb)
        gatt?.close()
        gatt = null
        onStatus(false, null)
    }

    private val scanCb = object : ScanCallback() {
        @SuppressLint("MissingPermission")
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            val name = result.device.name ?: return
            if (name != CollarGatt.ADV_NAME) return
            adapter?.bluetoothLeScanner?.stopScan(this)
            gatt = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                result.device.connectGatt(context, false, gattCb, BluetoothDevice.TRANSPORT_LE)
            } else {
                result.device.connectGatt(context, false, gattCb)
            }
        }
    }

    private val gattCb = object : BluetoothGattCallback() {
        @SuppressLint("MissingPermission")
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                g.discoverServices()
                main.post { onStatus(true, null) }
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                main.post { onStatus(false, null) }
            }
        }

        @SuppressLint("MissingPermission")
        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            val svc = g.getService(UUID.fromString(CollarGatt.SERVICE_UUID)) ?: return
            val ch = svc.getCharacteristic(UUID.fromString(CollarGatt.NOTIFY_UUID)) ?: return
            g.setCharacteristicNotification(ch, true)
        }

        @Deprecated("Deprecated in Java")
        override fun onCharacteristicChanged(g: BluetoothGatt, ch: BluetoothGattCharacteristic) {
            val v = CollarCbor.decode(ch.value) ?: return
            main.post { onVitals(v) }
        }
    }
}

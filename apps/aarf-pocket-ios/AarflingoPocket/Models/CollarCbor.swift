import Foundation

enum CollarGatt {
    static let advName = "aarf-collar"
    static let serviceUUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    static let notifyUUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
}

struct CollarVitals: Equatable {
    var v: Int
    var tsMs: UInt32
    var hrBpm: Int
    var rmssdMs: Int
    var vbatV: Double
    var imuRms: Double
    var bark: Bool
    var ppgOk: Bool
    var still: Bool
    var pant: Bool
    var rrBpm: Int
    var arousal: Double
    var gyroRms: Double
    var puckC: Double
    var skinC: Double
    var fault: String?
    var source: String
}

enum CollarCbor {
    static func decode(_ data: Data) -> CollarVitals? {
        let buf = [UInt8](data)
        guard !buf.isEmpty, buf[0] & 0xE0 == 0xA0 else { return nil }
        let pairs = Int(buf[0] & 0x1F)
        var i = 1
        var map: [String: Any] = [:]
        for _ in 0..<pairs {
            guard let key = text(buf, &i), let val = value(buf, &i) else { return nil }
            map[key] = val
        }
        return CollarVitals(
            v: map["v"] as? Int ?? 0,
            tsMs: UInt32(truncatingIfNeeded: (map["ts_ms"] as? Int) ?? 0),
            hrBpm: map["hr_bpm"] as? Int ?? 0,
            rmssdMs: map["rmssd_ms"] as? Int ?? 0,
            vbatV: map["vbat_v"] as? Double ?? 0,
            imuRms: map["imu_rms"] as? Double ?? 0,
            bark: map["bark"] as? Bool ?? false,
            ppgOk: map["ppg_ok"] as? Bool ?? false,
            still: map["still"] as? Bool ?? false,
            pant: map["pant"] as? Bool ?? false,
            rrBpm: map["rr_bpm"] as? Int ?? 0,
            arousal: map["arousal"] as? Double ?? 0,
            gyroRms: map["gyro"] as? Double ?? 0,
            puckC: map["puck_c"] as? Double ?? 0,
            skinC: map["skin_c"] as? Double ?? 0,
            fault: map["fault"] as? String,
            source: map["source"] as? String ?? "sensors"
        )
    }

    private static func u8(_ buf: [UInt8], _ i: inout Int) -> UInt8? {
        guard i < buf.count else { return nil }
        let v = buf[i]
        i += 1
        return v
    }

    private static func uint(_ buf: [UInt8], _ i: inout Int) -> Int? {
        guard let t = u8(buf, &i), t >> 5 == 0 else { return nil }
        let ai = Int(t & 0x1F)
        if ai < 24 { return ai }
        if ai == 24 { return u8(buf, &i).map(Int.init) }
        if ai == 25, let hi = u8(buf, &i), let lo = u8(buf, &i) {
            return (Int(hi) << 8) | Int(lo)
        }
        return nil
    }

    private static func text(_ buf: [UInt8], _ i: inout Int) -> String? {
        guard let t = u8(buf, &i), t >> 5 == 3 else { return nil }
        let n = Int(t & 0x1F)
        guard n < 24, i + n <= buf.count else { return nil }
        let s = String(bytes: buf[i..<(i + n)], encoding: .utf8)
        i += n
        return s
    }

    private static func f32(_ buf: [UInt8], _ i: inout Int) -> Double? {
        guard let t = u8(buf, &i), t == 0xFA, i + 4 <= buf.count else { return nil }
        var u: UInt32 = 0
        u |= UInt32(buf[i]) << 24
        u |= UInt32(buf[i + 1]) << 16
        u |= UInt32(buf[i + 2]) << 8
        u |= UInt32(buf[i + 3])
        i += 4
        return Double(Float(bitPattern: u))
    }

    private static func value(_ buf: [UInt8], _ i: inout Int) -> Any? {
        guard i < buf.count else { return nil }
        let t = buf[i]
        if t == 0xF4 { i += 1; return false }
        if t == 0xF5 { i += 1; return true }
        if t == 0xF6 { i += 1; return nil }
        if t == 0xFA { return f32(buf, &i) }
        if t >> 5 == 0 { return uint(buf, &i) }
        if t >> 5 == 3 { return text(buf, &i) }
        return nil
    }
}

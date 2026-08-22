package dev.deepiri.aarflingo.data

object CollarGatt {
    const val ADV_NAME = "aarf-collar"
    const val SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
    const val NOTIFY_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
}

data class CollarVitals(
    val v: Int,
    val tsMs: Long,
    val hrBpm: Int,
    val rmssdMs: Int,
    val vbatV: Float,
    val imuRms: Float,
    val bark: Boolean,
    val ppgOk: Boolean,
    val still: Boolean,
    val pant: Boolean,
    val rrBpm: Int,
    val arousal: Float,
    val fault: String?,
    val source: String,
)

object CollarCbor {
    fun decode(buf: ByteArray): CollarVitals? {
        if (buf.isEmpty() || (buf[0].toInt() and 0xE0) != 0xA0) return null
        val pairs = buf[0].toInt() and 0x1F
        var i = 1
        val map = HashMap<String, Any?>()
        repeat(pairs) {
            val key = text(buf, i) ?: return null
            i = key.second
            val value = value(buf, i) ?: return null
            i = value.second
            map[key.first] = value.first
        }
        return CollarVitals(
            v = (map["v"] as? Int) ?: 0,
            tsMs = ((map["ts_ms"] as? Int) ?: 0).toLong(),
            hrBpm = (map["hr_bpm"] as? Int) ?: 0,
            rmssdMs = (map["rmssd_ms"] as? Int) ?: 0,
            vbatV = (map["vbat_v"] as? Float) ?: 0f,
            imuRms = (map["imu_rms"] as? Float) ?: 0f,
            bark = (map["bark"] as? Boolean) ?: false,
            ppgOk = (map["ppg_ok"] as? Boolean) ?: false,
            still = (map["still"] as? Boolean) ?: false,
            pant = (map["pant"] as? Boolean) ?: false,
            rrBpm = (map["rr_bpm"] as? Int) ?: 0,
            arousal = (map["arousal"] as? Float) ?: 0f,
            fault = map["fault"] as? String,
            source = (map["source"] as? String) ?: "sensors",
        )
    }

    private fun u8(buf: ByteArray, i: Int): Pair<Int, Int>? {
        if (i >= buf.size) return null
        return (buf[i].toInt() and 0xFF) to (i + 1)
    }

    private fun uint(buf: ByteArray, i0: Int): Pair<Int, Int>? {
        val t = u8(buf, i0) ?: return null
        if (t.first shr 5 != 0) return null
        val ai = t.first and 0x1F
        var i = t.second
        if (ai < 24) return ai to i
        if (ai == 24) {
            val v = u8(buf, i) ?: return null
            return v.first to v.second
        }
        if (ai == 25) {
            val hi = u8(buf, i) ?: return null
            val lo = u8(buf, hi.second) ?: return null
            return ((hi.first shl 8) or lo.first) to lo.second
        }
        return null
    }

    private fun text(buf: ByteArray, i0: Int): Pair<String, Int>? {
        val t = u8(buf, i0) ?: return null
        if (t.first shr 5 != 3) return null
        val n = t.first and 0x1F
        val i = t.second
        if (n >= 24 || i + n > buf.size) return null
        return String(buf, i, n, Charsets.UTF_8) to (i + n)
    }

    private fun f32(buf: ByteArray, i0: Int): Pair<Float, Int>? {
        val t = u8(buf, i0) ?: return null
        if (t.first != 0xFA || t.second + 4 > buf.size) return null
        val i = t.second
        val bits = (buf[i].toInt() and 0xFF shl 24) or
            (buf[i + 1].toInt() and 0xFF shl 16) or
            (buf[i + 2].toInt() and 0xFF shl 8) or
            (buf[i + 3].toInt() and 0xFF)
        return Float.fromBits(bits) to (i + 4)
    }

    private fun value(buf: ByteArray, i0: Int): Pair<Any?, Int>? {
        if (i0 >= buf.size) return null
        val t = buf[i0].toInt() and 0xFF
        if (t == 0xF4) return false to (i0 + 1)
        if (t == 0xF5) return true to (i0 + 1)
        if (t == 0xF6) return null to (i0 + 1)
        if (t == 0xFA) return f32(buf, i0)
        if (t shr 5 == 0) return uint(buf, i0)
        if (t shr 5 == 3) return text(buf, i0)
        return null
    }
}

package dev.deepiri.aarflingo.data

import android.content.Context
import android.graphics.Bitmap
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import java.util.Date
import java.util.UUID
import kotlin.random.Random

data class TriadPrediction(
    val intent: String,
    val emotion: String,
    val behavior: String,
    val confidence: Float,
    val gate: String,
    val dogPresent: Boolean = true,
) {
    val intentLabel: String
        get() = when (intent) {
            "play" -> "Wants to play"
            "food" -> "Wants food"
            "outside" -> "Wants outside"
            "rest" -> "Resting"
            "avoid" -> "Needs space"
            "attention" -> "Seeks attention"
            else -> intent.replaceFirstChar { it.uppercase() }
        }

    val intentEmoji: String
        get() = when (intent) {
            "play" -> "\uD83C\uDFBE"
            "food" -> "\uD83C\uDF56"
            "outside" -> "\uD83D\uDEAA"
            "rest" -> "\uD83D\uDE34"
            "avoid" -> "\u26A0\uFE0F"
            "attention" -> "\uD83D\uDC3E"
            else -> "\uD83D\uDC15"
        }

    val gateColor: Long
        get() = when (gate) {
            "pass" -> 0xFF3DD68C
            "reject" -> 0xFFF07178
            else -> 0xFFF0C674
        }

    companion object {
        val Demo = TriadPrediction("play", "excited", "play_bow", 0.91f, "pass")

        fun randomDemo(): TriadPrediction {
            val options = listOf(
                TriadPrediction("play", "excited", "play_bow", 0.92f, "pass"),
                TriadPrediction("food", "content", "sniff_ground", 0.84f, "pass"),
                TriadPrediction("outside", "anxious", "freeze", 0.78f, "review"),
                TriadPrediction("rest", "calm", "yawning", 0.71f, "review"),
                TriadPrediction("avoid", "fearful", "cowering", 0.64f, "review"),
                TriadPrediction("attention", "happy", "paw_raise", 0.87f, "pass"),
            )
            return options[Random.nextInt(options.size)]
        }
    }
}

data class HistoryItem(
    val id: String = UUID.randomUUID().toString(),
    val intent: String,
    val emotion: String,
    val behavior: String,
    val confidence: Float,
    val timestamp: Date = Date(),
) {
    val intentEmoji: String
        get() = when (intent) {
            "play" -> "\uD83C\uDFBE"
            "food" -> "\uD83C\uDF56"
            "outside" -> "\uD83D\uDEAA"
            "rest" -> "\uD83D\uDE34"
            "avoid" -> "\u26A0\uFE0F"
            "attention" -> "\uD83D\uDC3E"
            else -> "\uD83D\uDC15"
        }
}

class AppViewModel : ViewModel() {
    var runtimeUrl by mutableStateOf("http://10.0.2.2:8765")
    var connected by mutableStateOf(false)
    var liveOn by mutableStateOf(false)
    var prediction by mutableStateOf(TriadPrediction.Demo)
    var onDevice by mutableStateOf(false)
    var onDeviceAvailable by mutableStateOf(false)
    var autoConnect by mutableStateOf(false)
    var selectedIntentFilter by mutableStateOf<String?>(null)
    var showOnboarding by mutableStateOf(false)
    var lastError by mutableStateOf<String?>(null)
    var collarListen by mutableStateOf(false)
    var collarConnected by mutableStateOf(false)
    var collarVitals by mutableStateOf<CollarVitals?>(null)
    var collarStatus by mutableStateOf<String?>(null)
    private var collarBle: CollarBleClient? = null

    var history by mutableStateOf(
        listOf(
            HistoryItem(intent = "play", emotion = "excited", behavior = "play_bow", confidence = 0.89f),
            HistoryItem(intent = "food", emotion = "content", behavior = "sniff_ground", confidence = 0.76f),
            HistoryItem(intent = "rest", emotion = "calm", behavior = "yawning", confidence = 0.93f),
            HistoryItem(intent = "outside", emotion = "anxious", behavior = "freeze", confidence = 0.68f),
            HistoryItem(intent = "play", emotion = "excited", behavior = "play_bow", confidence = 0.95f),
            HistoryItem(intent = "attention", emotion = "happy", behavior = "paw_raise", confidence = 0.82f),
        ),
    )

    // ── Runtime client ─────────────────────────────────────────────────
    private var _client: RuntimeClient = RuntimeClient(runtimeUrl)
    val runtimeClient: RuntimeClient get() = _client

    // ── On-device engine ───────────────────────────────────────────────
    private var _onDevice: OnDeviceEngine? = null
    private var _lastGray: FloatArray? = null

    /** Injects engine init + extracts brightness/contrast/motion + runs locally. */
    fun initOnDevice(context: Context) {
        if (_onDevice == null) {
            val engine = OnDeviceEngine(context.applicationContext)
            engine.init()
            _onDevice = engine
            onDeviceAvailable = engine.available
        }
    }

    fun toggleOnDevice() {
        onDevice = !onDevice && onDeviceAvailable
    }

    /** Rebuild the client when the URL changes in Settings. */
    fun updateRuntimeUrl(url: String) {
        runtimeUrl = url
        _client.disconnect()
        _client = RuntimeClient(url)
        if (liveOn) connectWs()
    }

    /** Connect WebSocket and wire callbacks. */
    fun connectWs() {
        _client.onConnected = { ok -> connected = ok }
        _client.onError = { msg -> lastError = msg }
        _client.onPrediction = { pred ->
            prediction = pred
            connected = true
            appendHistory(pred)
        }
        _client.connect(runtimeUrl)
    }

    fun disconnectWs() {
        _client.disconnect()
        connected = false
    }

    /** Upload a JPEG frame and update state from the response. */
    suspend fun inferFrame(jpeg: ByteArray) {
        if (onDevice) {
            val bitmap = decodeBitmap(jpeg) ?: return
            val frame = extractFrameFeatures(bitmap)
            bitmap.recycle()
            val pred = _onDevice?.pushAndPredict(frame) ?: return
            prediction = pred
            appendHistory(pred)
            return
        }
        val pred = _client.inferFrame(jpeg) ?: return
        prediction = pred
        connected = true
        appendHistory(pred)
    }

    private fun decodeBitmap(jpeg: ByteArray): Bitmap? = runCatching {
        android.graphics.BitmapFactory.decodeByteArray(jpeg, 0, jpeg.size)
    }.getOrNull()?.let { descale(it) }

    private fun descale(bmp: Bitmap): Bitmap {
        val scale = 240f / maxOf(bmp.width, bmp.height)
        if (scale >= 1f) return bmp
        val w = maxOf(1, (bmp.width * scale).toInt())
        val h = maxOf(1, (bmp.height * scale).toInt())
        val scaled = Bitmap.createScaledBitmap(bmp, w, h, true)
        if (scaled !== bmp) bmp.recycle()
        return scaled
    }

    /** Cheap grayscale stats (brightness/contrast) + normalized frame diff (motion). */
    private fun extractFrameFeatures(bmp: Bitmap): OnDeviceFrame {
        val w = bmp.width
        val h = bmp.height
        val pixels = IntArray(w * h)
        bmp.getPixels(pixels, 0, w, 0, 0, w, h)
        val gray = FloatArray(pixels.size)
        var sum = 0L
        for (i in pixels.indices) {
            val p = pixels[i]
            val g = ((p shr 16 and 0xFF) + (p shr 8 and 0xFF) + (p and 0xFF)) / 3f / 255f
            gray[i] = g
            sum += (g * 255).toLong()
        }
        val mean = sum.toFloat() / pixels.size / 255f
        var variance = 0.0
        var diff = 0.0f
        val prev = _lastGray
        for (i in gray.indices) {
            val d = gray[i] - mean
            variance += d * d
            if (prev != null) diff += kotlin.math.abs(prev[i] - gray[i])
        }
        _lastGray = gray
        val contrast = kotlin.math.sqrt(variance / pixels.size).toFloat()
        val motion = if (prev != null) diff / pixels.size else 0f
        val dogPresent = if (motion > 0.04f) 1f else 0f
        return OnDeviceFrame(
            brightness = mean,
            contrast = (contrast * 3f).coerceIn(0f, 1f),
            motion = motion,
            width = w,
            height = h,
            dogPresent = dogPresent,
        )
    }

    suspend fun checkHealth(): Boolean {
        val ok = _client.checkHealth()
        connected = ok
        return ok
    }

    private fun appendHistory(pred: TriadPrediction) {
        history = listOf(
            HistoryItem(
                intent = pred.intent,
                emotion = pred.emotion,
                behavior = pred.behavior,
                confidence = pred.confidence,
            )
        ) + history.take(49)
    }

    // ── Mock (kept for offline / demo use) ──────────────────────────────
    fun refreshMock() {
        connected = true
        prediction = TriadPrediction.randomDemo()
        appendHistory(prediction)
    }

    val uniqueIntents: List<String>
        get() = history.map { it.intent }.distinct().sorted()

    val filteredHistory: List<HistoryItem>
        get() = selectedIntentFilter?.let { f -> history.filter { it.intent == f } } ?: history

    val intentCounts: Map<String, Int>
        get() = history.groupBy { it.intent }.mapValues { it.value.size }

    val averageConfidence: Float
        get() = if (history.isEmpty()) 0f else history.map { it.confidence }.average().toFloat()

    fun clearHistory() {
        history = emptyList()
    }

    fun setCollarListen(context: Context, on: Boolean) {
        collarListen = on
        if (!on) {
            collarBle?.stop()
            collarBle = null
            collarConnected = false
            collarStatus = null
            return
        }
        val client = CollarBleClient(
            context.applicationContext,
            onVitals = { collarVitals = it },
            onStatus = { ok, msg ->
                collarConnected = ok
                collarStatus = msg
            },
        )
        collarBle = client
        client.start()
    }

    override fun onCleared() {
        super.onCleared()
        _client.disconnect()
        collarBle?.stop()
        _onDevice?.close()
    }
}

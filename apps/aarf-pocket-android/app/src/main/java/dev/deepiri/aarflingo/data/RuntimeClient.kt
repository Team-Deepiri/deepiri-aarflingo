package dev.deepiri.aarflingo.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Communicates with the Aarflingo FastAPI runtime.
 *
 *  POST /infer/frame  — multipart JPEG upload → TriadPrediction JSON
 *  WS   /ws/live      — streaming predictions
 *  GET  /health       — connectivity check
 */
class RuntimeClient(private var baseUrl: String) {

    private val http = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(5, TimeUnit.SECONDS)
        .build()

    private var ws: WebSocket? = null
    var onPrediction: ((TriadPrediction) -> Unit)? = null
    var onConnected: ((Boolean) -> Unit)? = null
    var onError: ((String) -> Unit)? = null

    // ── WebSocket ──────────────────────────────────────────────────────────

    fun connect(url: String = baseUrl) {
        baseUrl = url
        ws?.cancel()
        val wsUrl = url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/live"
        val request = Request.Builder().url(wsUrl).build()
        ws = http.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                onConnected?.invoke(true)
            }
            override fun onMessage(webSocket: WebSocket, text: String) {
                parsePrediction(text)?.let { onPrediction?.invoke(it) }
            }
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                onConnected?.invoke(false)
                onError?.invoke(t.message ?: "WebSocket error")
            }
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                onConnected?.invoke(false)
            }
        })
    }

    fun disconnect() {
        ws?.close(1000, "user stop")
        ws = null
    }

    // ── Frame upload ───────────────────────────────────────────────────────

    /** Upload a JPEG byte array; returns a TriadPrediction or null on error. */
    suspend fun inferFrame(jpeg: ByteArray): TriadPrediction? = withContext(Dispatchers.IO) {
        try {
            val body = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart(
                    "file", "frame.jpg",
                    jpeg.toRequestBody("image/jpeg".toMediaType())
                )
                .build()
            val req = Request.Builder()
                .url("$baseUrl/infer/frame")
                .post(body)
                .build()
            val response = http.newCall(req).execute()
            val text = response.body?.string() ?: return@withContext null
            if (!response.isSuccessful) return@withContext null
            parsePrediction(text)
        } catch (_: Exception) {
            null
        }
    }

    // ── Health ─────────────────────────────────────────────────────────────

    suspend fun checkHealth(): Boolean = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$baseUrl/health").build()
            val resp = http.newCall(req).execute()
            val text = resp.body?.string() ?: return@withContext false
            JSONObject(text).optBoolean("ok", false)
        } catch (_: Exception) {
            false
        }
    }

    // ── Parse ──────────────────────────────────────────────────────────────

    private fun parsePrediction(json: String): TriadPrediction? = runCatching {
        val j = JSONObject(json)
        val type = j.optString("type")
        // Accept prediction frames and bare JSON objects
        if (type == "error") return null
        TriadPrediction(
            intent = j.optString("intent", "unknown"),
            emotion = j.optString("emotion", "unknown"),
            behavior = j.optString("behavior", "unknown"),
            confidence = j.optDouble("confidence", 0.0).toFloat(),
            gate = j.optString("gate", "review"),
            dogPresent = j.optBoolean("dog_present", false),
        )
    }.getOrNull()
}

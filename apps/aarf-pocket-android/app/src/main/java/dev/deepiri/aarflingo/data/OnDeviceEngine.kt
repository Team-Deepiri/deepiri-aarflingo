package dev.deepiri.aarflingo.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.nio.FloatBuffer

/**
 * On-device TriadNet inference — cuts WiFi dependence.
 *
 * Loads `models/triad.onnx` from app assets and runs the same TriadNet the
 * runtime uses, on a rolling 15-frame × 73-dim feature window. The phone
 * estimates what it can from camera frames (brightness, contrast, motion,
 * aspect ratio, dog-presence heuristic); the rest of each feature row stays
 * zero like the runtime's cold-start padding (`flatten_sequence_rows`).
 *
 * When no model is bundled (debug builds / first run), the engine reports
 * `available = false` and the app keeps using the runtime over WiFi.
 */
class OnDeviceEngine(private val context: Context) {

    companion object {
        const val FEATURE_DIM = 73
        const val SEQUENCE_LEN = 15
        private const val MODEL_ASSET = "models/triad.onnx"
        private const val MANIFEST_ASSET = "models/triad_manifest.json"

        // Fallbacks if the manifest isn't bundled (shouldn't happen once
        // scripts/mobile/bundle-mobile-models.sh has run).
        val DEFAULT_INTENTS = listOf("rest", "attention", "avoid", "outside", "play", "food")
        val DEFAULT_EMOTIONS = listOf("calm", "happy", "fearful", "excited", "content", "anxious")
        val DEFAULT_BEHAVIORS = listOf("resting", "paw_raise", "cowering", "freeze", "play_bow", "sniff_ground")
    }

    private var session: ai.onnxruntime.OrtSession? = null
    private var environment: ai.onnxruntime.OrtEnvironment? = null
    private var inputName: String? = null
    private var outputNames: List<String> = listOf("intent_probs", "emotion_probs", "behavior_probs")
    private val window = ArrayDeque<FloatArray>()

    private var intents = DEFAULT_INTENTS
    private var emotions = DEFAULT_EMOTIONS
    private var behaviors = DEFAULT_BEHAVIORS

    /** True when the bundled ONNX model is present and ready to run. */
    val available: Boolean
        get() = session != null

    fun loadLabels(): Boolean = try {
        val text = context.assets.open(MANIFEST_ASSET).use { it.bufferedReader().readText() }
        val j = org.json.JSONObject(text)
        intents = jsonArrayToList(j.optJSONArray("intents")) ?: DEFAULT_INTENTS
        emotions = jsonArrayToList(j.optJSONArray("emotions")) ?: DEFAULT_EMOTIONS
        behaviors = jsonArrayToList(j.optJSONArray("behaviors")) ?: DEFAULT_BEHAVIORS
        true
    } catch (_: Exception) {
        false
    }

    private fun jsonArrayToList(a: org.json.JSONArray?): List<String>? {
        if (a == null || a.length() == 0) return null
        val out = mutableListOf<String>()
        for (i in 0 until a.length()) out.add(a.getString(i))
        return out
    }

    fun init(): Boolean {
        return try {
            if (session != null) true
            loadLabels()
            val bytes = context.assets.open(MODEL_ASSET).use { it.readBytes() }
            val env = ai.onnxruntime.OrtEnvironment.getEnvironment()
            val opts = ai.onnxruntime.OrtSession.SessionOptions()
            val sess = env.createSession(bytes, opts)
            environment = env
            session = sess
            inputName = sess.inputNames.first()
            val outs = sess.outputNames.toList()
            if (outs.size >= 3) outputNames = outs
            true
        } catch (_: Exception) {
            session?.close()
            session = null
            false
        }
    }

    /** Push one camera-derived feature row; runs the model when the window is full. */
    suspend fun pushAndPredict(frame: OnDeviceFrame): TriadPrediction? = withContext(Dispatchers.Default) {
        val sess = session ?: run {
            init()
            session
        } ?: return@withContext null
        val env = environment ?: return@withContext null

        window.addLast(frame.toFeatures())
        while (window.size > SEQUENCE_LEN) window.removeFirst()

        val input = FloatArray(FEATURE_DIM * SEQUENCE_LEN)
        val startPad = SEQUENCE_LEN - window.size
        for (i in 0 until window.size) {
            val row = window[i]
            val base = (startPad + i) * FEATURE_DIM
            for (j in 0 until FEATURE_DIM) {
                input[base + j] = row[j]
            }
        }

        try {
            val tensor = ai.onnxruntime.OnnxTensor.createTensor(
                env,
                FloatBuffer.wrap(input),
                longArrayOf(1, (FEATURE_DIM * SEQUENCE_LEN).toLong()),
            )
            val result = sess.run(mapOf(inputName to tensor))
            val intentOut = result.get(outputNames[0])?.orElse(null)?.value as? Array<FloatArray>
            val emotionOut = result.get(outputNames[1])?.orElse(null)?.value as? Array<FloatArray>
            val behaviorOut = result.get(outputNames[2])?.orElse(null)?.value as? Array<FloatArray>
            result.close()
            tensor.close()
            if (intentOut == null || emotionOut == null || behaviorOut == null) return@withContext null

            val pi = intentOut[0]
            val pe = emotionOut[0]
            val pb = behaviorOut[0]
            val ii = pi.indices.maxByOrNull { pi[it] } ?: 0
            val ei = pe.indices.maxByOrNull { pe[it] } ?: 0
            val bi = pb.indices.maxByOrNull { pb[it] } ?: 0
            val conf = (pi[ii] + pe[ei] + pb[bi]) / 3f

            TriadPrediction(
                intent = intents.getOrElse(ii) { "unknown" },
                emotion = emotions.getOrElse(ei) { "unknown" },
                behavior = behaviors.getOrElse(bi) { "unknown" },
                confidence = conf,
                gate = when {
                    conf >= 0.7f -> "pass"
                    conf <= 0.45f -> "reject"
                    else -> "review"
                },
                dogPresent = frame.dogPresent >= 0.5f,
            )
        } catch (_: Exception) {
            null
        }
    }
}

/** A single on-device camera frame with the features the phone can estimate. */
data class OnDeviceFrame(
    val brightness: Float,
    val contrast: Float,
    val motion: Float,
    val width: Int,
    val height: Int,
    val dogPresent: Float,
) {
    fun toFeatures(): FloatArray {
        val f = FloatArray(OnDeviceEngine.FEATURE_DIM)
        f[0] = dogPresent                       // dog_present
        f[5] = motion.coerceIn(0f, 1f)          // motion
        f[16] = brightness.coerceIn(0f, 1f)     // brightness
        f[17] = contrast.coerceIn(0f, 1f)       // contrast
        f[18] = if (height > 0) (width.toFloat() / height) else 1f  // aspect_ratio
        return f
    }
}
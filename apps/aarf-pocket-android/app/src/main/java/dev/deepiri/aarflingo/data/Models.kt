package dev.deepiri.aarflingo.data

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
)

class AppViewModel : ViewModel() {
    var runtimeUrl by mutableStateOf("http://10.0.2.2:8765")
    var connected by mutableStateOf(false)
    var liveOn by mutableStateOf(false)
    var prediction by mutableStateOf(TriadPrediction.Demo)
    var autoConnect by mutableStateOf(false)
    var selectedIntentFilter by mutableStateOf<String?>(null)

    var history by mutableStateOf(
        listOf(
            HistoryItem(intent = "play", emotion = "excited", behavior = "play_bow", confidence = 0.89f),
            HistoryItem(intent = "food", emotion = "content", behavior = "sniff_ground", confidence = 0.76f),
        ),
    )

    val uniqueIntents: List<String>
        get() = history.map { it.intent }.distinct().sorted()

    val filteredHistory: List<HistoryItem>
        get() = selectedIntentFilter?.let { f -> history.filter { it.intent == f } } ?: history

    val intentCounts: Map<String, Int>
        get() = history.groupBy { it.intent }.mapValues { it.value.size }

    val averageConfidence: Float
        get() = if (history.isEmpty()) 0f else history.map { it.confidence }.average().toFloat()

    fun refreshMock() {
        connected = true
        prediction = TriadPrediction.randomDemo()
        history = listOf(
            HistoryItem(
                intent = prediction.intent,
                emotion = prediction.emotion,
                behavior = prediction.behavior,
                confidence = prediction.confidence,
            ),
        ) + history.take(49)
    }

    fun clearHistory() {
        history = emptyList()
    }
}

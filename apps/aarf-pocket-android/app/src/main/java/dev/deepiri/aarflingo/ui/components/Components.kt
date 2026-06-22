package dev.deepiri.aarflingo.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.TriadPrediction
import dev.deepiri.aarflingo.ui.theme.AarflingoColors

@Composable
fun StatusChip(label: String, tone: ChipTone) {
    val (bg, fg) = when (tone) {
        ChipTone.Ok -> AarflingoColors.Accent to AarflingoColors.Accent
        ChipTone.Warn -> AarflingoColors.Warn to AarflingoColors.Warn
        ChipTone.Info -> AarflingoColors.Info to AarflingoColors.Info
        ChipTone.Neutral -> AarflingoColors.Muted to AarflingoColors.Muted
    }
    Text(
        text = label,
        modifier = Modifier
            .clip(CircleShape)
            .background(bg.copy(alpha = 0.12f))
            .border(1.dp, bg.copy(alpha = 0.4f), CircleShape)
            .padding(horizontal = 10.dp, vertical = 5.dp),
        color = fg,
        style = MaterialTheme.typography.labelMedium,
    )
}

enum class ChipTone { Ok, Warn, Info, Neutral }

@Composable
fun AarflingoCard(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(AarflingoColors.Card)
            .border(1.dp, AarflingoColors.Border, RoundedCornerShape(14.dp))
            .padding(16.dp),
    ) {
        content()
    }
}

@Composable
fun IntentHeroCard(prediction: TriadPrediction) {
    AarflingoCard {
        Text("CURRENT INTENT", color = AarflingoColors.Muted, style = MaterialTheme.typography.labelSmall)
        Text(prediction.intentLabel, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("${prediction.emotion} · ${prediction.behavior}", color = AarflingoColors.Muted)
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
            ConfidenceRing(prediction.confidence, prediction.gate)
            Column {
                Text("Gate: ${prediction.gate}", fontWeight = FontWeight.SemiBold)
                Text("Dog detected: ${if (prediction.dogPresent) "yes" else "no"}", color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
fun ConfidenceRing(confidence: Float, gate: String) {
    val color = if (gate == "pass") AarflingoColors.Accent else AarflingoColors.Warn
    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(72.dp)) {
        Box(
            Modifier
                .matchParentSize()
                .clip(CircleShape)
                .border(6.dp, AarflingoColors.Border, CircleShape),
        )
        Text("${(confidence * 100).toInt()}%", fontWeight = FontWeight.Bold, color = color)
    }
}

@Composable
fun SignalBar(label: String, value: Float) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
        Box(
            Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(RoundedCornerShape(99.dp))
                .background(AarflingoColors.Border),
        ) {
            Box(
                Modifier
                    .fillMaxWidth(value.coerceIn(0f, 1f))
                    .height(8.dp)
                    .clip(RoundedCornerShape(99.dp))
                    .background(AarflingoColors.Accent),
            )
        }
    }
}

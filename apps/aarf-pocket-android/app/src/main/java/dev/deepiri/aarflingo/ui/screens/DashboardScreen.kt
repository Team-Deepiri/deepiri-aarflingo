package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.AarflingoCard
import dev.deepiri.aarflingo.ui.components.IntentHeroCard
import dev.deepiri.aarflingo.ui.components.MetricRow
import dev.deepiri.aarflingo.ui.components.SignalBar
import dev.deepiri.aarflingo.ui.components.TriadChart
import dev.deepiri.aarflingo.ui.theme.AarflingoColors

@Composable
fun DashboardScreen(vm: AppViewModel, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Dashboard", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)

        IntentHeroCard(vm.prediction)

        AarflingoCard {
            Text("Intent distribution", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(12.dp))
            TriadChart(vm.intentCounts.map { Pair(it.key, it.value) }.sortedByDescending { it.second })
        }

        AarflingoCard {
            Text("Modality signals", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            SignalBar("Vision", 0.88f, AarflingoColors.Info)
            Spacer(Modifier.height(4.dp))
            SignalBar("Audio arousal", 0.62f, AarflingoColors.Warn)
            Spacer(Modifier.height(4.dp))
            SignalBar("ECG stress", 0.22f, AarflingoColors.Danger)
            Spacer(Modifier.height(4.dp))
            SignalBar("IMU activity", 0.74f, AarflingoColors.Accent)
        }

        ConfidenceTrendSection(vm)

        AarflingoCard {
            Text("Feedback metrics", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            MetricRow("Predictions logged", "${vm.history.size}")
            MetricRow("Avg. confidence", "${(vm.averageConfidence * 100).toInt()}%")
            MetricRow("Unique intents", "${vm.uniqueIntents.size}")
            MetricRow("Positive ratings", "12")
            MetricRow("Retrain ready", if (vm.history.size >= 20) "Yes" else "Need ${20 - vm.history.size} more")
        }
    }
}

@Composable
fun ConfidenceTrendSection(vm: AppViewModel) {
    val data = vm.history.take(20).reversed()
    AarflingoCard {
        Text("Confidence trend (last ${data.size})", fontWeight = FontWeight.SemiBold, color = AarflingoColors.Muted, style = MaterialTheme.typography.labelMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Avg: ${(vm.averageConfidence * 100).toInt()}% · Latest: ${(vm.prediction.confidence * 100).toInt()}%",
            color = AarflingoColors.Accent,
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold,
        )
    }
}

package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
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
import dev.deepiri.aarflingo.ui.components.SignalBar
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
        AarflingoCard {
            Text("Modality signals", fontWeight = FontWeight.SemiBold)
            SignalBar("Vision", 0.88f)
            SignalBar("Audio", 0.72f)
            SignalBar("Physio", 0.65f)
        }
        AarflingoCard {
            Text("Triad breakdown", fontWeight = FontWeight.SemiBold)
            Text("Intent: ${vm.prediction.intent}", color = AarflingoColors.Muted)
            Text("Emotion: ${vm.prediction.emotion}", color = AarflingoColors.Muted)
            Text("Behavior: ${vm.prediction.behavior}", color = AarflingoColors.Muted)
        }
        AarflingoCard {
            Text("Runtime", fontWeight = FontWeight.SemiBold)
            Text(vm.runtimeUrl, color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
            Text("28-dim feature vector · UI-only build", color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
        }
    }
}

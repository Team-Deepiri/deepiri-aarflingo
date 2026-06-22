package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.ChipTone
import dev.deepiri.aarflingo.ui.components.IntentHeroCard
import dev.deepiri.aarflingo.ui.components.StatusChip
import dev.deepiri.aarflingo.ui.theme.AarflingoColors

@Composable
fun LiveScreen(vm: AppViewModel, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Live", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatusChip(
                if (vm.connected) "Runtime live" else "Runtime offline",
                if (vm.connected) ChipTone.Ok else ChipTone.Warn,
            )
            StatusChip(
                if (vm.liveOn) "Streaming" else "Idle",
                if (vm.liveOn) ChipTone.Info else ChipTone.Neutral,
            )
        }

        Box(
            Modifier
                .fillMaxWidth()
                .height(300.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(Color.Black),
            contentAlignment = Alignment.Center,
        ) {
            if (vm.liveOn) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("\uD83D\uDC36", fontSize = MaterialTheme.typography.displayLarge.fontSize)
                    Text("Camera preview active", style = MaterialTheme.typography.titleMedium)
                    Text(
                        "On-device ML ships in v0.2 — mock inference running",
                        color = AarflingoColors.Muted,
                        style = MaterialTheme.typography.bodySmall,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 24.dp),
                    )
                    if (vm.connected) {
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            LiveMetric("${(vm.prediction.confidence * 100).toInt()}%", "Confidence")
                            LiveMetric("${vm.history.size}", "Readings")
                            LiveMetric(vm.prediction.gate.uppercase(), "Gate")
                        }
                    }
                }
            } else {
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("\uD83D\uDCF9", fontSize = 48.dp.value)
                    Text("Tap Start to preview", color = AarflingoColors.Muted)
                    Text("Live dog intent inference", color = AarflingoColors.Muted.copy(alpha = 0.6f), style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        if (vm.liveOn) {
            IntentHeroCard(vm.prediction)
        }

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
            Button(
                onClick = {
                    vm.liveOn = !vm.liveOn
                    if (vm.liveOn) {
                        vm.connected = true
                        vm.refreshMock()
                    } else {
                        vm.connected = false
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Accent),
                modifier = Modifier.weight(1f),
            ) {
                Text(if (vm.liveOn) "Stop session" else "Start session")
            }
        }

        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
            Text("TriadNet pipeline · v0.1 UI mock", color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
            Text("Camera, CoreML, and runtime connect land in v0.2", color = AarflingoColors.Muted.copy(alpha = 0.6f), style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
fun LiveMetric(value: String, label: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(value, fontWeight = FontWeight.Bold, color = AarflingoColors.Text, style = MaterialTheme.typography.titleSmall)
        Text(label, color = AarflingoColors.Muted, fontSize = MaterialTheme.typography.labelSmall.fontSize)
    }
}

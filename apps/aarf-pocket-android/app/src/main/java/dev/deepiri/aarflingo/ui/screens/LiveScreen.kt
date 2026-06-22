package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.AarflingoCard
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
            StatusChip(if (vm.connected) "Runtime connected" else "Offline", if (vm.connected) ChipTone.Ok else ChipTone.Warn)
            StatusChip(if (vm.liveOn) "Streaming" else "Idle", if (vm.liveOn) ChipTone.Info else ChipTone.Neutral)
        }
        Box(
            Modifier
                .fillMaxWidth()
                .height(220.dp)
                .clip(RoundedCornerShape(14.dp))
                .background(AarflingoColors.Card),
            contentAlignment = Alignment.Center,
        ) {
            Text("Camera preview\n(ML pipeline coming soon)", color = AarflingoColors.Muted)
        }
        IntentHeroCard(vm.prediction)
        Button(
            onClick = {
                vm.liveOn = !vm.liveOn
                if (vm.liveOn) vm.refreshMock()
            },
            colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Accent),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(if (vm.liveOn) "Stop live session" else "Start live session")
        }
    }
}

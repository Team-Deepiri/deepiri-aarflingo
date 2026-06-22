package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.AarflingoCard
import dev.deepiri.aarflingo.ui.theme.AarflingoColors

@Composable
fun SettingsScreen(vm: AppViewModel, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Settings", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        AarflingoCard {
            Text("Runtime URL", fontWeight = FontWeight.SemiBold)
            OutlinedTextField(
                value = vm.runtimeUrl,
                onValueChange = { vm.runtimeUrl = it },
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = AarflingoColors.Accent,
                    unfocusedBorderColor = AarflingoColors.Border,
                    focusedTextColor = AarflingoColors.Text,
                    unfocusedTextColor = AarflingoColors.Text,
                ),
            )
            Text(
                "Emulator default: 10.0.2.2 maps to host localhost. WSL: use Windows host IP.",
                color = AarflingoColors.Muted,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(top = 8.dp),
            )
        }
        AarflingoCard {
            Text("About", fontWeight = FontWeight.SemiBold)
            Text("Aarflingo Pocket · UI shell", color = AarflingoColors.Muted)
            Text("ML inference hooks land in a future release.", color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
        }
        Button(
            onClick = { vm.refreshMock() },
            colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Accent),
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Simulate prediction")
        }
    }
}

package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
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
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Settings", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)

        AarflingoCard {
            Text("Runtime API", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("\uD83D\uDCF6", fontSize = MaterialTheme.typography.titleMedium.fontSize)
                Spacer(Modifier.width(8.dp))
                TextField(vm, Modifier.weight(1f))
            }
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Auto-connect on launch", color = AarflingoColors.Text)
                Switch(
                    checked = vm.autoConnect,
                    onCheckedChange = { vm.autoConnect = it },
                    colors = SwitchDefaults.colors(checkedThumbColor = AarflingoColors.Accent),
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(
                "Connects to Aarflingo runtime for live TriadNet inference (v0.2).",
                color = AarflingoColors.Muted,
                style = MaterialTheme.typography.bodySmall,
            )
        }

        AarflingoCard {
            Text("Preferences", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Haptic feedback", color = AarflingoColors.Text)
                Switch(
                    checked = true,
                    onCheckedChange = {},
                    colors = SwitchDefaults.colors(checkedThumbColor = AarflingoColors.Accent),
                )
            }
        }

        AarflingoCard {
            Text("Debug", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = { vm.refreshMock() },
                colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Accent),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Simulate prediction")
            }
        }

        AarflingoCard {
            Text("About", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Version", color = AarflingoColors.Muted)
                Text("0.1.0")
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Bundle", color = AarflingoColors.Muted)
                Text("dev.deepiri.aarflingo-pocket")
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("ML Engine", color = AarflingoColors.Muted)
                Text("Stub — UI only")
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Framework", color = AarflingoColors.Muted)
                Text("TriadNet (mock)")
            }
        }

        AarflingoCard {
            Text("Help", fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(8.dp))
            Button(
                onClick = { vm.showOnboarding = true },
                colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Card),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Show onboarding", color = AarflingoColors.Accent)
            }
        }
    }
}

@Composable
private fun TextField(vm: AppViewModel, modifier: Modifier = Modifier) {
    OutlinedTextField(
        value = vm.runtimeUrl,
        onValueChange = { vm.runtimeUrl = it },
        modifier = modifier,
        singleLine = true,
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = AarflingoColors.Accent,
            unfocusedBorderColor = AarflingoColors.Border,
            focusedTextColor = AarflingoColors.Text,
            unfocusedTextColor = AarflingoColors.Text,
            cursorColor = AarflingoColors.Accent,
        ),
    )
}

package dev.deepiri.aarflingo.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.screens.DashboardScreen
import dev.deepiri.aarflingo.ui.screens.HistoryScreen
import dev.deepiri.aarflingo.ui.screens.LiveScreen
import dev.deepiri.aarflingo.ui.screens.SettingsScreen
import dev.deepiri.aarflingo.ui.theme.AarflingoColors

@Composable
fun AarflingoApp(viewModel: AppViewModel) {
    var tab by remember { mutableIntStateOf(0) }
    val tabs = listOf("Live", "Dashboard", "History", "Settings")

    if (viewModel.showOnboarding) {
        OnboardingDialog(onDismiss = { viewModel.showOnboarding = false })
    }

    Scaffold(
        containerColor = AarflingoColors.Bg,
        bottomBar = {
            NavigationBar(containerColor = AarflingoColors.Card) {
                NavigationBarItem(
                    selected = tab == 0,
                    onClick = { tab = 0 },
                    icon = { Icon(Icons.Default.Videocam, contentDescription = null) },
                    label = { Text(tabs[0]) },
                )
                NavigationBarItem(
                    selected = tab == 1,
                    onClick = { tab = 1 },
                    icon = { Icon(Icons.Default.Speed, contentDescription = null) },
                    label = { Text(tabs[1]) },
                )
                NavigationBarItem(
                    selected = tab == 2,
                    onClick = { tab = 2 },
                    icon = { Icon(Icons.Default.History, contentDescription = null) },
                    label = { Text(tabs[2]) },
                )
                NavigationBarItem(
                    selected = tab == 3,
                    onClick = { tab = 3 },
                    icon = { Icon(Icons.Default.Settings, contentDescription = null) },
                    label = { Text(tabs[3]) },
                )
            }
        },
    ) { padding ->
        when (tab) {
            0 -> LiveScreen(viewModel, Modifier.padding(padding))
            1 -> DashboardScreen(viewModel, Modifier.padding(padding))
            2 -> HistoryScreen(viewModel, Modifier.padding(padding))
            else -> SettingsScreen(viewModel, Modifier.padding(padding))
        }
    }
}

@Composable
fun OnboardingDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Get started", color = AarflingoColors.Accent)
            }
        },
        containerColor = AarflingoColors.Card,
        title = {
            Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxSize()) {
                Text("\uD83D\uDC36", fontSize = MaterialTheme.typography.displayMedium.fontSize)
                Spacer(Modifier.height(8.dp))
                Text("Welcome to Aarflingo Pocket", fontWeight = FontWeight.Bold, textAlign = TextAlign.Center)
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                OnboardingStep("\uD83D\uDCF9", "Live monitoring", "Point your camera at your dog and get real-time intent predictions — play, food, rest, and more.")
                OnboardingStep("\uD83D\uDCCA", "Triad dashboard", "View intent distribution, confidence trends, and multi-modal signal strengths at a glance.")
                OnboardingStep("\uD83D\uDD53", "History & analytics", "Review past predictions, filter by intent, and track behavioral patterns over time.")
                OnboardingStep("\uD83D\uDD17", "Runtime connect", "Connect to the Aarflingo runtime for live TriadNet inference. Configure the URL in Settings.")
            }
        },
    )
}

@Composable
fun OnboardingStep(icon: String, title: String, description: String) {
    Row(verticalAlignment = Alignment.Top) {
        Text(icon, fontSize = MaterialTheme.typography.titleLarge.fontSize)
        Spacer(Modifier.width(12.dp))
        Column {
            Text(title, fontWeight = FontWeight.SemiBold, color = AarflingoColors.Text)
            Text(description, color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
        }
    }
}

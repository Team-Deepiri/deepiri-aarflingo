package dev.deepiri.aarflingo.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.Videocam
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
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

package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.AarflingoCard
import dev.deepiri.aarflingo.ui.theme.AarflingoColors
import java.text.SimpleDateFormat
import java.util.Locale

@Composable
fun HistoryScreen(vm: AppViewModel, modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxSize().padding(16.dp)) {
        Text("History", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.padding(top = 12.dp)) {
            items(vm.history, key = { it.id }) { item ->
                AarflingoCard {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Column {
                            Text(item.intent.replaceFirstChar { it.uppercase() }, fontWeight = FontWeight.SemiBold)
                            Text("${item.emotion} · ${item.behavior}", color = AarflingoColors.Muted, style = MaterialTheme.typography.bodySmall)
                        }
                        Text("${(item.confidence * 100).toInt()}%", color = AarflingoColors.Accent, fontWeight = FontWeight.Bold)
                    }
                    Text(
                        SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(item.timestamp),
                        color = AarflingoColors.Muted,
                        style = MaterialTheme.typography.labelSmall,
                    )
                }
            }
        }
    }
}

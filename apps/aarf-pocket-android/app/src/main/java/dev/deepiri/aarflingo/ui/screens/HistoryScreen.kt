package dev.deepiri.aarflingo.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.AarflingoCard
import dev.deepiri.aarflingo.ui.theme.AarflingoColors
import java.text.SimpleDateFormat
import java.util.Locale

@Composable
fun HistoryScreen(vm: AppViewModel, modifier: Modifier = Modifier) {
    var searchText by remember { mutableStateOf("") }

    val displayedItems = remember(searchText, vm.selectedIntentFilter, vm.history) {
        val filtered = vm.selectedIntentFilter?.let { f -> vm.history.filter { it.intent == f } } ?: vm.history
        if (searchText.isBlank()) filtered
        else filtered.filter {
            it.intent.contains(searchText, ignoreCase = true) ||
            it.emotion.contains(searchText, ignoreCase = true) ||
            it.behavior.contains(searchText, ignoreCase = true)
        }
    }

    Column(modifier = modifier.fillMaxSize()) {
        Text(
            "History",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(start = 16.dp, top = 0.dp, end = 16.dp, bottom = 8.dp),
        )

        if (vm.history.isNotEmpty()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                FilterChip("All", vm.selectedIntentFilter == null) { vm.selectedIntentFilter = null }
                vm.uniqueIntents.forEach { intent ->
                    FilterChip(
                        "${emoji(intent)} ${intent.replaceFirstChar { it.uppercase() }}",
                        vm.selectedIntentFilter == intent,
                    ) { vm.selectedIntentFilter = intent }
                }
            }

            Spacer(Modifier.height(4.dp))

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp)
                    .clip(RoundedCornerShape(8.dp))
                    .background(AarflingoColors.Card)
                    .border(1.dp, AarflingoColors.Border, RoundedCornerShape(8.dp))
                    .padding(horizontal = 12.dp, vertical = 4.dp),
            ) {
                MaterialTheme(
                    colorScheme = MaterialTheme.colorScheme.copy(
                        onSurface = AarflingoColors.Text,
                        surface = AarflingoColors.Card,
                    ),
                ) {
                    androidx.compose.material3.TextField(
                        value = searchText,
                        onValueChange = { searchText = it },
                        placeholder = { Text("Search intents, emotions...", color = AarflingoColors.Muted) },
                        singleLine = true,
                        colors = androidx.compose.material3.TextFieldDefaults.colors(
                            focusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
                            unfocusedContainerColor = androidx.compose.ui.graphics.Color.Transparent,
                            focusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                            unfocusedIndicatorColor = androidx.compose.ui.graphics.Color.Transparent,
                            cursorColor = AarflingoColors.Accent,
                            focusedTextColor = AarflingoColors.Text,
                            unfocusedTextColor = AarflingoColors.Text,
                        ),
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        }

        if (displayedItems.isEmpty()) {
            Column(
                modifier = Modifier.fillMaxSize().padding(top = 100.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text("\uD83D\uDD53", fontSize = 48.dp.value)
                Text("No history yet", style = MaterialTheme.typography.titleMedium, color = AarflingoColors.Muted)
                Text("Start a live session to see predictions here", color = AarflingoColors.Muted.copy(alpha = 0.6f), style = MaterialTheme.typography.bodySmall)
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(10.dp),
                modifier = Modifier.padding(horizontal = 16.dp),
            ) {
                items(displayedItems, key = { it.id }) { item ->
                    AarflingoCard {
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                                Text(item.intentEmoji, fontSize = MaterialTheme.typography.titleLarge.fontSize)
                                Spacer(Modifier.width(8.dp))
                                Column {
                                    Text(item.intent.replaceFirstChar { it.uppercase() }, fontWeight = FontWeight.SemiBold)
                                    Text(
                                        "${item.emotion} · ${item.behavior.replace("_", " ")}",
                                        color = AarflingoColors.Muted,
                                        style = MaterialTheme.typography.bodySmall,
                                    )
                                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            SimpleDateFormat("MMM d, HH:mm", Locale.getDefault()).format(item.timestamp),
                                            color = AarflingoColors.Muted.copy(alpha = 0.7f),
                                            style = MaterialTheme.typography.labelSmall,
                                        )
                                        if (item.confidence >= 0.8f) {
                                            Text("\u2B50", fontSize = 10.dp.value)
                                        }
                                    }
                                }
                            }
                            Text(
                                "${(item.confidence * 100).toInt()}%",
                                fontWeight = FontWeight.Bold,
                                color = if (item.confidence >= 0.8f) AarflingoColors.Accent else AarflingoColors.Warn,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FilterChip(label: String, selected: Boolean, onClick: () -> Unit) {
    Box(
        Modifier
            .clip(CircleShape)
            .background(if (selected) AarflingoColors.Accent.copy(alpha = 0.2f) else AarflingoColors.Card)
            .border(1.dp, if (selected) AarflingoColors.Accent else AarflingoColors.Border, CircleShape)
            .clickable { onClick() }
            .padding(horizontal = 12.dp, vertical = 6.dp),
    ) {
        Text(
            label,
            color = if (selected) AarflingoColors.Accent else AarflingoColors.Muted,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

private fun emoji(intent: String): String = when (intent) {
    "play" -> "\uD83C\uDFBE"
    "food" -> "\uD83C\uDF56"
    "outside" -> "\uD83D\uDEAA"
    "rest" -> "\uD83D\uDE34"
    "avoid" -> "\u26A0\uFE0F"
    "attention" -> "\uD83D\uDC3E"
    else -> "\uD83D\uDC15"
}

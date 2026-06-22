package dev.deepiri.aarflingo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.lifecycle.viewmodel.compose.viewModel
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.AarflingoApp
import dev.deepiri.aarflingo.ui.theme.AarflingoColors

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val dark = darkColorScheme(
                primary = AarflingoColors.Accent,
                background = AarflingoColors.Bg,
                surface = AarflingoColors.Card,
                onBackground = AarflingoColors.Text,
                onSurface = AarflingoColors.Text,
                secondary = AarflingoColors.Info,
                tertiary = AarflingoColors.Warn,
            )
            MaterialTheme(colorScheme = dark, typography = MaterialTheme.typography) {
                AarflingoApp(viewModel = viewModel())
            }
        }
    }
}

package dev.deepiri.aarflingo.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
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
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import dev.deepiri.aarflingo.data.AppViewModel
import dev.deepiri.aarflingo.ui.components.AarflingoCard
import dev.deepiri.aarflingo.ui.components.ChipTone
import dev.deepiri.aarflingo.ui.components.IntentHeroCard
import dev.deepiri.aarflingo.ui.components.SignalBar
import dev.deepiri.aarflingo.ui.components.StatusChip
import dev.deepiri.aarflingo.ui.theme.AarflingoColors
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer

// ── FPS cap for frame uploads ─────────────────────────────────────────────
private const val INFER_FPS = 5
private const val FRAME_INTERVAL_MS = 1000L / INFER_FPS

@Composable
fun LiveScreen(vm: AppViewModel, modifier: Modifier = Modifier) {
    val context       = LocalContext.current
    val lifecycle     = LocalLifecycleOwner.current
    val scope         = rememberCoroutineScope()
    var cameraGranted by remember { mutableStateOf(
        ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
    )}
    var lensFacing    by remember { mutableStateOf(CameraSelector.LENS_FACING_BACK) }
    var lastFrameMs   by remember { mutableStateOf(0L) }

    // ── Permission launcher ───────────────────────────────────────────────
    val permLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> cameraGranted = granted }

    // ── Health check on start ─────────────────────────────────────────────
    LaunchedEffect(vm.runtimeUrl) {
        // Model asset loading + ONNX session creation is heavy — never on the
        // main thread (ANR / UI jank on slow devices).
        launch(Dispatchers.IO) { vm.initOnDevice(context) }
        launch(Dispatchers.IO) { vm.checkHealth() }
    }

    // ── Disconnect on leave ───────────────────────────────────────────────
    DisposableEffect(Unit) {
        onDispose {
            if (vm.liveOn) {
                vm.liveOn = false
                vm.disconnectWs()
            }
        }
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("Live", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)

        // Status chips
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            StatusChip(
                if (vm.onDevice) "On-device engine" else if (vm.connected) "Runtime live" else "Runtime offline",
                if (vm.onDevice) ChipTone.Ok else if (vm.connected) ChipTone.Ok else ChipTone.Warn,
            )
            StatusChip(
                if (vm.liveOn) "Camera live" else "Camera off",
                if (vm.liveOn) ChipTone.Info else ChipTone.Neutral,
            )
        }
        if (!vm.onDeviceAvailable && !vm.onDevice) {
            Row {
                StatusChip(
                    "On-device model not bundled — add via scripts/mobile/bundle-mobile-models.sh",
                    ChipTone.Neutral,
                )
            }
        }

        // Camera preview box
        Box(
            Modifier
                .fillMaxWidth()
                .height(300.dp)
                .clip(RoundedCornerShape(16.dp))
                .background(Color.Black),
            contentAlignment = Alignment.Center,
        ) {
            if (vm.liveOn && cameraGranted) {
                // ── CameraX preview + analysis ────────────────────────
                AndroidView(
                    factory = { ctx ->
                        val previewView = PreviewView(ctx)
                        val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                        cameraProviderFuture.addListener({
                            val cameraProvider = cameraProviderFuture.get()

                            val preview = Preview.Builder().build().also {
                                it.setSurfaceProvider(previewView.surfaceProvider)
                            }

                            val analysis = ImageAnalysis.Builder()
                                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                                .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                                .build()

                            analysis.setAnalyzer(ContextCompat.getMainExecutor(ctx)) { imageProxy ->
                                val now = System.currentTimeMillis()
                                if (now - lastFrameMs >= FRAME_INTERVAL_MS) {
                                    lastFrameMs = now
                                    val jpeg = imageProxy.toJpeg()
                                    imageProxy.close()
                                    scope.launch(Dispatchers.IO) {
                                        vm.inferFrame(jpeg)
                                    }
                                } else {
                                    imageProxy.close()
                                }
                            }

                            val selector = CameraSelector.Builder()
                                .requireLensFacing(lensFacing)
                                .build()

                            runCatching {
                                cameraProvider.unbindAll()
                                cameraProvider.bindToLifecycle(lifecycle, selector, preview, analysis)
                            }
                        }, ContextCompat.getMainExecutor(ctx))
                        previewView
                    },
                    modifier = Modifier.fillMaxSize(),
                )

                // Confidence overlay badge
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.BottomStart) {
                    val pred = vm.prediction
                    val gateColor = when (pred.gate) {
                        "pass"   -> AarflingoColors.Accent
                        "reject" -> AarflingoColors.Danger
                        else     -> AarflingoColors.Warn
                    }
                    Row(
                        modifier = Modifier
                            .padding(12.dp)
                            .background(Color.Black.copy(alpha = 0.55f), RoundedCornerShape(20.dp))
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        Box(
                            Modifier
                                .height(8.dp)
                                .padding(2.dp)
                                .background(gateColor, RoundedCornerShape(4.dp))
                        )
                        Text(
                            "${(pred.confidence * 100).toInt()}% · ${pred.gate}",
                            color = Color.White,
                            style = MaterialTheme.typography.labelSmall,
                        )
                    }
                }
            } else if (!cameraGranted && vm.liveOn) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text("📵", fontSize = MaterialTheme.typography.displayMedium.fontSize)
                    Text("Camera permission required", color = AarflingoColors.Muted, textAlign = TextAlign.Center)
                    Button(
                        onClick = { permLauncher.launch(Manifest.permission.CAMERA) },
                        colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Accent),
                    ) { Text("Grant permission") }
                }
            } else {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text("📹", fontSize = MaterialTheme.typography.displayLarge.fontSize)
                    Text("Tap Start to begin", color = AarflingoColors.Muted)
                    Text(
                        "TriadNet · live dog intent inference",
                        color = AarflingoColors.Muted.copy(alpha = 0.6f),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }

        // Intent card (real predictions)
        if (vm.liveOn) {
            IntentHeroCard(vm.prediction)

            AarflingoCard {
                Text("Live signals", fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(8.dp))
                SignalBar("Confidence", vm.prediction.confidence, AarflingoColors.Accent)
                Spacer(Modifier.height(4.dp))
                SignalBar("Dog detected", if (vm.prediction.dogPresent) 1f else 0f, AarflingoColors.Info)
            }
        }

        // Error display
        vm.lastError?.let { err ->
            Text(
                err,
                color = AarflingoColors.Danger,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(horizontal = 4.dp),
            )
        }

        // Controls
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
            Button(
                onClick = {
                    if (vm.liveOn) {
                        vm.liveOn = false
                        vm.disconnectWs()
                    } else {
                        if (!cameraGranted) {
                            permLauncher.launch(Manifest.permission.CAMERA)
                        }
                        vm.liveOn = true
                        vm.connectWs()
                        scope.launch { vm.checkHealth() }
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Accent),
                modifier = Modifier.weight(1f),
            ) {
                Text(if (vm.liveOn) "Stop" else "Start")
            }

            if (vm.liveOn) {
                Button(
                    onClick = {
                        lensFacing = if (lensFacing == CameraSelector.LENS_FACING_BACK)
                            CameraSelector.LENS_FACING_FRONT
                        else
                            CameraSelector.LENS_FACING_BACK
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = AarflingoColors.Card),
                    modifier = Modifier.weight(1f),
                ) {
                    Text("Flip", color = AarflingoColors.Text)
                }
            }
            if (vm.liveOn && vm.onDeviceAvailable) {
                Button(
                    onClick = { vm.toggleOnDevice() },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (vm.onDevice) AarflingoColors.Accent else AarflingoColors.Card,
                    ),
                    modifier = Modifier.weight(1f),
                ) {
                    Text(
                        if (vm.onDevice) "Local ✓" else "Local",
                        color = if (vm.onDevice) AarflingoColors.Bg else AarflingoColors.Text,
                    )
                }
            }
        }

        Text(
            "Runtime: ${vm.runtimeUrl}",
            color = AarflingoColors.Muted.copy(alpha = 0.6f),
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
        )
    }
}

// ── ImageProxy → JPEG ByteArray ───────────────────────────────────────────
// Requires ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888 set on the builder.

private fun ImageProxy.toJpeg(quality: Int = 70): ByteArray {
    val plane  = planes[0]
    val buffer = plane.buffer.rewind() as java.nio.ByteBuffer
    val bitmap = android.graphics.Bitmap.createBitmap(width, height, android.graphics.Bitmap.Config.ARGB_8888)
    bitmap.copyPixelsFromBuffer(buffer)
    val out = ByteArrayOutputStream()
    bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG, quality, out)
    bitmap.recycle()
    return out.toByteArray()
}

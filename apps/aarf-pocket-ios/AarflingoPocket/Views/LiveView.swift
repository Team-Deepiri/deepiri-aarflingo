import SwiftUI
import AVFoundation

struct LiveView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var camera = CameraManager()
    @StateObject private var engine = OnDeviceEngine()
    @StateObject private var client: RuntimeClient = {
        let stored = UserDefaults.standard.string(forKey: "runtimeURL") ?? "http://127.0.0.1:8765"
        return RuntimeClient(baseURL: URL(string: stored)!)
    }()

    // Reconnect client when runtimeURL changes in settings
    private var runtimeURL: String { appState.runtimeURL }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {

                    // ── Status chips ────────────────────────────────────
                    HStack {
                        StatusChip(
                            label: appState.localMode ? "On-device engine" : (client.connected ? "Runtime live" : "Runtime offline"),
                            tone: appState.localMode || client.connected ? .ok : .warn
                        )
                        StatusChip(
                            label: camera.isRunning ? "Camera live" : "Camera off",
                            tone: camera.isRunning ? .info : .neutral
                        )
                    }
                    if !appState.engineAvailable && !appState.localMode {
                        HStack {
                            StatusChip(
                                label: "On-device model not bundled — run scripts/mobile/bundle-mobile-models.sh",
                                tone: .neutral
                            )
                        }
                    }

                    // ── Camera preview ──────────────────────────────────
                    ZStack(alignment: .bottomLeading) {
                        RoundedRectangle(cornerRadius: 16)
                            .fill(Color.black)
                            .overlay(
                                RoundedRectangle(cornerRadius: 16)
                                    .stroke(AarflingoTheme.border, lineWidth: 1)
                            )
                            .frame(height: 300)
                            .overlay(
                                Group {
                                    if camera.isRunning {
                                        CameraPreviewView(session: camera.session)
                                            .clipShape(RoundedRectangle(cornerRadius: 16))
                                    } else {
                                        VStack(spacing: 12) {
                                            Image(systemName: camera.permissionDenied ? "video.slash" : "video.fill")
                                                .font(.system(size: 48))
                                                .foregroundStyle(AarflingoTheme.muted)
                                            Text(camera.permissionDenied
                                                 ? "Camera access denied — check Settings"
                                                 : "Tap Start to begin")
                                                .foregroundStyle(AarflingoTheme.muted)
                                                .multilineTextAlignment(.center)
                                                .padding(.horizontal)
                                        }
                                    }
                                }
                            )

                        // Confidence badge overlay
                        if camera.isRunning, let pred = activePrediction {
                            HStack(spacing: 6) {
                                Circle()
                                    .fill(gateColor(pred.gate))
                                    .frame(width: 8, height: 8)
                                Text("\(Int(pred.confidence * 100))% · \(pred.gate)")
                                    .font(.caption2.weight(.semibold))
                                    .foregroundStyle(.white)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(.ultraThinMaterial)
                            .clipShape(Capsule())
                            .padding(12)
                        }
                    }

                    // ── Intent card ─────────────────────────────────────
                    if let pred = activePrediction, camera.isRunning {
                        IntentHeroCard(prediction: .init(
                            intent: pred.intent,
                            emotion: pred.emotion,
                            behavior: pred.behavior,
                            confidence: pred.confidence,
                            gate: pred.gate,
                            dogPresent: pred.dogPresent
                        ))

                        // Live signal bars (from runtime features — placeholder ratios for now)
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Live signals").font(.headline)
                            SignalBar(label: "Confidence",
                                          value: pred.confidence,
                                          color: gateColor(pred.gate))
                            SignalBar(label: "Dog detected",
                                          value: pred.dogPresent ? 1.0 : 0.0,
                                          color: AarflingoTheme.info)
                        }
                        .aarflingoCard()
                    }

                    // ── Controls ────────────────────────────────────────
                    HStack(spacing: 10) {
                        Button(camera.isRunning ? "Stop" : "Start") {
                            if camera.isRunning {
                                camera.stop()
                                client.disconnect()
                                engine.resetDiff()
                            } else {
                                startSession()
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle(accent: true))

                        if camera.isRunning {
                            Button {
                                camera.flip()
                            } label: {
                                Label("Flip", systemImage: "arrow.triangle.2.circlepath.camera")
                            }
                            .buttonStyle(PrimaryButtonStyle(accent: false))
                        }

                        if camera.isRunning && engine.available {
                            Button(appState.localMode ? "Local ✓" : "Local") {
                                appState.localMode.toggle()
                            }
                            .buttonStyle(PrimaryButtonStyle(accent: appState.localMode))
                        }
                    }

                    // Error
                    if let err = client.lastError, !appState.localMode {
                        Text(err)
                            .font(.caption)
                            .foregroundStyle(AarflingoTheme.danger)
                            .padding(.horizontal, 4)
                    }

                    // Footer
                    Text(appState.localMode
                         ? "On-device TriadNet · no network needed"
                         : "TriadNet · live inference via \(appState.runtimeURL)")
                        .font(.caption2)
                        .foregroundStyle(AarflingoTheme.muted.opacity(0.6))
                        .frame(maxWidth: .infinity)
                }
                .padding()
            }
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("Live")
            .toolbar {
                ToolbarItem(placement: .principal) {
                    HStack(spacing: 8) {
                        Image("AarflingoLogo")
                            .resizable()
                            .scaledToFit()
                            .frame(height: 28)
                        Text("Aarflingo")
                            .font(.headline)
                    }
                }
            }
            .onChange(of: appState.runtimeURL) { newURL in
                // Reconnect to new URL when changed in Settings
                guard URL(string: newURL) != nil else { return }
                camera.stop()
                client.disconnect()
            }
        }
        // Wire camera frames → runtime on start
        .onDisappear {
            camera.stop()
            client.disconnect()
        }
    }

    // MARK: – Private

    /// Prediction from local engine (when enabled) or the runtime client.
    private var activePrediction: RuntimePrediction? {
        appState.localMode ? localPrediction : client.prediction
    }

    private var localPrediction: RuntimePrediction? {
        guard appState.localMode, camera.isRunning else { return nil }
        let p = appState.prediction
        return RuntimePrediction(
            intent: p.intent,
            emotion: p.emotion,
            behavior: p.behavior,
            confidence: p.confidence,
            gate: p.gate,
            dogPresent: p.dogPresent,
            tsMsRaw: nil
        )
    }

    private func startSession() {
        guard let url = URL(string: appState.runtimeURL) else { return }
        appState.engineAvailable = engine.available

        // Re-create client with current URL
        let freshClient = RuntimeClient(baseURL: url)

        // Wire camera → local engine (when bundled) or POST /infer/frame
        camera.onFrame = { [weak freshClient] jpeg in
            if appState.localMode, let ui = UIImage(data: jpeg) {
                let frame = engine.diffFrame(ui)
                if let pred = engine.pushAndPredict(frame: frame) {
                    await MainActor.run {
                        appState.prediction = pred
                        appState.connected = true
                    }
                }
            } else {
                await freshClient?.inferFrame(jpeg)
            }
        }

        camera.start(fps: 5)

        // Also connect WebSocket for live prediction stream (network mode)
        freshClient.connect()

        // Health check
        Task {
            _ = await freshClient.checkHealth()
        }
    }

    private func gateColor(_ gate: String) -> Color {
        switch gate {
        case "pass":   return AarflingoTheme.accent
        case "reject": return AarflingoTheme.danger
        default:       return AarflingoTheme.warn
        }
    }
}



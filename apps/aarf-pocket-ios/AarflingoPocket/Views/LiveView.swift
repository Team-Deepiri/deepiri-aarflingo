import SwiftUI

struct LiveView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        StatusChip(
                            label: appState.connected ? "Runtime live" : "Runtime offline",
                            tone: appState.connected ? .ok : .warn
                        )
                        StatusChip(
                            label: appState.liveOn ? "Streaming" : "Idle",
                            tone: appState.liveOn ? .info : .neutral
                        )
                    }

                    ZStack {
                        RoundedRectangle(cornerRadius: 16)
                            .fill(Color.black)
                            .overlay(RoundedRectangle(cornerRadius: 16).stroke(AarflingoTheme.border, lineWidth: 1))
                            .frame(height: 300)

                        if appState.liveOn {
                            VStack(spacing: 8) {
                                Image(systemName: "dog.fill")
                                    .font(.system(size: 64))
                                    .foregroundStyle(AarflingoTheme.accent.opacity(0.8))
                                Text("Camera preview active")
                                    .font(.headline)
                                Text("On-device ML ships in v0.2 — mock inference running")
                                    .font(.caption)
                                    .foregroundStyle(AarflingoTheme.muted)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal)
                            }
                            .overlay(alignment: .center) {
                                RoundedRectangle(cornerRadius: 10)
                                    .stroke(AarflingoTheme.accent, lineWidth: 2)
                                    .frame(width: 180, height: 140)
                                    .opacity(0.6)
                            }
                        } else {
                            VStack(spacing: 12) {
                                Image(systemName: "video.slash")
                                    .font(.system(size: 48))
                                    .foregroundStyle(AarflingoTheme.muted)
                                Text("Tap Start to preview")
                                    .foregroundStyle(AarflingoTheme.muted)
                                Text("Live dog intent inference")
                                    .font(.caption2)
                                    .foregroundStyle(AarflingoTheme.muted.opacity(0.6))
                            }
                        }
                    }

                    IntentHeroCard(prediction: appState.prediction)

                    HStack(spacing: 10) {
                        Button(appState.liveOn ? "Stop session" : "Start session") {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                appState.liveOn.toggle()
                                if appState.liveOn {
                                    appState.connected = true
                                    appState.refreshMock()
                                } else {
                                    appState.connected = false
                                }
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle())
                    }

                    Text("ML models (TriadNet, vocal, vitals) will run on-device via CoreML in a future release.")
                        .font(.caption)
                        .foregroundStyle(AarflingoTheme.muted)
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
        }
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(AarflingoTheme.accent.opacity(configuration.isPressed ? 0.7 : 1))
            .foregroundStyle(Color.black.opacity(0.85))
            .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

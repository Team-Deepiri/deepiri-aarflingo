import SwiftUI

struct LiveView: View {
    @EnvironmentObject private var appState: AppState
    @State private var liveOn = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    HStack {
                        StatusChip(label: appState.connected ? "Runtime live" : "Runtime offline", tone: appState.connected ? .ok : .warn)
                        StatusChip(label: liveOn ? "Preview on" : "Preview off", tone: liveOn ? .ok : .neutral)
                    }

                    ZStack {
                        RoundedRectangle(cornerRadius: 16)
                            .fill(Color.black)
                            .overlay(RoundedRectangle(cornerRadius: 16).stroke(AarflingoTheme.border, lineWidth: 1))
                            .frame(height: 280)

                        if liveOn {
                            VStack(spacing: 8) {
                                Image(systemName: "dog.fill")
                                    .font(.system(size: 56))
                                    .foregroundStyle(AarflingoTheme.accent.opacity(0.8))
                                Text("Camera preview")
                                    .font(.headline)
                                Text("On-device ML ships in v0.2 — mock inference active")
                                    .font(.caption)
                                    .foregroundStyle(AarflingoTheme.muted)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal)
                            }
                            .overlay(alignment: .center) {
                                RoundedRectangle(cornerRadius: 10)
                                    .stroke(AarflingoTheme.accent, lineWidth: 2)
                                    .frame(width: 160, height: 120)
                                    .opacity(0.85)
                            }
                        } else {
                            VStack(spacing: 8) {
                                Image(systemName: "video.slash")
                                    .font(.largeTitle)
                                    .foregroundStyle(AarflingoTheme.muted)
                                Text("Tap Start to preview")
                                    .foregroundStyle(AarflingoTheme.muted)
                            }
                        }
                    }

                    IntentHeroCard(prediction: appState.prediction)

                    HStack(spacing: 10) {
                        Button(liveOn ? "Stop" : "Start") {
                            liveOn.toggle()
                            if liveOn {
                                appState.connected = true
                                appState.refreshMock()
                            } else {
                                appState.connected = false
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle())

                        Button("Simulate") {
                            appState.refreshMock()
                        }
                        .buttonStyle(SecondaryButtonStyle())
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

struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(AarflingoTheme.card.opacity(configuration.isPressed ? 0.7 : 1))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(AarflingoTheme.border, lineWidth: 1))
            .foregroundStyle(AarflingoTheme.text)
            .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

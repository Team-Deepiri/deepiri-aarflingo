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
                                if appState.connected {
                                    HStack(spacing: 12) {
                                        LiveMetric(value: "\(Int(appState.prediction.confidence * 100))%", label: "Confidence")
                                        LiveMetric(value: "\(appState.history.count)", label: "Readings")
                                        LiveMetric(value: appState.prediction.gate.uppercased(), label: "Gate")
                                    }
                                    .padding(.top, 4)
                                }
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

                    if appState.liveOn {
                        IntentHeroCard(prediction: appState.prediction)

                        VStack(alignment: .leading, spacing: 12) {
                            Text("Live signals")
                                .font(.headline)
                            LiveSignalBar(label: "Vision", value: 0.88, color: AarflingoTheme.info)
                            LiveSignalBar(label: "Audio", value: 0.62, color: AarflingoTheme.warn)
                            LiveSignalBar(label: "Heart rate", value: 0.35, color: AarflingoTheme.danger)
                            LiveSignalBar(label: "Motion", value: 0.74, color: AarflingoTheme.accent)
                        }
                        .aarflingoCard()
                    }

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
                        .buttonStyle(PrimaryButtonStyle(accent: true))

                        Button("Simulate") {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                appState.refreshMock()
                            }
                        }
                        .buttonStyle(PrimaryButtonStyle(accent: false))
                    }

                    VStack(spacing: 4) {
                        Text("TriadNet pipeline · v0.1 UI mock")
                            .font(.caption)
                            .foregroundStyle(AarflingoTheme.muted)
                        Text("Camera, CoreML, and runtime connect land in v0.2")
                            .font(.caption2)
                            .foregroundStyle(AarflingoTheme.muted.opacity(0.6))
                    }
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
        }
    }
}

struct LiveMetric: View {
    let value: String
    let label: String

    var body: some View {
        VStack(spacing: 2) {
            Text(value)
                .font(.headline.weight(.bold))
                .foregroundStyle(AarflingoTheme.text)
            Text(label)
                .font(.system(size: 9))
                .foregroundStyle(AarflingoTheme.muted)
        }
        .frame(minWidth: 60)
        .padding(8)
        .background(AarflingoTheme.card.opacity(0.6))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

struct LiveSignalBar: View {
    let label: String
    let value: Double
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(label).font(.caption).foregroundStyle(AarflingoTheme.muted)
                Spacer()
                Text("\(Int(value * 100))%")
                    .font(.caption2)
                    .foregroundStyle(AarflingoTheme.muted)
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(AarflingoTheme.border)
                    Capsule()
                        .fill(color)
                        .frame(width: geo.size.width * value)
                        .animation(.easeOut(duration: 0.4), value: value)
                }
            }
            .frame(height: 6)
        }
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    let accent: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(
                accent
                    ? AarflingoTheme.accentGradient
                    : LinearGradient(colors: [AarflingoTheme.card, AarflingoTheme.border], startPoint: .leading, endPoint: .trailing)
            )
            .foregroundStyle(accent ? Color.black.opacity(0.85) : AarflingoTheme.text)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
    }
}

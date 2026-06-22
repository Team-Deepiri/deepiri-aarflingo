import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        Label("Runtime URL", systemImage: "antenna.radiowaves.left.and.right")
                            .font(.subheadline.weight(.semibold))
                        TextField("URL", text: $appState.runtimeURL)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .padding(10)
                            .background(AarflingoTheme.card)
                            .overlay(RoundedRectangle(cornerRadius: 8).stroke(AarflingoTheme.border, lineWidth: 1))
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                    Toggle(isOn: $appState.autoConnect) {
                        Label("Auto-connect on launch", systemImage: "link.icloud")
                    }
                    .tint(AarflingoTheme.accent)
                    Text("Connects to Aarflingo runtime for live TriadNet inference (v0.2).")
                        .font(.caption)
                        .foregroundStyle(AarflingoTheme.muted)
                } header: {
                    Text("Runtime API")
                }

                Section {
                    Toggle(isOn: $appState.hapticsEnabled) {
                        Label("Haptic feedback", systemImage: "iphone.radiowaves.left.and.right")
                    }
                    .tint(AarflingoTheme.accent)
                } header: {
                    Text("Preferences")
                }

                Section {
                    Button(action: { appState.refreshMock() }) {
                        Label("Simulate prediction", systemImage: "play.fill")
                            .frame(maxWidth: .infinity)
                    }
                    .listRowBackground(AarflingoTheme.accent.opacity(0.2))
                    .tint(AarflingoTheme.accent)
                } header: {
                    Text("Debug")
                }

                Section {
                    LabeledContent("Version", value: "0.1.0")
                    LabeledContent("Bundle", value: "dev.deepiri.aarflingo-pocket")
                    LabeledContent("ML Engine", value: "Stub — UI only")
                    LabeledContent("Framework", value: "TriadNet (mock)")
                    LabeledContent("Platform", value: "iOS \(UIDevice.current.systemVersion)")
                } header: {
                    Text("About")
                }

                Section {
                    Button(action: { appState.showOnboarding = true }) {
                        Label("Show onboarding", systemImage: "hand.wave")
                    }
                } header: {
                    Text("Help")
                }

                Section {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Aarflingo Pocket")
                            .font(.subheadline.weight(.semibold))
                        Text("On-the-go dog intent monitoring. This is a UI shell — ML inference hooks land in v0.2. Built with the Aarflingo TriadNet multimodal stack.")
                            .font(.caption)
                            .foregroundStyle(AarflingoTheme.muted)
                    }
                } header: {
                    Text("")
                }
            }
            .scrollContentBackground(.hidden)
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("Settings")
            .sheet(isPresented: $appState.showOnboarding) {
                OnboardingView()
            }
        }
    }
}

struct OnboardingView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    Image(systemName: "dog.fill")
                        .font(.system(size: 72))
                        .foregroundStyle(AarflingoTheme.accent)
                    Text("Welcome to Aarflingo Pocket")
                        .font(.title.bold())
                        .multilineTextAlignment(.center)

                    VStack(alignment: .leading, spacing: 16) {
                        OnboardingStep(icon: "video.fill", title: "Live monitoring", description: "Point your camera at your dog and get real-time intent predictions — play, food, rest, and more.")
                        OnboardingStep(icon: "gauge.with.dots.needle.67percent", title: "Triad dashboard", description: "View intent distribution, confidence trends, and multi-modal signal strengths at a glance.")
                        OnboardingStep(icon: "clock.arrow.circlepath", title: "History & analytics", description: "Review past predictions, filter by intent, and track behavioral patterns over time.")
                        OnboardingStep(icon: "link.circle", title: "Runtime connect", description: "Connect to the Aarflingo runtime for live TriadNet inference. Configure the URL in Settings.")
                    }
                    .padding(.horizontal)
                }
                .padding()
            }
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Get started") { dismiss() }
                }
            }
        }
    }
}

struct OnboardingStep: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(AarflingoTheme.accent)
                .frame(width: 36)
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.subheadline.weight(.semibold))
                Text(description).font(.caption).foregroundStyle(AarflingoTheme.muted)
            }
        }
    }
}

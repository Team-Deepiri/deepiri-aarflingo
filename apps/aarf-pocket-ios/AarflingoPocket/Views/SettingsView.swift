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
        }
    }
}

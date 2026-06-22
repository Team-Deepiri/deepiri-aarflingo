import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            Form {
                Section("Runtime API") {
                    TextField("URL", text: $appState.runtimeURL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Text("Connects to Aarflingo runtime for live inference (v0.2).")
                        .font(.caption)
                        .foregroundStyle(AarflingoTheme.muted)
                }
                Section("About") {
                    LabeledContent("Version", value: "0.1.0")
                    LabeledContent("Bundle", value: "dev.deepiri.aarflingo-pocket")
                    LabeledContent("ML", value: "Stub — UI only")
                }
            }
            .scrollContentBackground(.hidden)
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("Settings")
        }
    }
}

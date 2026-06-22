import SwiftUI

struct HistoryView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            List {
                ForEach(appState.history) { item in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.intent.capitalized)
                            .font(.headline)
                        Text("\(item.emotion) · \(item.behavior)")
                            .font(.subheadline)
                            .foregroundStyle(AarflingoTheme.muted)
                        HStack {
                            Text(item.timestamp, style: .relative)
                            Spacer()
                            Text("\(Int(item.confidence * 100))%")
                                .foregroundStyle(AarflingoTheme.accent)
                        }
                        .font(.caption)
                    }
                    .listRowBackground(AarflingoTheme.card)
                }
            }
            .scrollContentBackground(.hidden)
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("History")
        }
    }
}

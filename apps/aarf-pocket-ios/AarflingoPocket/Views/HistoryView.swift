import SwiftUI

struct HistoryView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            List {
                ForEach(appState.history) { item in
                    HistoryRow(item: item)
                        .listRowBackground(AarflingoTheme.card)
                }
            }
            .scrollContentBackground(.hidden)
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("History")
        }
    }
}

struct FilterChip: View {
    let label: String
    let selected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(.caption.weight(.semibold))
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(selected ? AarflingoTheme.accent.opacity(0.2) : AarflingoTheme.card)
                .overlay(Capsule().stroke(selected ? AarflingoTheme.accent : AarflingoTheme.border, lineWidth: 1))
                .foregroundStyle(selected ? AarflingoTheme.accent : AarflingoTheme.muted)
                .clipShape(Capsule())
        }
    }
}

struct HistoryRow: View {
    let item: HistoryItem

    var body: some View {
        HStack(spacing: 12) {
            Text(item.intentEmoji)
                .font(.title2)
            VStack(alignment: .leading, spacing: 2) {
                Text(item.intent.capitalized)
                    .font(.headline)
                Text("\(item.emotion) · \(item.behavior.replacingOccurrences(of: "_", with: " "))")
                    .font(.subheadline)
                    .foregroundStyle(AarflingoTheme.muted)
                HStack(spacing: 8) {
                    Text(item.timestamp, style: .relative)
                        .font(.caption2)
                        .foregroundStyle(AarflingoTheme.muted.opacity(0.7))
                    if item.confidence >= 0.8 {
                        Image(systemName: "star.fill")
                            .font(.system(size: 8))
                            .foregroundStyle(AarflingoTheme.warn)
                    }
                }
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text("\(Int(item.confidence * 100))%")
                    .font(.headline.weight(.bold))
                    .foregroundStyle(item.confidence >= 0.8 ? AarflingoTheme.accent : AarflingoTheme.warn)
            }
        }
        .padding(.vertical, 4)
    }
}

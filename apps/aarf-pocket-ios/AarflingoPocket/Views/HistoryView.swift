import SwiftUI

struct HistoryView: View {
    @EnvironmentObject private var appState: AppState
    @State private var searchText = ""

    var displayedItems: [HistoryItem] {
        let items = appState.history
        guard !searchText.isEmpty else { return items }
        return items.filter {
            $0.intent.localizedCaseInsensitiveContains(searchText) ||
            $0.emotion.localizedCaseInsensitiveContains(searchText) ||
            $0.behavior.localizedCaseInsensitiveContains(searchText)
        }
    }

    var groupedItems: [String: [HistoryItem]] {
        let calendar = Calendar.current
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.doesRelativeDateFormatting = true
        return Dictionary(grouping: displayedItems) { item in
            if calendar.isDateInToday(item.timestamp) { return "Today" }
            if calendar.isDateInYesterday(item.timestamp) { return "Yesterday" }
            return formatter.string(from: item.timestamp)
        }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if displayedItems.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "clock.arrow.circlepath")
                            .font(.system(size: 48))
                            .foregroundStyle(AarflingoTheme.muted)
                        Text("No history yet")
                            .font(.headline)
                            .foregroundStyle(AarflingoTheme.muted)
                        Text("Start a live session to see predictions here")
                            .font(.caption)
                            .foregroundStyle(AarflingoTheme.muted.opacity(0.6))
                    }
                    .frame(maxHeight: .infinity)
                    .padding(.top, 60)
                } else {
                    List {
                        ForEach(groupedItems.keys.sorted(by: >), id: \.self) { section in
                            Section(
                                header: Text(section)
                                    .font(.subheadline.weight(.semibold))
                                    .foregroundStyle(AarflingoTheme.text)
                            ) {
                                ForEach(groupedItems[section]!) { item in
                                    HistoryRow(item: item)
                                        .listRowBackground(AarflingoTheme.card)
                                        .listRowSeparator(.hidden)
                                }
                            }
                        }
                    }
                    .scrollContentBackground(.hidden)
                }
            }
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("History")
            .searchable(text: $searchText, prompt: "Search intents, emotions...")
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

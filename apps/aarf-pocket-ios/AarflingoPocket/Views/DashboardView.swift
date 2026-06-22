import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    IntentHeroCard(prediction: appState.prediction)

                    VStack(alignment: .leading, spacing: 12) {
                        Text("Intent distribution")
                            .font(.headline)
                        TriadChart(counts: appState.intentCounts.map { ($0.key, $0.value) }.sorted { $0.1 > $1.1 })
                    }
                    .aarflingoCard()

                    VStack(alignment: .leading, spacing: 12) {
                        Text("Modality signals")
                            .font(.headline)
                        SignalBar(label: "Vision", value: 0.88, color: AarflingoTheme.info)
                        SignalBar(label: "Audio arousal", value: 0.62, color: AarflingoTheme.warn)
                        SignalBar(label: "ECG stress", value: 0.22, color: AarflingoTheme.danger)
                        SignalBar(label: "IMU activity", value: 0.74, color: AarflingoTheme.accent)
                    }
                    .aarflingoCard()

                    ConfidenceTrendChart(items: appState.history)

                    VStack(alignment: .leading, spacing: 12) {
                        Text("Feedback metrics")
                            .font(.headline)
                        MetricRow(label: "Predictions logged", value: "\(appState.history.count)")
                        MetricRow(label: "Avg. confidence", value: "\(Int(appState.averageConfidence * 100))%")
                        MetricRow(label: "Unique intents", value: "\(appState.uniqueIntents.count)")
                        MetricRow(label: "Positive ratings", value: "12")
                        MetricRow(label: "Retrain ready", value: appState.history.count >= 20 ? "Yes" : "Need \(20 - appState.history.count) more")
                    }
                    .aarflingoCard()
                }
                .padding()
            }
            .background(AarflingoTheme.gradient.ignoresSafeArea())
            .navigationTitle("Dashboard")
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

struct SignalBar: View {
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
                        .animation(.easeOut(duration: 0.5), value: value)
                }
            }
            .frame(height: 8)
        }
    }
}

struct MetricRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label).foregroundStyle(AarflingoTheme.muted)
            Spacer()
            Text(value).fontWeight(.semibold)
        }
        .font(.subheadline)
    }
}

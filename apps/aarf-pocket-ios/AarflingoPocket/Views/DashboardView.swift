import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    IntentHeroCard(prediction: appState.prediction)

                    VStack(alignment: .leading, spacing: 12) {
                        Text("Modality signals")
                            .font(.headline)
                        SignalBar(label: "Vision", value: 0.88)
                        SignalBar(label: "Audio arousal", value: 0.62)
                        SignalBar(label: "ECG stress", value: 0.22)
                        SignalBar(label: "IMU activity", value: 0.74)
                    }
                    .aarflingoCard()

                    VStack(alignment: .leading, spacing: 12) {
                        Text("Feedback metrics")
                            .font(.headline)
                        MetricRow(label: "Predictions logged", value: "\(appState.history.count)")
                        MetricRow(label: "Positive ratings", value: "12")
                        MetricRow(label: "Retrain ready", value: "No")
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

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label).font(.caption).foregroundStyle(AarflingoTheme.muted)
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(AarflingoTheme.border)
                    Capsule()
                        .fill(AarflingoTheme.accent)
                        .frame(width: geo.size.width * value)
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

struct TriadChart: View {
    let counts: [(String, Int)]

    var maxCount: Int { counts.map(\.1).max() ?? 1 }

    var body: some View {
        VStack(spacing: 8) {
            ForEach(counts, id: \.0) { intent, count in
                HStack {
                    Text(intent.capitalized)
                        .font(.caption)
                        .frame(width: 80, alignment: .leading)
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            RoundedRectangle(cornerRadius: 4)
                                .fill(AarflingoTheme.border)
                            RoundedRectangle(cornerRadius: 4)
                                .fill(AarflingoTheme.accent)
                                .frame(width: max(geo.size.width * CGFloat(count) / CGFloat(maxCount), 4))
                        }
                    }
                    .frame(height: 16)
                    Text("\(count)")
                        .font(.caption2.weight(.semibold))
                        .frame(width: 24)
                }
                .foregroundStyle(AarflingoTheme.text)
            }
        }
    }
}

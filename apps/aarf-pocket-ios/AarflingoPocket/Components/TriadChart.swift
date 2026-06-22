import SwiftUI

struct TriadChart: View {
    let counts: [(String, Int)]

    var total: Int { counts.map(\.1).reduce(0, +) }

    var body: some View {
        VStack(spacing: 12) {
            ForEach(Array(counts.enumerated()), id: \.offset) { _, entry in
                let (label, count) = entry
                let fraction = total > 0 ? Double(count) / Double(total) : 0.0
                HStack(spacing: 8) {
                    Text(emoji(for: label))
                        .font(.title3)
                    Text(label.capitalized)
                        .font(.subheadline)
                        .foregroundStyle(AarflingoTheme.text)
                        .frame(width: 80, alignment: .leading)
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule()
                                .fill(AarflingoTheme.border)
                            Capsule()
                                .fill(color(for: label))
                                .frame(width: geo.size.width * fraction)
                                .animation(.easeOut(duration: 0.5), value: fraction)
                        }
                    }
                    .frame(height: 20)
                    Text("\(count)")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(AarflingoTheme.muted)
                        .frame(width: 30)
                }
            }
        }
    }

    func emoji(for intent: String) -> String {
        switch intent {
        case "play": return "🎾"
        case "food": return "🍖"
        case "outside": return "🚪"
        case "rest": return "😴"
        case "avoid": return "⚠️"
        case "attention": return "🐾"
        default: return "🐕"
        }
    }

    func color(for intent: String) -> Color {
        switch intent {
        case "play": return AarflingoTheme.accent
        case "food": return AarflingoTheme.warn
        case "outside": return AarflingoTheme.info
        case "rest": return AarflingoTheme.muted
        case "avoid": return AarflingoTheme.danger
        case "attention": return Color(red: 0.82, green: 0.56, blue: 0.98)
        default: return AarflingoTheme.info
        }
    }
}

struct ConfidenceTrendChart: View {
    let items: [HistoryItem]

    var body: some View {
        let data = Array(items.prefix(20).reversed())
        VStack(spacing: 8) {
            Text("Confidence trend (last \(data.count))")
                .font(.caption.weight(.semibold))
                .foregroundStyle(AarflingoTheme.muted)
                .frame(maxWidth: .infinity, alignment: .leading)
            GeometryReader { geo in
                let w = geo.size.width
                let h = geo.size.height
                let maxVal = 1.0
                let step = data.count > 1 ? w / CGFloat(data.count - 1) : w
                Path { path in
                    guard !data.isEmpty else { return }
                    for i in data.indices {
                        let x = CGFloat(i) * step
                        let y = h - CGFloat(data[i].confidence / maxVal) * h * 0.85 - h * 0.075
                        if i == 0 { path.move(to: CGPoint(x: x, y: y)) }
                        else { path.addLine(to: CGPoint(x: x, y: y)) }
                    }
                }
                .stroke(AarflingoTheme.accent, style: StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round))
            }
            .frame(height: 80)
        }
        .padding(12)
        .background(AarflingoTheme.card)
        .overlay(RoundedRectangle(cornerRadius: 10).stroke(AarflingoTheme.border, lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

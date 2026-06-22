import SwiftUI

struct StatusChip: View {
    let label: String
    let tone: ChipTone

    enum ChipTone { case ok, warn, info, neutral }

    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(background)
                .frame(width: 6, height: 6)
            Text(label)
                .font(.caption.weight(.semibold))
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 5)
        .background(background.opacity(0.12))
        .overlay(Capsule().stroke(background.opacity(0.35), lineWidth: 1))
        .foregroundStyle(foreground)
        .clipShape(Capsule())
    }

    private var background: Color {
        switch tone {
        case .ok: return AarflingoTheme.accent
        case .warn: return AarflingoTheme.warn
        case .info: return AarflingoTheme.info
        case .neutral: return AarflingoTheme.muted
        }
    }

    private var foreground: Color {
        switch tone {
        case .neutral: return AarflingoTheme.muted
        default: return background
        }
    }
}

struct IntentHeroCard: View {
    let prediction: TriadPrediction

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(prediction.intentEmoji)
                    .font(.system(size: 36))
                Spacer()
                ConfidenceRing(confidence: prediction.confidence, gate: prediction.gate)
            }
            Text("CURRENT INTENT")
                .font(.caption.weight(.bold))
                .foregroundStyle(AarflingoTheme.muted)
            Text(prediction.intentLabel)
                .font(.title.bold())
                .foregroundStyle(AarflingoTheme.text)
            Text("\(prediction.emotion) · \(prediction.behavior.replacingOccurrences(of: "_", with: " "))")
                .font(.subheadline)
                .foregroundStyle(AarflingoTheme.muted)
            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 4) {
                    Label(
                        title: { Text("Gate: \(prediction.gate.uppercased())") },
                        icon: {
                            Image(systemName: prediction.gate == "pass" ? "checkmark.shield.fill" : "exclamationmark.shield.fill")
                        }
                    )
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(gateColor)
                    Label("Dog detected: \(prediction.dogPresent ? "yes" : "no")", systemImage: "pawprint.fill")
                        .font(.caption)
                        .foregroundStyle(AarflingoTheme.muted)
                }
                Spacer()
            }
        }
        .aarflingoCard()
    }

    private var gateColor: Color {
        switch prediction.gate {
        case "pass": return AarflingoTheme.accent
        case "reject": return AarflingoTheme.danger
        default: return AarflingoTheme.warn
        }
    }
}

struct ConfidenceRing: View {
    let confidence: Double
    let gate: String

    var body: some View {
        ZStack {
            Circle()
                .stroke(AarflingoTheme.border, lineWidth: 6)
            Circle()
                .trim(from: 0, to: confidence)
                .stroke(ringColor, style: StrokeStyle(lineWidth: 6, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeInOut(duration: 0.6), value: confidence)
            VStack(spacing: -2) {
                Text("\(Int(confidence * 100))")
                    .font(.headline.bold())
                    .foregroundStyle(AarflingoTheme.text)
                Text("%")
                    .font(.system(size: 10).bold())
                    .foregroundStyle(AarflingoTheme.muted)
            }
        }
        .frame(width: 72, height: 72)
    }

    private var ringColor: Color {
        gate == "pass" ? AarflingoTheme.accent : AarflingoTheme.warn
    }
}

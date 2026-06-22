import Foundation
import SwiftUI

@MainActor
final class AppState: ObservableObject {
    @Published var runtimeURL: String {
        didSet { UserDefaults.standard.set(runtimeURL, forKey: "runtimeURL") }
    }
    @Published var connected = false
    @Published var prediction: TriadPrediction = .demo
    @Published var history: [HistoryItem] = HistoryItem.samples
    @Published var liveOn = false

    init() {
        runtimeURL = UserDefaults.standard.string(forKey: "runtimeURL") ?? "http://127.0.0.1:8765"
    }

    func refreshMock() {
        connected = true
        prediction = TriadPrediction.randomDemo()
        history.insert(
            HistoryItem(
                id: UUID(),
                intent: prediction.intent,
                emotion: prediction.emotion,
                behavior: prediction.behavior,
                confidence: prediction.confidence,
                timestamp: Date()
            ),
            at: 0
        )
        if history.count > 50 { history.removeLast() }
    }

    func clearHistory() {
        history.removeAll()
    }
}

struct TriadPrediction: Identifiable, Equatable {
    let id = UUID()
    let intent: String
    let emotion: String
    let behavior: String
    let confidence: Double
    let gate: String
    let dogPresent: Bool

    static let demo = TriadPrediction(
        intent: "play",
        emotion: "excited",
        behavior: "play_bow",
        confidence: 0.91,
        gate: "pass",
        dogPresent: true
    )

    static func randomDemo() -> TriadPrediction {
        let intents = [
            ("play", "excited", "play_bow", 0.92),
            ("food", "content", "sniff_ground", 0.84),
            ("outside", "anxious", "freeze", 0.78),
            ("rest", "calm", "yawning", 0.71),
            ("avoid", "fearful", "cowering", 0.64),
            ("attention", "happy", "paw_raise", 0.87),
        ]
        let pick = intents.randomElement()!
        return TriadPrediction(
            intent: pick.0,
            emotion: pick.1,
            behavior: pick.2,
            confidence: pick.3,
            gate: pick.3 > 0.8 ? "pass" : "review",
            dogPresent: true
        )
    }

    var intentLabel: String {
        switch intent {
        case "play": return "Wants to play"
        case "food": return "Wants food"
        case "outside": return "Wants outside"
        case "rest": return "Resting"
        case "avoid": return "Needs space"
        case "attention": return "Seeks attention"
        default: return intent.capitalized
        }
    }

    var intentEmoji: String {
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

    var emotionEmoji: String {
        switch emotion {
        case "excited": return "🤩"
        case "content": return "😊"
        case "anxious": return "😰"
        case "calm": return "😌"
        case "fearful": return "😨"
        case "happy": return "🐶"
        default: return "❓"
        }
    }
}

struct HistoryItem: Identifiable {
    let id: UUID
    let intent: String
    let emotion: String
    let behavior: String
    let confidence: Double
    let timestamp: Date

    var intentEmoji: String {
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

    static let samples: [HistoryItem] = [
        HistoryItem(id: UUID(), intent: "play", emotion: "excited", behavior: "play_bow", confidence: 0.89, timestamp: Date().addingTimeInterval(-120)),
        HistoryItem(id: UUID(), intent: "food", emotion: "content", behavior: "sniff_ground", confidence: 0.76, timestamp: Date().addingTimeInterval(-600)),
        HistoryItem(id: UUID(), intent: "rest", emotion: "calm", behavior: "yawning", confidence: 0.93, timestamp: Date().addingTimeInterval(-1800)),
        HistoryItem(id: UUID(), intent: "outside", emotion: "anxious", behavior: "freeze", confidence: 0.68, timestamp: Date().addingTimeInterval(-3600)),
        HistoryItem(id: UUID(), intent: "play", emotion: "excited", behavior: "play_bow", confidence: 0.95, timestamp: Date().addingTimeInterval(-7200)),
        HistoryItem(id: UUID(), intent: "attention", emotion: "happy", behavior: "paw_raise", confidence: 0.82, timestamp: Date().addingTimeInterval(-14400)),
    ]
}

import Foundation

@MainActor
final class IntentViewModel: ObservableObject {
    @Published var intent: String = "rest"
    @Published var emotion: String = "calm"
    @Published var behavior: String = "yawning"
    @Published var confidence: Double = 0.55
    @Published var gateStatus: String = "review"

    private let coreML = CoreMLService()

    func runInference() {
        let result = coreML.predict(features: ["gaze_aversion": 0.2, "motion": 0.8])
        intent = result.intent
        emotion = result.emotion
        behavior = result.behavior
        confidence = result.confidence
        gateStatus = confidence >= 0.5 ? "pass" : "review"
    }
}

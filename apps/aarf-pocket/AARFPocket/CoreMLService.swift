import Foundation

struct TriadResult {
    let intent: String
    let emotion: String
    let behavior: String
    let confidence: Double
}

struct CoreMLService {
    func predict(features: [String: Double]) -> TriadResult {
        let motion = features["motion"] ?? 0
        if motion > 0.5 {
            return TriadResult(intent: "solicit_play", emotion: "excited", behavior: "play_bow", confidence: 0.82)
        }
        return TriadResult(intent: "rest", emotion: "calm", behavior: "yawning", confidence: 0.58)
    }
}

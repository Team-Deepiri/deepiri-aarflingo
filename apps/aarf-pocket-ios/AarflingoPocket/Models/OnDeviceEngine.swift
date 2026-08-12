import CoreML
import Foundation
import UIKit

/// On-device TriadNet inference — cuts WiFi dependence.
///
/// Loads the bundled `Triad.mlpackage` (CoreML, iOS 16+) produced by
/// `aarflingo-bridge export --target coreml` via
/// `scripts/mobile/bundle-mobile-models.sh`. Runs the same TriadNet the runtime
/// uses on a rolling 15-frame × 43-dim feature window.
///
/// The phone estimates what it can from camera frames (brightness, contrast,
/// motion, aspect ratio, dog-presence heuristic); the rest of each feature row
/// stays zero, matching the runtime's cold-start padding.
///
/// When the model isn't bundled (debug / first run), `available` is false and
/// the app keeps using the runtime over WiFi.
final class OnDeviceEngine {

    struct Constants {
        static let featureDim = 43
        static let sequenceLen = 15
        static let modelName = "Triad"
    }

    /// argmax index → label. Read from the bundled labels JSON when present,
    /// otherwise falls back to the same defaults as the Android engine.
    private var intents: [String] = ["rest", "attention", "avoid", "outside", "play", "food"]
    private var emotions: [String] = ["calm", "happy", "fearful", "excited", "content", "anxious"]
    private var behaviors: [String] = ["resting", "paw_raise", "cowering", "freeze", "play_bow", "sniff_ground"]

    private var model: MLModel?
    private var window: [[Float]] = []
    private var lastGray: [Float]?

    /// True when the bundled CoreML model is present and ready to run.
    var available: Bool { model != nil }

    init() {
        loadLabels()
        loadModel()
    }

    // MARK: – Model + labels loading

    private func loadLabels() {
        guard let url = Bundle.main.url(forResource: "triad_labels", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: [String]] else {
            return
        }
        if let i = json["intents"], !i.isEmpty { intents = i }
        if let e = json["emotions"], !e.isEmpty { emotions = e }
        if let b = json["behaviors"], !b.isEmpty { behaviors = b }
    }

    private func loadModel() {
        // Prefer compiled model; fall back to the raw mlpackage path.
        let candidates = [
            Bundle.main.url(forResource: "Triad", withExtension: "mlmodelc"),
            Bundle.main.url(forResource: "Triad", withExtension: "mlpackage"),
        ]
        for url in candidates.compactMap({ $0 }) {
            if let m = try? MLModel(contentsOf: url) {
                model = m
                return
            }
        }
    }

    // MARK: – Inference

    /// Push one camera-derived frame and run the model when the window fills.
    func pushAndPredict(frame: OnDeviceFrame) -> TriadPrediction? {
        guard let model else { return nil }

        window.append(frame.toFeatures())
        if window.count > Constants.sequenceLen {
            window.removeFirst()
        }

        var input = [Float](repeating: 0, count: Constants.featureDim * Constants.sequenceLen)
        let startPad = Constants.sequenceLen - window.count
        for (i, row) in window.enumerated() {
            let base = (startPad + i) * Constants.featureDim
            for j in 0..<Constants.featureDim where j < row.count {
                input[base + j] = row[j]
            }
        }

        do {
            let shape = [NSNumber(value: 1), NSNumber(value: Constants.featureDim * Constants.sequenceLen)]
            let arr = try MLMultiArray(shape: shape, dataType: .float32)
            let buf = arr.dataPointer.bindMemory(to: Float.self, capacity: input.count)
            for (i, v) in input.enumerated() { buf[i] = v }

            let prediction = try model.prediction(from: TriadInput(input: arr))
            guard let iProbs = prediction.featureValue(for: "intent_probs")?.multiArrayValue,
                  let eProbs = prediction.featureValue(for: "emotion_probs")?.multiArrayValue,
                  let bProbs = prediction.featureValue(for: "behavior_probs")?.multiArrayValue else {
                return nil
            }

            let ii = argmax(iProbs)
            let ei = argmax(eProbs)
            let bi = argmax(bProbs)
            let conf = (iProbs[ii].floatValue + eProbs[ei].floatValue + bProbs[bi].floatValue) / 3.0
            let gate: String = conf >= 0.7 ? "pass" : (conf <= 0.45 ? "reject" : "review")

            return TriadPrediction(
                intent: intents.indices.contains(ii) ? intents[ii] : "unknown",
                emotion: emotions.indices.contains(ei) ? emotions[ei] : "unknown",
                behavior: behaviors.indices.contains(bi) ? behaviors[bi] : "unknown",
                confidence: Double(conf),
                gate: gate,
                dogPresent: frame.dogPresent > 0.5,
            )
        } catch {
            return nil
        }
    }

    private func argmax(_ a: MLMultiArray) -> Int {
        var best = 0
        var bestVal = a[0].floatValue
        for i in 1..<a.count {
            let v = a[i].floatValue
            if v > bestVal { bestVal = v; best = i }
        }
        return best
    }
}

/// A single on-device camera frame with the features the phone can estimate.
struct OnDeviceFrame {
    let brightness: Float
    let contrast: Float
    let motion: Float
    let width: Int
    let height: Int
    let dogPresent: Float

    func toFeatures() -> [Float] {
        var f = [Float](repeating: 0, count: OnDeviceEngine.Constants.featureDim)
        f[0] = dogPresent              // dog_present
        f[5] = min(max(motion, 0), 1)  // motion
        f[16] = min(max(brightness, 0), 1)
        f[17] = min(max(contrast, 0), 1)
        f[18] = height > 0 ? Float(width) / Float(height) : 1  // aspect_ratio
        return f
    }

    /// Build from a UIImage: grayscale stats + frame diff.
    static func from(image: UIImage, prevGray: inout [Float]?) -> OnDeviceFrame {
        guard let cg = image.cgImage else {
            return OnDeviceFrame(brightness: 0, contrast: 0, motion: 0, width: 1, height: 1, dogPresent: 0)
        }
        let w = cg.width
        let h = cg.height
        var pixels = [UInt8](repeating: 0, count: w * h)
        guard let ctx = CGContext(
            data: &pixels, width: w, height: h, bitsPerComponent: 8,
            bytesPerRow: w, space: CGColorSpaceCreateDeviceGray(),
            bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else {
            return OnDeviceFrame(brightness: 0, contrast: 0, motion: 0, width: w, height: h, dogPresent: 0)
        }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))

        var sum: Double = 0
        for p in pixels { sum += Double(p) }
        let mean = Float(sum / Double(pixels.count)) / 255.0

        var variance: Double = 0
        var diff: Float = 0
        if let prev = prevGray {
            for i in 0..<pixels.count {
                let d = Double(pixels[i]) / 255.0 - Double(mean)
                variance += d * d
                diff += abs(prev[i] - Float(pixels[i]) / 255.0)
            }
        } else {
            for i in 0..<pixels.count {
                let d = Double(pixels[i]) / 255.0 - Double(mean)
                variance += d * d
            }
        }
        prevGray = pixels.map { Float($0) / 255.0 }

        let contrast = Float(sqrt(variance / Double(pixels.count)))
        let motion = prevGray == nil ? 0 : diff / Float(pixels.count)
        let dogPresent: Float = motion > 0.04 ? 1 : 0
        return OnDeviceFrame(
            brightness: mean,
            contrast: min(max(contrast * 3, 0), 1),
            motion: motion,
            width: w,
            height: h,
            dogPresent: dogPresent
        )
    }
}

// MARK: – CoreML generated feature provider

/// Feature provider for the bundled `Triad` model (input: `input`).
private class TriadInput: MLFeatureProvider {
    let input: MLMultiArray

    init(input: MLMultiArray) {
        self.input = input
    }

    var featureNames: Set<String> { ["input"] }

    func featureValue(for featureName: String) -> MLFeatureValue? {
        guard featureName == "input" else { return nil }
        return MLFeatureValue(multiArray: input)
    }
}
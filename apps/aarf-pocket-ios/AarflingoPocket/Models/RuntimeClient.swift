import Foundation
import Combine

// MARK: - Models

struct RuntimePrediction: Decodable, Identifiable {
    let id = UUID()
    let intent: String
    let emotion: String
    let behavior: String
    let confidence: Double
    let gate: String
    let dogPresent: Bool
    let tsMsRaw: Int?

    var tsMs: Int { tsMsRaw ?? 0 }

    enum CodingKeys: String, CodingKey {
        case intent, emotion, behavior, confidence, gate
        case dogPresent = "dog_present"
        case tsMsRaw = "ts_ms"
    }
}

// MARK: - RuntimeClient

/// Connects to the Aarflingo FastAPI runtime.
///
/// - POST /infer/frame  (JPEG upload → prediction JSON)
/// - WS   /ws/live      (streaming predictions)
@MainActor
final class RuntimeClient: ObservableObject {

    @Published var prediction: RuntimePrediction? = nil
    @Published var connected: Bool = false
    @Published var lastError: String? = nil

    private var wsTask: URLSessionWebSocketTask?
    private var session = URLSession.shared
    private var baseURL: URL

    init(baseURL: URL) {
        self.baseURL = baseURL
    }

    // MARK: – WebSocket

    func connect() {
        let wsURL = baseURL
            .absoluteString
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
        guard let url = URL(string: wsURL + "/ws/live") else { return }

        wsTask?.cancel(with: .goingAway, reason: nil)
        let task = session.webSocketTask(with: url)
        wsTask = task
        task.resume()
        connected = true
        lastError = nil
        receive()
    }

    func disconnect() {
        wsTask?.cancel(with: .goingAway, reason: nil)
        wsTask = nil
        connected = false
    }

    private func receive() {
        wsTask?.receive { [weak self] result in
            guard let self else { return }
            switch result {
            case .success(let msg):
                if case .string(let text) = msg,
                   let data = text.data(using: .utf8),
                   let pred = try? JSONDecoder().decode(RuntimePrediction.self, from: data),
                   pred.intent != "" {
                    Task { @MainActor in
                        self.prediction = pred
                        self.connected = true
                    }
                }
                self.receive() // keep loop alive
            case .failure(let err):
                Task { @MainActor in
                    self.connected = false
                    self.lastError = err.localizedDescription
                }
            }
        }
    }

    func sendPing() {
        wsTask?.sendPing { _ in }
    }

    // MARK: – Frame upload

    /// Upload a JPEG frame and return the prediction. Non-throwing — returns nil on error.
    func inferFrame(_ jpeg: Data) async -> RuntimePrediction? {
        let url = baseURL.appendingPathComponent("infer/frame")
        var req = URLRequest(url: url, timeoutInterval: 4)
        req.httpMethod = "POST"
        let boundary = "AARFBoundary\(UInt64.random(in: 0..<UInt64.max))"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"frame.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(jpeg)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        req.httpBody = body

        do {
            let (data, resp) = try await session.data(for: req)
            guard (resp as? HTTPURLResponse)?.statusCode == 200 else { return nil }
            let pred = try JSONDecoder().decode(RuntimePrediction.self, from: data)
            await MainActor.run {
                self.prediction = pred
                self.connected = true
            }
            return pred
        } catch {
            return nil
        }
    }

    // MARK: – Health check

    func checkHealth() async -> Bool {
        let url = baseURL.appendingPathComponent("health")
        do {
            let (data, _) = try await session.data(from: url)
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               json["ok"] as? Bool == true {
                await MainActor.run { self.connected = true }
                return true
            }
        } catch {}
        await MainActor.run { self.connected = false }
        return false
    }
}

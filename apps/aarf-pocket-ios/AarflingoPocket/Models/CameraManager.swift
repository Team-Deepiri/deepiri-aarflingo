import AVFoundation
import CoreImage
import UIKit

/// Wraps `AVCaptureSession` and delivers compressed JPEG frames via a callback.
///
/// Usage:
/// ```swift
/// let cam = CameraManager()
/// cam.onFrame = { jpeg in
///     await client.inferFrame(jpeg)
/// }
/// cam.start()
/// ```
final class CameraManager: NSObject, ObservableObject {

    @Published var isRunning = false
    @Published var permissionDenied = false

    /// Called on a background queue with each compressed JPEG (~640×480, Q70).
    var onFrame: ((Data) async -> Void)?

    let session = AVCaptureSession()   // public — used by CameraPreviewView
    private let output  = AVCaptureVideoDataOutput()
    private let queue   = DispatchQueue(label: "dev.deepiri.aarflingo.camera", qos: .userInitiated)

    /// Frames-per-second cap — 5 fps is enough for TriadNet; avoids flooding the runtime.
    private var fpsCap: Double = 5.0
    private var lastFrameTime: CFTimeInterval = 0

    // MARK: – Public API

    func start(fps: Double = 5.0) {
        fpsCap = fps
        Task.detached { [weak self] in await self?.setUp() }
    }

    func stop() {
        session.stopRunning()
        DispatchQueue.main.async { self.isRunning = false }
    }

    func flip() {
        guard let currentInput = session.inputs.first as? AVCaptureDeviceInput else { return }
        let nextPosition: AVCaptureDevice.Position = currentInput.device.position == .back ? .front : .back
        guard let nextDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: nextPosition),
              let nextInput = try? AVCaptureDeviceInput(device: nextDevice) else { return }
        session.beginConfiguration()
        session.removeInput(currentInput)
        if session.canAddInput(nextInput) { session.addInput(nextInput) }
        session.commitConfiguration()
    }

    // MARK: – Private

    private func setUp() async {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        if status == .notDetermined {
            await AVCaptureDevice.requestAccess(for: .video)
        }
        guard AVCaptureDevice.authorizationStatus(for: .video) == .authorized else {
            DispatchQueue.main.async { self.permissionDenied = true }
            return
        }

        session.beginConfiguration()
        session.sessionPreset = .vga640x480

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let input  = try? AVCaptureDeviceInput(device: device) else {
            session.commitConfiguration(); return
        }

        if session.canAddInput(input)  { session.addInput(input) }

        output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
        output.alwaysDiscardsLateVideoFrames = true
        output.setSampleBufferDelegate(self, queue: queue)
        if session.canAddOutput(output) { session.addOutput(output) }

        // Portrait orientation
        if let conn = output.connection(with: .video) {
            if #available(iOS 17.0, *) {
                if conn.isVideoRotationAngleSupported(90) {
                    conn.videoRotationAngle = 90
                }
            }
        }

        session.commitConfiguration()
        session.startRunning()
        DispatchQueue.main.async { self.isRunning = true }
    }
}

// MARK: – AVCaptureVideoDataOutputSampleBufferDelegate

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {

    func captureOutput(_ output: AVCaptureOutput,
                       didOutput sampleBuffer: CMSampleBuffer,
                       from connection: AVCaptureConnection) {
        let now = CACurrentMediaTime()
        guard now - lastFrameTime >= 1.0 / fpsCap else { return }
        lastFrameTime = now

        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext()
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else { return }
        let uiImage = UIImage(cgImage: cgImage)
        guard let jpeg = uiImage.jpegData(compressionQuality: 0.7) else { return }

        let cb = onFrame
        Task { await cb?(jpeg) }
    }
}

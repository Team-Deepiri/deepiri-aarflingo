# AARFLingo Roadmap

## Now (v0.1)

- Webcam live inference via `services/runtime` + AARF Studio browser UI
- OpenCV motion dog detect + 20-dim feature vector + TriadNet forecast
- SQLite feedback store + one-click retrain hook
- Jetson edge-runtime CLI + Docker deploy path

## Next

- Real pose keypoints (MediaPipe / YOLO-pose) replacing bbox proxies
- Collar IMU + mic fusion with vision triad
- Active learning: surface low-confidence frames for human label
- ONNX → TensorRT on Jetson with INT8 calibration

## Later

- Multi-dog household disambiguation
- Federated ethogram updates per breed / individual
- On-device vocalization policy engine (AARF gate + TTS)

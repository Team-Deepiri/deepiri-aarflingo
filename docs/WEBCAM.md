# Webcam live paths for Aarflingo

## Recommended: WSL dev (Windows bridge)

WSL cannot see USB webcams directly. Pattern from `lighthouse-avionics-video-processing`:

### 1. Start bridge on **Windows** (PowerShell)

```powershell
cd \\wsl$\Ubuntu\home\<you>\projects\Deepiri\deepiri-aarflingo
.\scripts\webcam\start_webcam_bridge.ps1
```

Stream: `http://localhost:8766/video/stream`

### 2. Start runtime in WSL

```bash
./scripts/run_runtime.sh
```

Runtime auto-detects WSL and uses `http://<windows-host>:8766/video/stream` for server capture.

### 3. Open studio

```bash
./setup.sh --run
# or
cd apps/aarf-studio && npm run electron:dev
```

In **Live camera** → choose **WSL bridge** → **Start**.

The UI displays the MJPEG stream and POSTs frames to `/infer/frame` for predictions.

## Browser camera (native Linux / macOS / Windows host)

Choose **Browser cam** — uses `getUserMedia` in Electron or Chrome. Electron grants media permissions automatically.

## Server OpenCV (runtime pulls frames)

Choose **Server OpenCV** — runtime reads the bridge URL (WSL) or `/dev/video0` (Linux).

```bash
curl -X POST http://127.0.0.1:8765/live/start \
  -H 'Content-Type: application/json' \
  -d '{"camera":0,"mode":"server"}'
```

## Probe endpoints

```bash
curl http://127.0.0.1:8765/bridge/info
curl http://127.0.0.1:8766/health   # bridge on Windows host
cd services/ingest && poetry run aarflingo-ingest webcam-probe --camera 0
```

## Calibrate gaze zones

Edit [`infra/configs/zones.default.yaml`](../infra/configs/zones.default.yaml) for door / toy / bowl regions in your room.

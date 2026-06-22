# Webcam live inference

## 1. Start runtime

```bash
./scripts/run_runtime.sh
# → http://127.0.0.1:8765/health
```

## 2. Studio (browser camera → server inference)

```bash
cd apps/aarf-studio && cp .env.example .env && npm run dev
```

Open **Camera** → **Start webcam + runtime**. The browser captures frames and POSTs them to `/infer/frame`; predictions stream on `WS /ws/live`.

## 3. Server-side OpenCV webcam

```bash
curl -X POST http://127.0.0.1:8765/live/start -H 'Content-Type: application/json' -d '{"camera":0}'
```

Useful when the runtime runs on the same machine as a USB camera (collar dev kit, Jetson).

## 4. Feedback loop

- **Correct / Wrong** buttons → `POST /feedback`
- **Fix: outside|play|food** → stores corrected label for retrain
- **Retrain**: `POST /live/retrain` or CLI export + `aarflingo-forecast train --feedback ...`

## 5. Calibrate zones

Edit [`infra/configs/zones.default.yaml`](../infra/configs/zones.default.yaml) so `door`, `toy`, and `bowl` rectangles match where those objects appear in your camera frame (normalized 0–1).

## 6. Probe camera

```bash
cd services/ingest && poetry run aarflingo-ingest webcam-probe --camera 0
```

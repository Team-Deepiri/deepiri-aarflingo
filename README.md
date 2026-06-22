# Aarflingo

<img src="assets/branding/Aarflingo-logo.png" alt="Aarflingo" width="420" />

**Deepiri's Aarflingo** — proactive canine intent forecasting: webcam → perception → triad model → feedback → retrain → edge deploy.

## Quick start (webcam)

```bash
./setup.sh --run        # install + train + Electron studio
./scripts/run_runtime.sh
```

**WSL:** USB cameras need the Windows MJPEG bridge (lighthouse pattern):

```powershell
# Windows PowerShell
.\scripts\webcam\start_webcam_bridge.ps1
```

Then in studio → **Live camera** → **WSL bridge** → **Start**. See [docs/WEBCAM.md](docs/WEBCAM.md).

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md), [docs/ELECTRON.md](docs/ELECTRON.md), and [docs/ROADMAP.md](docs/ROADMAP.md).

## Architecture

| Path | Role |
|------|------|
| `ethogram/` | Intent / emotion / behavior taxonomy + coupling matrix |
| `core/feature_spec.py` | 28-dim perception + modality vector layout |
| `lib/aarf-physio` | ECG/IMU vitals encoder (PhysioZoo-shaped) |
| `services/audio` | Bark / arousal-valence vocal encoder |
| `services/perception` | OpenCV + YOLO dog detect, gaze zones, scene |
| `services/forecast` | PyTorch TriadNet (BiLSTM-style MLP), train + infer |
| `services/feedback` | SQLite prediction log + human corrections |
| `services/runtime` | FastAPI + WebSocket live webcam inference |
| `services/edge-runtime` | Jetson / collar loop (ONNX optional) |
| `services/artifact-bridge` | ONNX export for studio + hardware |
| `apps/aarf-studio` | Live camera UI + feedback buttons |
| `apps/aarf-pocket-ios` | SwiftUI pocket app (UI shell, iOS 16+) |
| `apps/aarf-pocket-android` | Kotlin Compose pocket app (UI shell) |
| `infra/docker/` | `runtime.Dockerfile` + `jetson.Dockerfile` |

## API (runtime)

- `GET /health` — status
- `POST /live/start` — OpenCV webcam on server (`{"camera":0}`)
- `POST /infer/frame` — JPEG upload → prediction (browser camera path)
- `POST /feedback` — rate / correct a prediction
- `POST /live/retrain` — export feedback → fine-tune checkpoint
- `WS /ws/live` — streaming predictions

## Hardware deploy

```bash
# x86/ARM runtime container (USB webcam)
docker compose -f infra/docker/docker-compose.yml up aarf-runtime

# Jetson (L4T base image — build on device or with buildx)
docker build -f infra/docker/jetson.Dockerfile -t aarflingo-edge .
poetry run aarflingo-edge run --camera 0
```

Calibrate gaze zones for your home: edit `infra/configs/zones.default.yaml` (door / toy / bowl regions).

## Training & retrain

Multimodal pipeline: **YOLO vision** + **vocal encoder** + **ECG/IMU vitals** → **TriadNet** fusion.

```bash
./scripts/train_aarflingo.sh         # all stages (downloads YOLOv8n on first run)
SKIP_VISION=1 ./scripts/train_aarflingo.sh   # audio + physio + triad only
./scripts/verify_aarflingo.sh        # tests + train + runtime API + studio build
make train
make verify
```

Public dataset catalog: [docs/DATASETS.md](docs/DATASETS.md) (PhysioZoo, DogSpeak, Barkopedia, Mendeley IMU)

Math reference: [docs/MATH.md](docs/MATH.md) · notebooks: [notebooks/](notebooks/)

From human feedback export:

```bash
poetry run aarflingo-feedback export --out artifacts/feedback/export.json
poetry run aarflingo-forecast train --feedback artifacts/feedback/export.json
```

## Mobile (pocket apps)

Native shells for on-the-go monitoring — **UI-only in v0.1** (mock predictions; ML hooks later).

| App | Stack | Docs |
|-----|-------|------|
| iOS | SwiftUI | [apps/aarf-pocket-ios/README.md](apps/aarf-pocket-ios/README.md) |
| Android | Kotlin + Compose | [apps/aarf-pocket-android/README.md](apps/aarf-pocket-android/README.md) |

```bash
make mobile-android    # WSL: build debug APK
make mobile-verify     # Android build + iOS source check
./scripts/mobile/run-android-app.sh   # emulator + install
```

iOS Simulator requires **macOS**; CI builds both on `.github/workflows/mobile.yml`.

## License

Apache-2.0 — see [LICENSE](LICENSE).

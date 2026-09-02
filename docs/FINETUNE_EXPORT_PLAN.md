# Aarflingo — Model Finetuning & Export Initiation Plan

**Date**: 2026-09-02
**Status**: READY TO EXECUTE
**Owner**: Deepiri ML Engineering (Aarflingo / canine intent forecasting)

---

## Goal

Aarflingo predicts what a dog is about to do (outside, play, food, avoid, rest) by fusing vision, audio, ECG/IMU, and gating against an ethogram. Today only the **TriadNet fusion head** is trained/exported; the **audio, vitals, and vision encoders are untrained/not wired**. This plan:

1. **Trains** all missing encoders (VocalEncoder, VitalsEncoder, YOLO) — moving from synthetic-only to real data.
2. **Finetunes on real data** (Barkopedia barks, your dog's clips, dog ECG) to replace trivial synthetic triads.
3. **Exports** every model to ONNX (+ real CoreML for iOS) for edge deployment.
4. **Wires the live multimodal encoders** into the runtime so the modality bars are real, not zeros.

---

## Current State

| Model | Artifact | State |
|-------|----------|-------|
| **TriadNet** (intent×emotion×behavior) | `artifacts/models/default/triad.pt` + `triad.onnx` | Trained + exported, but **100% val acc on synthetic** (6 epochs, trivial) |
| **VocalEncoder** (arousal/valence) | `vocal.pt` — **MISSING** | Code exists, **not trained**, **not wired** into runtime |
| **VitalsEncoder** (stress/HR) | `vitals.pt` — **MISSING** | Code exists, **not trained**, **not wired** |
| **Vision / YOLOv8n** (dog detect) | `yolov8n.pt` / `dog_yolo.onnx` — **MISSING** | Uses stock COCO weights; **no fine-tune**, **no export** |
| **CoreML export** (iOS) | — | Placeholder only (writes JSON, no real `.mlmodel`) |
| **Runtime modality wiring** | `services/runtime/app/engine.py` | Audio/ECG/IMU bars show **zeros** — encoders not loaded |

### Known problems

- `train_metrics.json` shows `best_val_acc: 1.0` by epoch 6 — synthetic data is well-separated; **doesn't reflect real performance**.
- `artifacts/models/default/` only has `triad.pt` — the `train_aarflingo.sh` stages for vision/audio/physio are present but their outputs are **missing**.
- The runtime `engine.py` loads perception + forecast + feedback + voice but **not** VocalEncoder or VitalsEncoder → modality bars static at inference.
- ROADMAP v0.3 explicitly lists: wire live encoders, Barkopedia data, YOLO-on-your-dog, real CoreML.

---

## Execution Plan

### Phase 1 — Train the Missing Encoders

**Goal**: produce `vocal.pt`, `vitals.pt`, and vision artifacts.

- [ ] **1.1** Run the full orchestrated pipeline (all stages):
  ```bash
  ./scripts/train_aarflingo.sh   # vision → audio → physio → triad → export
  ```
- [ ] **1.2** **VocalEncoder** (`aarflingo-audio train`): synthetic DogSpeak/Barkopedia-shaped barks; produce `vocal.pt`.
- [ ] **1.3** **VitalsEncoder** (`aarf-physio train`): PhysioZoo/Mendeley-shaped ECG/IMU; produce `vitals.pt`.
- [ ] **1.4** **Vision** (`aarflingo-perception prepare-vision`): download `yolov8n.pt`, export `dog_yolo.onnx`.
- [ ] **1.5** Verify **triad** re-trains fusing all modalities (not just the vision-only vector it saw before).
- [ ] **1.6** Confirm ONNX exports for triad + vocal + vitals exist with manifests.

### Phase 2 — Finetune on Real Data

**Goal**: replace trivial synthetic models with ones that generalize to the real dog.

- [ ] **2.1** **Barkopedia** (`./scripts/fetch_public_datasets.sh --barkopedia`): wire real bark clips into `services/audio/app/train.py`, retrain `vocal.pt`.
- [ ] **2.2** **YOLO on your dog**: label home clips from `services/ingest`, fine-tune `yolov8n` (`services/perception/app/vision_train.py`), export updated `dog_yolo.onnx`.
- [ ] **2.3** **Dog ECG / HRV** (optional): PhysioZoo real HRV labels for `lib/aarf-physio`.
- [ ] **2.4** **TriadNet**: retrain with real labeled intents via the `services/labeler` + `services/feedback` loop (human corrections as supervision).
- [ ] **2.5** Maintain a **validation split** and gate each encoder on real-data metrics (not 100%-on-synthetic).

### Phase 3 — Export & Validate All Models

**Goal**: portable, edge-deployable artifacts.

- [ ] **3.1** **ONNX**: export triad (done), plus **vocal** + **vitals** encoders to `artifacts/bundles/default/studio/`.
- [ ] **3.2** **Fix CoreML export** (`services/artifact-bridge/app/export_coreml.py`): use `coremltools` to produce a real `.mlmodel`/`.mlpackage` for iOS on-device inference (currently JSON placeholder).
- [ ] **3.3** **Round-trip validation**: load each ONNX via ONNX Runtime, compare outputs to PyTorch within tolerance.
- [ ] **3.4** **Edge runtime check**: `services/edge-runtime/app/loop.py` runs triad ONNX on Jetson/collar — add vocal/vitals ONNX inputs.
- [ ] **3.5** Update every bundle manifest with model version + calibration metadata.

### Phase 4 — Wire Live Multimodal Encoders into Runtime

**Goal**: modality bars and predictions reflect real live signals.

- [ ] **4.1** In `services/runtime/app/engine.py::process_frame()`:
  - Load `vocal.pt`; feed mic audio chunks (`MicListener`) → MFCC → VocalEncoder → `audio_arousal/valence/bark_prob`.
  - Load `vitals.pt` when BLE/IMU connected (stub with simulated 6-DoF first) → `ecg/hr/imu` features.
- [ ] **4.2** Merge encoder outputs into `core/modality_spec` feature dims **before** the TriadNet call.
- [ ] **4.3** Verify the studio modality bars (Audio arousal, ECG stress, IMU activity) move with live input.
- [ ] **4.4** A/B: prediction with vs without audio/vitals to quantify modality contribution.

### Phase 5 — Integration & Deployment

**Goal**: prove the full multimodal pipeline end-to-end.

- [ ] **5.1** Run `make verify` / verification script with all four models loaded.
- [ ] **5.2** Live demo: webcam + mic + (simulated) vitals → intent forecast gated by ethogram.
- [ ] **5.3** Deploy via `infra/` docker-compose (runtime + Jetson edge).
- [ ] **5.4** Optional: TensorRT INT8 calibration on Jetson for edge (ROADMAP v0.4).

---

## Key Commands

```bash
# 1. Train all encoders + triad + export
./scripts/train_aarflingo.sh

#   or stage-by-stage
STAGES=audio,physio ./scripts/train_aarflingo.sh
STAGES=triad     ./scripts/train_aarflingo.sh

# 2. Fetch real datasets + retrain audio on Barkopedia
./scripts/fetch_public_datasets.sh --barkopedia
poetry run aarflingo-audio train --epochs 60 --data path/to/barkopedia

# 3. Fine-tune dog YOLO and export
poetry run aarflingo-perception prepare-vision --data labeled_home_clips

# 4. Export vocal/vitals/vitals ONNX + CoreML
poetry run aarflingo-export onnx --models triad,vocal,vitals
poetry run aarflingo-export coreml --models triad

# 5. Verify
make verify
```

---

## Data Flow

```
home clips ─▶ labeler ─▶ human feedback ─▶ supervised intents
Barkopedia ─▶ vocal encoder finetune ─▶ vocal.pt ─▶ ONNX
PhysioZoo  ─▶ vitals encoder train    ─▶ vitals.pt ─▶ ONNX
your dog   ─▶ YOLO finetune           ─▶ dog_yolo.onnx
              │
              └─▶ fused into TriadNet ─▶ triad.onnx ─▶ edge runtime (Jetson/collar)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Synthetic-only models overfit | Phase 2 finetune on Barkopedia + labeled home clips |
| Runtime modality bars zero | Phase 4 wire + verify live signal |
| CoreML placeholder | Phase 3 use `coremltools` for real iOS artifact |
| Missing `vocal/vitals.pt` blocks fusing | Phase 1 train first; gate triad on them |
| Labeling cost | Semi-supervised `services/labeler` + human-correction loop |
| Edge latency | ONNX + optional TensorRT INT8 calibration |

---

## Success Criteria

1. `vocal.pt`, `vitals.pt`, `yolov8n.pt`/`dog_yolo.onnx` all produced.
2. TriadNet re-trained and exported fused on **all** modalities (not vision-only).
3. Real-data finetuning improves metrics on a held-out split (documented delta vs synthetic).
4. All encoders exported to ONNX + round-trip validated; real CoreML for iOS.
5. Live webcam+mic+(sim)vitals demo producing gated intent forecasts; modality bars nonzero.

---

## Dependencies

- GPU machine for YOLO/finetune + available dog-home clips.
- Public datasets: Barkopedia, PhysioZoo/Mendeley.
- `coremltools` + `onnxruntime` for export; Jetson for edge (optional).
- No Helox coupling required (Aarflingo trains locally), but can route curated intents to Helox if a shared control-plane model is desired.

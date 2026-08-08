# Public datasets for Aarflingo multimodal training

Curated open sources for vision, audio, and physiological encoders. The default
`./scripts/train_aarflingo.sh` trains on **synthetic data shaped after these
datasets** so the pipeline works offline. Use the fetch script when you want real
recordings.

## Vision — YOLO dog detection

| Source | What | URL |
|--------|------|-----|
| **Stanford Dogs** | 120 breeds, real dog photos (~750 MB) | http://vision.stanford.edu/aditya86/ImageNetDogs/ |
| Ultralytics YOLOv8n | COCO-pretrained detector (class 16 = dog) | https://docs.ultralytics.com |
| Home fine-tune (future) | Label clips from `services/ingest` | local |

Artifact: `artifacts/models/vision/yolov8n.pt`, `artifacts/bundles/default/studio/dog_yolo.onnx`

Real Stanford Dogs photos are run through the runtime perception pipeline
(detection → tracking → pose → approach geometry) to produce **real feature
rows** for audit / calibration / feedback-driven retraining:

```bash
./scripts/fetch_public_datasets.sh --dog-images          # full ~750 MB
./scripts/fetch_public_datasets.sh --dog-images-sample   # a few breeds, fast
poetry run aarflingo-perception collect-real --directory data/raw/dog_images
poetry run aarflingo-perception verify-real --file artifacts/real/vision_features.jsonl
```

## Audio — bark / whimper / arousal-valence

| Source | Size | URL |
|--------|------|-----|
| **DogSpeak** | 77k bark sequences, 156 dogs | https://huggingface.co/datasets/ArlingtonCL2/DogSpeak_Dataset |
| **Barkopedia (EmotionalCanines)** | 1,400 clips, arousal + valence | https://huggingface.co/datasets/ArlingtonCL2/BarkopediaDogEmotionClassification_Data |
| **AudioSet** | whimper (dog) class | https://research.google.com/audioset/dataset/whimper_dog.html |

Artifact: `artifacts/models/default/vocal.pt`

## Physiological — ECG, HRV, IMU

| Source | Modality | URL |
|--------|----------|-----|
| **PhysioZoo** | Dog ECG @ 500 Hz, R-peaks, HRV | https://physionet.org/content/physiozoo/1.0.0/ |
| **UWB-DVS** | Radar + clinical BM7Vet ECG reference | https://www.nature.com/articles/s41597-024-02947-4 |
| **Zenodo dog HRV stress** | Wearable R-R intervals + cortisol | https://zenodo.org/records/19383015 |
| **Mendeley posture IMU** | Neck/chest/back @ 100 Hz | https://data.mendeley.com/datasets/mpph6bmn7g/1 |
| **Mendeley behavior IMU** | Collar + harness 6-DoF | https://data.mendeley.com/datasets/vxhx934tbn/3 |

Library: `lib/aarf-physio` (`aarf-physio list-sources`)

Artifact: `artifacts/models/default/vitals.pt`

## Fetch real data (optional)

```bash
./scripts/fetch_public_datasets.sh --list
./scripts/fetch_public_datasets.sh --barkopedia   # ~67 MB HF sample set
./scripts/fetch_public_datasets.sh --dog-images   # real dog photos (~750 MB)
./scripts/fetch_public_datasets.sh --dog-images-sample   # few breeds, fast
# PhysioNet PhysioZoo requires account: https://physionet.org/settings/credentials/
```

## Voice — deepiri-speech engine

AARFLingo speaks to and listens for the dog through the **deepiri-speech**
engine (deepiri-platform PR #302, FastAPI + Pipecat + LiveKit on `:5020`).

```bash
poetry run aarflingo-voice status
poetry run aarflingo-voice speak --text "come here buddy" --play
poetry run aarflingo-voice listen --audio bark.wav        # classify + respond
poetry run aarflingo-voice respond                        # camera loop, speaks on intent change
```

Enable the runtime voice hook (speaks when the dog's intent changes):

```bash
VOICE_ENABLED=1 SPEECH_URL=http://localhost:5020 poetry run aarflingo-runtime
```

Offline: without the engine running, TTS falls back to a silent WAV and STT
returns an empty transcript, so the voice CLI and runtime hook still work in dev.

## Train everything

```bash
./scripts/train_aarflingo.sh
SKIP_VISION=1 ./scripts/train_aarflingo.sh    # no YOLO download
STAGES=physio,triad ./scripts/train_aarflingo.sh
```

# AARFLingo Architecture

## Pipeline

```
ingest → perception → labeler → forecast → artifact-bridge → apps
                ↓
           aarf-gate (ethogram coupling)
```

## Services

- **ingest** — Captures short clips around motion triggers; records baselines.
- **perception** — Lightweight CV features: dog bbox, pose keypoints, gaze proxy, scene context.
- **labeler** — Human review queue; anticipation labels for semi-supervised training.
- **forecast** — Triad head (intent × emotion × behavior) with coupling-aware loss.
- **artifact-bridge** — Exports ONNX/CoreML bundles with signed manifests.

## Shared contracts

- `ethogram/` — Source of truth for labels and coupling matrix.
- `core/triad-spec/` — JSON schemas exchanged between services.
- `lib/aarf-gate` — Runtime enforcement of ethogram constraints in TS/Swift clients.

## Deployment targets

| Target | Artifact | App |
|--------|----------|-----|
| Desktop review | ONNX + gate | aarf-studio |
| iOS on-device | CoreML | aarf-pocket |

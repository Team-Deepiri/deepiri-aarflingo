# deepiri-aarflingo

Monorepo for **AARF** (Affect-Action-Response Framework) dog ethogram modeling:
capture → perceive → label → forecast → deploy.

## Layout

| Path | Role |
|------|------|
| `ethogram/` | Canonical intents, emotions, behaviors, coupling matrix |
| `core/triad-spec/` | JSON schemas for session/event/prediction/baseline |
| `services/ingest` | Clip capture and baseline recording |
| `services/perception` | Vision pipeline (detect, pose, gaze, scene) |
| `services/labeler` | Human review and anticipation labeling |
| `services/forecast` | Triad model training and inference |
| `services/artifact-bridge` | ONNX/CoreML export and manifests |
| `lib/aarf-gate` | TypeScript ethogram coupling gate |
| `apps/aarf-studio` | Desktop review studio (Electron + Vite) |
| `apps/aarf-pocket` | iOS on-device CoreML viewer |

## Quick start

```bash
./scripts/setup.sh
./scripts/smoke_pipeline.sh
```

## Bootstrap history

```bash
python scripts/bootstrap_commits.py
```

## License

Apache-2.0 — see [LICENSE](LICENSE).

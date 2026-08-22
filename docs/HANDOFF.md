# Handoff — pick up here

> Single source of truth for "where are we, what's next". Update the checkboxes
> as you go; deeper plans live in [ROADMAP.md](ROADMAP.md).

**Last updated:** 2026-08-21 · **Branch:** `feat/home-capture` · **Open PR:** [#33](https://github.com/Team-Deepiri/deepiri-aarflingo/pull/33)

---

## State right now

| Item | Status |
|------|--------|
| Roadmap through v1.0 + research paper | ✅ merged (PR #32) |
| Home-capture tooling (bridge-aware capture, auto-label, breed extra-stills) | ✅ built, tests green — **in open PR #33** |
| Collar Rev-A KiCad + in-repo `kicad-launcher` | ✅ on this branch — `./kicad-launcher --sch verify` |
| Collar EE + firmware design docs | ✅ [DESIGN_SPEC](../hardware/collar-reva/DESIGN_SPEC.md), [AFE](../hardware/collar-reva/AFE_CALCULATIONS.md), [MATH](../hardware/collar-reva/MATH.md), [FIRMWARE_COLLAR](FIRMWARE_COLLAR.md) |
| Windows webcam bridge | ⛔ not running — start it before capture (command below) |
| Runtime server (port 8765) | ⛔ down — old pre-PR#23 process was killed; restart loads current code (cv2 import chain verified fixed) |
| Live vitals/IMU feed (`vitals.pt` in runtime) | ⬜ not started — Completion §1 |
| Mobile voice display + offline fallback | ⬜ not started — Completion §3 |

## Your dog session (do this)

```powershell
# 1. Windows PowerShell — start the bridge
.\scripts\webcam\start_webcam_bridge.ps1
```

```bash
# 2. WSL — capture ~200 motion-skipped frames + YOLO auto-labels
make home-capture

# 3. Review boxes (x,y = center, normalized 0–1); delete junk frames
$EDITOR data/dog/captures/labels.jsonl

# 4. Fine-tune detector → artifacts/models/vision/dog_yolo.onnx
make home-train

# 5. Breed ID on your dog: ~30 varied stills → data/my_dog/breed/<Breed>/
poetry run aarflingo-perception train-breed --extra-dir data/my_dog/breed

# 6. Restart runtime, open studio, verify bbox + breed at 5+ fps
./scripts/run_runtime.sh     # studio served at http://localhost:8765
```

Full details: [HOME_CAPTURE.md](HOME_CAPTURE.md). Done-when: stable
`dog_present=true` + correct breed label in your room/lighting; then tick
ROADMAP Completion §2 boxes.

## After the session

1. Merge PR #33 (all checks green locally; CI will confirm).
2. Tick ROADMAP Completion §2 items that passed.
3. Next build item per roadmap: **Completion §1 live vitals/IMU feed**
   (`vitals.pt` load path in runtime mirroring `update_audio_modality`,
   simulated 6-DoF stub first) — unblocks ECG/IMU bars and the paper's
   physiology ablation.
4. Paper track starts once home data exists: dataset protocol in ROADMAP
   "Research paper" §2 (`docs/paper/METHODS.md` etc.).

## Gotchas learned this session

- WSL has no `/dev/video*` — always go through the bridge or `--source URL`.
- `poetry install --sync` prunes ad-hoc pip installs (torchvision/ultralytics
  were wiped once); restore with `--extras yolo` + force-reinstall opencv if
  `import cv2` breaks.
- typer must stay ≥0.17 while click is 8.4.x, or every CLI `--help` crashes.
- Per-service test runs need that service on PYTHONPATH:
  `PYTHONPATH=".:services/<svc>" poetry run pytest -q services/<svc>/tests`.

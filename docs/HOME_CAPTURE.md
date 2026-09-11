# Home data capture — fine-tune on YOUR dog

One session: capture frames from your room → model-assisted labels → fine-tuned
detector + breed head that replace the generic COCO weights in the runtime.

## Quick start (WSL + webcam bridge)

```bash
# 0. On Windows, start the bridge (WSL has no /dev/video*):
#    .\scripts\webcam\start_webcam_bridge.ps1

# 1. Capture + auto-label in one command
make home-capture            # FRAMES=300 make home-capture to grab more

# 2. Review labels (x,y = box CENTER, normalized 0–1)
$EDITOR data/dog/captures/labels.jsonl

# 3. Fine-tune the detector → artifacts/models/vision/dog_yolo.onnx
make home-train

# 4. Breed ID: drop stills of your dog in data/my_dog/breed/<Breed>/ then
poetry run aarflingo-perception train-breed --extra-dir data/my_dog/breed

# 5. Restart the runtime so it loads the new ONNX
./scripts/run_runtime.sh
```

**Done when:** stable `dog_present=true` bbox + correct breed label at 5+ fps
in your actual room/lighting.

## How capture finds a source

`capture-frames` resolves its source in order:

1. `--source URL-or-index` when given (e.g. `http://192.168.1.50:8766/video/stream`)
2. local camera index (`--camera`, default 0)
3. WSL bridge auto-detect — probes `127.0.0.1:8766/health`, then the NAT-mode
   host IP from `/etc/resolv.conf`

## Model-assisted labeling

`auto-label-dog` runs COCO YOLOv8n over every captured frame and pre-fills
`data/dog/captures/labels.jsonl` with boxes above `--conf` (default 0.25).
Files that already have rows are kept unless `--overwrite`. Multiple dogs per
frame are supported (one JSONL row per rect).

You only review and fix — hand-drawing boxes from scratch is not required.
Frames with no row train as background (negatives), which is what you want for
empty-room shots.

## Personal breed stills

`train-breed --extra-dir data/my_dog/breed` merges your stills into the
Stanford Dogs training run:

- folder name = `<Breed>` or `<synset>-<Breed>` (e.g. `n02085620-Chihuahua`)
- matching an existing 120-way breed reuses that class; unknown names become
  new classes appended to `breed_labels.json`
- ~15% of your stills are held out for val so metrics reflect them

Aim for 30+ varied stills (lighting, distance, pose) — captured frames with a
dog crop work well: crop the bbox region from `data/dog/captures` frames.

## Commands reference

| Command | Purpose |
|---------|---------|
| `aarflingo-perception capture-frames --out DIR [--source URL] [--frames N]` | motion-skipped frame grab |
| `aarflingo-perception auto-label-dog [--captures DIR] [--conf F] [--overwrite]` | pre-fill labels.jsonl |
| `aarflingo-perception prep-dog-yolo` | captures+JSONL → YOLO dataset layout |
| `aarflingo-perception finetune-dog-yolo [--epochs N]` | train + export dog_yolo.onnx |
| `aarflingo-perception train-breed --extra-dir DIR` | breed head incl. your dog |

See also: [LABELING.md](LABELING.md) (triad labeling) · [WEBCAM.md](WEBCAM.md) (bridge setup)

# Reproduce

Manuscript: [PAPER.md](PAPER.md). arXiv source: [aarflingo.tex](aarflingo.tex).

## Harness (no GPU)

```bash
python3 -m pytest -q core/tests/test_v1_gate.py
python3 scripts/v1_gate.py              # writes docs/paper/RESULTS.md
python3 scripts/v1_gate.py --require-bar   # fails until the bar is real
```

## Train + artifact verify

```bash
./scripts/train_aarflingo.sh
python3 scripts/verify_artifacts.py
```

`verify_artifacts.py` checks that a checkpoint loads. It is **not** the v1.0 bar.

## Jetson hub

Build on L4T (or buildx for arm64):

```bash
docker build -f infra/docker/jetson.Dockerfile -t aarflingo-edge .
docker run --rm aarflingo-edge python3 -m app.cli status
docker run --rm --device /dev/video0 -v "$(pwd)/artifacts/bundles:/opt/aarflingo/artifacts/bundles:ro" aarflingo-edge
```

Host without Docker:

```bash
PYTHONPATH=.:services/edge-runtime python3 -m app.cli status
```

The collar flashes with `./scripts/flash_collar.sh`. It does not run this image.

Live puck → triad slots (laptop or phone on the same LAN as runtime):

```bash
python3 scripts/collar_listen.py --runtime http://127.0.0.1:8000
```

## Home eval

1. Capture and label sessions (`docs/HOME_CAPTURE.md`, studio feedback).
2. Export one JSONL row per scored window to `data/dog/eval/dog_split.jsonl`.
3. Re-run `python3 scripts/v1_gate.py --require-bar`.

# Hardware deployment

## Runtime container (USB webcam + API)

```bash
docker compose -f infra/docker/docker-compose.yml build aarf-runtime
docker compose -f infra/docker/docker-compose.yml up aarf-runtime
```

Mounts `artifacts/` for models and feedback DB. Exposes port **8765**.

## Jetson / collar edge loop

Build on L4T host:

```bash
docker build -f infra/docker/jetson.Dockerfile -t aarflingo-edge .
docker run --device /dev/video0 -v $(pwd)/artifacts/bundles:/opt/aarflingo/artifacts/bundles:ro aarflingo-edge
```

Native (no Docker):

```bash
cd services/edge-runtime && poetry install
export PYTHONPATH=/path/to/deepiri-aarflingo
poetry run aarflingo-edge run --camera 0
```

Export ONNX before edge deploy:

```bash
cd services/forecast && poetry run aarflingo-forecast build-default
cd ../artifact-bridge && poetry run aarflingo-artifact-bridge --out ../../artifacts/bundles/default/studio
```

## BOM pointer

See [PHASE2_COLLAR.md](PHASE2_COLLAR.md) for Jetson Orin Nano, MIPI camera, LiPo, and enclosure notes.

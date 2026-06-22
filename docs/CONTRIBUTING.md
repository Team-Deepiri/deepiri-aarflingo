# Contributing to deepiri-aarflingo

## Branching

- **`main`** — stable; CI must be green before merge.
- **`dev`** — integration branch for features. Branch off `dev`, open PRs into `dev`.

```bash
git checkout dev
git pull origin dev
git checkout -b feat/my-change
```

## Local setup

```bash
./setup.sh              # system + project deps + default model
./setup.sh --run        # install and launch Electron studio
make test               # unit tests across services
make train              # train checkpoint + ONNX + artifact verify
make smoke              # quick perception + train + feedback smoke
make verify             # full test suite + train + runtime + studio build
```

## Run live stack

```bash
make dev                # runtime + Vite studio (web)
make electron           # desktop Electron shell + Vite
./setup.sh --kill       # stop background processes
```

Runtime API: http://127.0.0.1:8765 — see [README](README.md) for endpoints.

## CI

GitHub Actions on `main` and `dev`:

- **Deepiri CI** — Python services, core metrics, aarf-gate, studio build
- **CodeQL** — Python + TypeScript security analysis

## Commits

Use conventional prefixes: `feat`, `fix`, `chore`, `docs`, `test`, `ci`, `refactor`.

Keep commits focused; the repo uses atomic history where practical.

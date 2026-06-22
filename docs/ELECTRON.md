# AARF Studio — Electron desktop

The web UI runs in the browser via Vite. The Electron shell wraps the same renderer for a native desktop window.

## Dev (hot reload)

```bash
# terminal 1
./scripts/run_runtime.sh

# terminal 2
cd apps/aarf-studio
npm install
npm run electron:dev
```

`electron:dev` starts Vite and opens Electron pointed at `http://127.0.0.1:5173`.

## Production build

```bash
cd apps/aarf-studio
npm run electron:start   # vite build + electron loads dist/
```

## Preload API

`electron/preload.mjs` exposes `window.aarf`:

| Field | Description |
|-------|-------------|
| `isElectron` | `true` in desktop shell |
| `runtimeUrl` | AARF runtime base URL (default `http://127.0.0.1:8765`) |

Set `VITE_RUNTIME_URL` before launch to point at a remote runtime.

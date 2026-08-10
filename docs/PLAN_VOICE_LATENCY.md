# Plan — low-latency TTS + deepiri-speech → aarflingo wire-up

Status: DRAFT
Owner: deepiri-speech + deepiri-aarflingo
Repos: `deepiri-speech` (engine), `deepiri-aarflingo` (consumer/runtime)

---

## 1. Goal

Close the loop: **deepiri-speech is the dog's voice + ears, aarflingo is the brain.**
Make TTS fast enough that the phrase a dog actually hears starts *speaking*
within ~100–200 ms of an intent prediction, then make sure aarflingo actually
consumes the engine (currently it half-does via a thin HTTP client).

Three workstreams:

1. **Fix + harden deepiri-speech** (test hang already fixed; remaining: latency audit).
2. **Latency-optimize TTS** in the engine.
3. **Wire engine into aarflingo** properly (speech client + runtime voice hook + latency telemetry).
4. **Resume pending aarflingo work**: uncommitted `webcam_bridge.py` rewrite
   (shared-owner single-writer architecture) is complete but not committed/verified.

---

## 2. deepiri-speech — status of prior work

| Item | State |
|---|---|
| Test hang on `POST /v1/sessions` (Redis xadd to dead port blocks forever) | ✅ Fixed — root cause: `redis.asyncio` connects on-demand in `publish_stream`; loopback to an unbound port gets *dropped*, not refused → infinite connect wait. Fix: hermetic `FakeBus` in tests (no Redis/LiveKit network). |
| 18 tests | ✅ `18 passed in 1.39s` |
| `kokoro-onnx` installed? | ❌ No (onnxruntime/numpy/pipecat/openai present, kokoro_onnx absent) |

**Latency audit findings (TTS path):**

- `providers.KokoroTTS.synthesize` — whole-utterance synth in `to_thread`; model
  loads **lazily on first request** (multi-second cold start); no cache; re-encodes
  numpy → WAV each call; `speed` hardcoded 1.0.
- `providers.OpenAITTS` — creates a **new `OpenAI` client per request** (re-inits
  connection pool, TLS) inside every `synthesize`; should be a singleton.
- `pipecat_bridge.ProviderTTS` — no cache; every TextFrame → full synth.
- Engine has **no warm-start** — models load on first real audio, so the very first
  dog phrase pays the full cold-start price.
- No TTS latency telemetry anywhere (health has no per-request timing).

---

## 3. Latency-optimization work (deepiri-speech)

Priority order (highest ROI first):

### 3.0 LOCAL-FIRST ENGINE (decision, 2026-08-09)
The engine runs **100% local open-source speech** by default — no OpenAI, no cloud.
Research (CodeSOTA/localaimaster 2026): **Kokoro-82M** is the top local TTS
(Apache-2.0, 82M params, CPU-friendly, ~210x realtime on GPU, ~90–855 ms first
audio); **faster-whisper** (CTranslate2) is the standard open-source local STT
(~4x faster than Whisper, CPU/GPU). OpenAI remains an **opt-in** provider via
`STT_PROVIDER=openai` + `OPENAI_API_KEY` — never the default.

- Defaults flipped: `TTS_PROVIDER=kokoro`, `STT_PROVIDER=faster_whisper` (was `mock`).
- `KOKORO_AUTO_DOWNLOAD=1` default — models pull to `KOKORO_MODEL_DIR` on first use.
- faster-whisper downloads to `WHISPER_MODEL_DIR` (HF cache override) on first use.
- Fallback: if a local engine isn't installed, provider resolution degrades to
  `mock` with a warning (CI/dev stay hermetic via tests/conftest.py).

### 3.1 Reusable HTTP client in OpenAI providers
`OpenAISTT` / `OpenAITTS` each `OpenAI(api_key=...)` per call. Lift to a module
singleton (thread-safe lazy init) so connection pooling + TLS handshake happen once.
(OpenAI is now opt-in only.)

### 3.2 TTS result cache (LRU)
Phrase bank is small and heavily repeated ("Come here, good dog!"). Add an
`functools.lru_cache`-style (bounded, thread-safe) cache keyed by
`(provider, model, voice, text)`. First utterance pays full cost; every repeat is
a dict read. Invalidate via `reset_provider_singletons`.

### 3.3 Warm-start on lifespan
Add `TTS_WARM_UP` / `STT_WARM_UP` settings (default on). During FastAPI lifespan,
fire a background `asyncio.create_task` that calls `provider.warmup()` (loads
Kokoro/whisper model, runs a 1-second silence synth) so the first real request is
already hot. Warm-up failures are non-fatal, logged, and the provider still works.

### 3.4 Kokoro: reuse buffer, allow speed, skip re-encode when possible
- Keep loaded `Kokoro` instance (already singleton) — cold start only on warm-up.
- Add `TTS_SPEED` setting; pass `speed=` through instead of hardcoding.
- Keep WAV output (client needs it) but don't rebuild headers for cached hits.
- `KokoroTTS.warmup()`: load model + synth a 1-s phrase in background.

### 3.5 TTS latency telemetry
Add per-request `latency_ms` to the TTS/stt responses via a `X-Processing-Ms`
header (and/or a `metric` in the JSON body where the contract returns JSON).
Health endpoint reports `tts_last_ms`, `tts_avg_ms`, `tts_cache_hits`.

### 3.6 (Scoped) pipecat ProviderTTS cache reuse
`ProviderTTS` calls the same `get_tts()` singleton — so it inherits the cache from
3.2 automatically. No separate work beyond confirming cache is shared.

---

## 4. Wire engine into aarflingo

Current state: `services/voice/app/speech_client.py` is a thin sync httpx client
with offline fallback. Runtime engine calls it **synchronously inside the 15 fps
frame loop** (`engine._conversation_speak` → `voice.client.synthesize`) — that
stalls vision inference while TTS runs. Fix:

### 4.1 Async + non-blocking TTS in runtime
- `SpeechClient` gains async `synthesize_async()` (httpx.AsyncClient) + a
  `latency_ms` field on results.
- `engine._conversation_speak` schedules TTS as a background task (`asyncio.create_task`)
  with a per-utterance timeout instead of blocking `process_frame`.
- Voice utterances write to `artifacts/voice/` as now (already non-blocking after the change).

### 4.2 Streaming speak path (post-MVP)
Add `/v1/tts/stream` (or reuse `/v1/pipecat/ws`) that streams audio chunks.
Runtime plays the first chunk as soon as it arrives → perceived latency drops to
first-byte time, not full-file time. Deferred until base latency is measured.

### 4.3 Latency instrumentation surfaced to studio
`/health` and runtime `live_status()` expose:
`tts_latency_ms` (p50/p95 window), `tts_cache_hits`, `stt_latency_ms`.
Studio live rail shows them once present.

### 4.4 Contract alignment
Verify client ↔ engine contract matches the *actual* engine endpoints:
`POST /v1/tts` (returns raw audio — client handles bytes ✅), `POST /v1/stt`
(multipart ✅), `POST /v1/sessions`, `GET /health`. Keep offline silent-WAV fallback.

---

## 5. Latency testing methodology

> "test you can use audio clips online and transmit them and get the latency"

Two measurements, both from the host:

### 5.1 TTS latency (text → audio)
```
echo 'Come here, good dog!' | ... POST /v1/tts  →  time to first byte
```
- Script measures: cold-start ms, warm p50/p95, cache-hit ms, file size.
- Target: warm first-byte < 200 ms; cache-hit < 5 ms; cold-start moved to startup.

### 5.2 STT latency (audio clip → text)
Grab a public WAV/webm speech clip (e.g. a LibriVox/Common Voice sample), POST it
to `/v1/stt`, measure end-to-end. Also test the duplex WS path by replaying the
clip bytes into `/v1/session/ws` and timing `stt_final` → `tts_chunk`.

Deliverable: `scripts/bench_latency.py` (in deepiri-speech) printing a
`LATENCY_REPORT.md` table. Re-run after each optimization to prove the delta.

---

## 6. Pending aarflingo work — resume

Uncommitted, appears complete, NOT verified:
`scripts/webcam/webcam_bridge.py` — rewritten from per-connection camera ownership
(which wedged the camera under concurrent clients) to a single
`CameraOwner` thread publishing to a shared slot + many read-only MJPEG subscribers.

Remaining:
- [ ] Read it as-is, confirm the design holds (done above — looks coherent).
- [ ] Syntax/import smoke check + a short `--source <file>` run (a video file, not
      a camera, so it runs headless in CI).
- [ ] Add a minimal pytest for the slot semantics (single-writer publish, latest-wins,
      idempotent `start_owner`).
- [ ] Commit on `feat/mobile-pocket-apps` with a conventional message.

---

## 7. Execution order

1. deepiri-speech: OpenAI singleton reuse + TTS LRU cache + warm-start + telemetry. *(3.1–3.6)*
2. deepiri-speech: `scripts/bench_latency.py` + baseline run. *(5)*
3. aarflingo: async TTS client + non-blocking runtime speak + live_status metrics. *(4.1, 4.3, 4.4)*
4. aarflingo: verify + commit webcam_bridge.py rewrite. *(6)*
5. Streaming speak path only if p50 > target after 1–3. *(4.2)*
6. Update `docs/VOICE.md` + ROADMAP.

## 8. Definition of done

- deepiri-speech: 18 tests green; warm TTS first-byte p50 < 200 ms; cache-hit < 5 ms;
  latency telemetry in `/health`; OpenAI client reused.
- aarflingo: TTS async/non-blocking in frame loop; studio shows tts/stt latency;
  webcam_bridge committed + tested; `docs/VOICE.md` reflects the new flow.

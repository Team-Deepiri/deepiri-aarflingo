# VOICE — Bidirectional Dog Conversation Loop

Aarflingo doesn't just classify your dog — it talks back. The voice system
closes a **speak → listen → learn** loop that adapts phrase choices to your
specific dog over time.

---

## How it works

```
Camera ──► TriadNet prediction
                │
                ▼
        ConversationEngine.on_prediction()
                │ best_phrase_for(pred)        ← weighted by past outcomes
                ▼
        DogVoice.speak()  ──►  deepiri-speech TTS  ──►  speaker
                │   (background worker — never blocks the 15 fps frame loop)
                │
                │  (response window: 8 s)
                │
Microphone ──► MicListener
                │ bark detected + classified (arousal / valence)
                ▼
        ConversationEngine.on_bark()
                │
                ▼
        score outcome  ──►  update phrase weight  ──►  artifacts/voice/phrase_weights.json
                │
                ▼
        FeedbackStore.log_voice_outcome()  ──►  artifacts/feedback/aarf.db
```

---

## Quick start

```bash
# 1. Start the deepiri-speech engine — 100% local-first (Kokoro TTS + faster-whisper
#    STT, no cloud/OpenAI required). Models auto-download on first boot.
#    cd ../deepiri-speech && poetry install -E engines && poetry run uvicorn deepiri_speech.main:app --port 5020

# 2. Start the runtime with voice + mic enabled
VOICE_ENABLED=1 SPEECH_URL=http://localhost:5020 poetry run aarflingo-runtime

# 3. Open the studio (or hit the API directly)
./setup.sh --run

# Check health + voice status
curl http://localhost:8765/health
curl http://localhost:8765/voice/outcomes   # what the dog said back
curl http://localhost:8765/voice/weights    # learned phrase weights
```

---

## CLI commands

```bash
# Speak a phrase directly (oneshot)
poetry run aarflingo-voice speak --text "come here buddy" --play

# Classify a bark file + respond
poetry run aarflingo-voice listen --audio bark.wav

# Watch camera and speak whenever intent changes
poetry run aarflingo-voice respond --frames 300

# Check speech engine status
poetry run aarflingo-voice status
```

---

## Offline mode

When `deepiri-speech` is not running, TTS returns a **silent WAV** and STT
returns an empty transcript. The conversation engine still runs, weights still
update, and outcomes still log — the dog just won't hear anything from the
speaker. Useful for CI and development without audio hardware.

---

## What phrase weights mean

Every spoken phrase gets a weight (default `1.0`, range `0.05 – 2.0`).

| Dog response | Reward | Effect on weight |
|---|---|---|
| Bark with **positive** valence within 8 s | +1.0 | Weight goes up → phrase used more |
| **Silence** for 8 s | 0.0 | Weight unchanged |
| Bark with **negative** valence within 8 s | −0.5 | Weight goes down → phrase used less |

The update rule is an exponential moving average (α = 0.15):

```
w_new = 0.85 * w_old + 0.15 * target
```

where `target` maps the reward to `[0, 2]`. This means:
- One positive response shifts the weight by ~15% toward `2.0`.
- It takes roughly 10 negative responses with no positive ones to halve a
  phrase's weight from `1.0` to ~`0.5`.
- The floor of `0.05` ensures no phrase is permanently silenced.

Weights survive restarts — stored in `artifacts/voice/phrase_weights.json`.

---

## How the engine learns

The `ConversationEngine` doesn't require a trained model or labelled data. It
learns purely from **your dog's actual bark responses** to what you say.

After ~20–30 sessions you'll notice that for your dog:
- Phrases it responds to positively (excited bark, tail wag detected → high
  arousal + positive valence) will rise in weight and be preferred.
- Phrases it ignores or responds to anxiously will drift down.
- The system settles on a personalised phrase set for each (intent, emotion)
  combination without any manual labelling.

To reset learning for a specific phrase, delete its entry from
`artifacts/voice/phrase_weights.json` and restart the runtime.

To reset all learning:

```bash
rm artifacts/voice/phrase_weights.json
```

---

## Mic listener

`MicListener` captures audio in 300 ms chunks at 16 kHz. A bark is detected
when:

- RMS > 0.05 (loud enough to be a bark, not ambient noise)
- Zero-crossing rate > 0.02 (has harmonic content, not a door slam)

If the vocal encoder checkpoint (`artifacts/models/default/vocal.pt`) is
present, arousal/valence are classified by the neural model. Otherwise a
spectral heuristic is used (works well enough for learning).

Every chunk (bark or not) also emits a continuous audio modality sample —
`audio_arousal`, `audio_valence`, `audio_bark_prob` (RMS-scaled 0–1) — which
the runtime fuses into `process_frame` via `update_audio_modality`, so the
vision pipeline always sees live audio, not just bark events.

A **debounce window of 400 ms** suppresses repeated detections from a single
bark burst.

`sounddevice` is required for live mic capture:

```bash
pip install sounddevice
```

Without it the listener degrades gracefully — it logs a warning and stays
idle. The runtime still starts.

---

## Architecture diagram

```
services/voice/app/
├── mic_listener.py     # background thread: chunk → bark detect → BarkEvent
├── conversation.py     # ConversationEngine: speak + score + weight update
├── dog_voice.py        # phrase bank + DogVoice (cooldown wrapper)
├── speech_client.py    # deepiri-speech HTTP client + offline fallback
└── wav.py              # stdlib PCM WAV decode

services/runtime/app/
└── engine.py           # VOICE_ENABLED=1 → wires ConversationEngine + MicListener

services/feedback/app/
└── store.py            # voice_outcomes table: phrase / arousal / valence / reward

artifacts/voice/
├── phrase_weights.json # learned phrase weights (persisted across restarts)
└── utterance-*.wav     # audio files of what was spoken (for debugging)
```

---

## Extending the phrase bank

Edit `services/voice/app/dog_voice.py`. Phrases are keyed by
`(intent_id, emotion_id)` — look at `ethogram/intents.yaml` and
`ethogram/emotions.yaml` for valid values.

```python
_PHRASES[("outside", "excited")] = [
    "Outside time! Let's go, good dog.",
    "Wanna go out? Let's go, buddy.",
    "Walk time! Come on!",          # ← new phrase; starts at DEFAULT_WEIGHT
]
```

The new phrase starts at weight `1.0` and will rise or fall based on your
dog's responses.

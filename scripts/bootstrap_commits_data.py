"""Bootstrap commit definitions for deepiri-aarflingo monorepo."""

from __future__ import annotations

ALL_COMMITS: list[tuple[dict[str, str], str]] = [
    (
        {
            "LICENSE": """\
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works, within the Source form or
          documentation, if provided along with the Derivative Works, or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   Copyright 2026 Deepiri

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
""",
        },
        "chore: add Apache-2.0 license",
    ),
    (
        {
            ".gitignore": """\
# Python
__pycache__/
*.py[cod]
.venv/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
dist/
*.tsbuildinfo

# Swift / Xcode
.build/
DerivedData/
*.xcuserstate

# Artifacts
artifacts/bundles/*
!artifacts/bundles/.gitkeep
artifacts/manifests/*
!artifacts/manifests/.gitkeep
*.onnx
*.mlmodel
*.mlpackage

# Data
data/raw/
data/clips/
*.mp4
*.mov

# Env
.env
.env.*

# OS
.DS_Store
Thumbs.db
""",
        },
        "chore: add gitignore",
    ),
    (
        {
            "README.md": """\
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
""",
        },
        "docs: add project README",
    ),
    (
        {
            "ethogram/intents.yaml": """\
# Canonical dog intent taxonomy (AARF triad — intent axis)
version: "1.0"
intents:
  - id: approach
    label: Approach
    description: Moving toward a person, object, or stimulus
  - id: avoid
    label: Avoid
    description: Moving away or increasing distance from stimulus
  - id: solicit_play
    label: Solicit play
    description: Play bow, bounce, or toy presentation
  - id: rest
    label: Rest
    description: Settling, lying down, low arousal stillness
  - id: guard_resource
    label: Guard resource
    description: Protecting food, toy, or space
  - id: explore
    label: Explore
    description: Sniffing, scanning environment without fixation
  - id: alert
    label: Alert
    description: Orienting to novel or salient stimulus
""",
        },
        "feat(ethogram): define intent taxonomy",
    ),
    (
        {
            "ethogram/emotions.yaml": """\
# Affect / arousal axis for AARF triad
version: "1.0"
emotions:
  - id: calm
    label: Calm
    valence: 0.2
    arousal: 0.1
  - id: content
    label: Content
    valence: 0.5
    arousal: 0.2
  - id: excited
    label: Excited
    valence: 0.6
    arousal: 0.8
  - id: anxious
    label: Anxious
    valence: -0.4
    arousal: 0.7
  - id: fearful
    label: Fearful
    valence: -0.7
    arousal: 0.8
  - id: frustrated
    label: Frustrated
    valence: -0.5
    arousal: 0.6
  - id: conflicted
    label: Conflicted
    valence: 0.0
    arousal: 0.5
""",
        },
        "feat(ethogram): define emotion taxonomy",
    ),
    (
        {
            "ethogram/behaviors.yaml": """\
# Observable behavior labels (AARF triad — behavior axis)
version: "1.0"
behaviors:
  - id: tail_wag_loose
    label: Loose tail wag
    modality: body
  - id: tail_tucked
    label: Tail tucked
    modality: body
  - id: play_bow
    label: Play bow
    modality: body
  - id: lip_lick
    label: Lip lick
    modality: face
  - id: whale_eye
    label: Whale eye
    modality: face
  - id: hard_stare
    label: Hard stare
    modality: gaze
  - id: yawning
    label: Yawning
    modality: face
  - id: sniff_ground
    label: Sniff ground
    modality: scene
  - id: freeze
    label: Freeze
    modality: body
  - id: bark
    label: Bark
    modality: vocal
""",
        },
        "feat(ethogram): define behavior taxonomy",
    ),
    (
        {
            "ethogram/coupling-matrix.json": """\
{
  "version": "1.0",
  "description": "Allowed intent-emotion-behavior triples with prior weights",
  "triples": [
    {"intent": "solicit_play", "emotion": "excited", "behavior": "play_bow", "weight": 0.9},
    {"intent": "solicit_play", "emotion": "excited", "behavior": "tail_wag_loose", "weight": 0.85},
    {"intent": "approach", "emotion": "content", "behavior": "tail_wag_loose", "weight": 0.7},
    {"intent": "approach", "emotion": "anxious", "behavior": "lip_lick", "weight": 0.6},
    {"intent": "avoid", "emotion": "fearful", "behavior": "tail_tucked", "weight": 0.85},
    {"intent": "avoid", "emotion": "anxious", "behavior": "whale_eye", "weight": 0.75},
    {"intent": "rest", "emotion": "calm", "behavior": "yawning", "weight": 0.5},
    {"intent": "rest", "emotion": "content", "behavior": "sniff_ground", "weight": 0.4},
    {"intent": "guard_resource", "emotion": "frustrated", "behavior": "hard_stare", "weight": 0.8},
    {"intent": "guard_resource", "emotion": "conflicted", "behavior": "freeze", "weight": 0.65},
    {"intent": "explore", "emotion": "content", "behavior": "sniff_ground", "weight": 0.8},
    {"intent": "alert", "emotion": "excited", "behavior": "hard_stare", "weight": 0.7},
    {"intent": "alert", "emotion": "anxious", "behavior": "freeze", "weight": 0.55},
    {"intent": "solicit_play", "emotion": "content", "behavior": "bark", "weight": 0.3}
  ],
  "forbidden_pairs": [
    {"intent": "rest", "behavior": "play_bow"},
    {"intent": "avoid", "behavior": "play_bow"},
    {"intent": "rest", "emotion": "excited"}
  ]
}
""",
        },
        "feat(ethogram): add coupling matrix for triad gating",
    ),
    (
        {
            "core/triad-spec/prediction.json": """\
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://deepiri.dev/aarflingo/triad/prediction.json",
  "title": "TriadPrediction",
  "type": "object",
  "required": ["intent_id", "emotion_id", "behavior_id", "confidence", "ts_ms"],
  "properties": {
    "intent_id": {"type": "string"},
    "emotion_id": {"type": "string"},
    "behavior_id": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "ts_ms": {"type": "integer", "minimum": 0},
    "source": {"type": "string", "enum": ["model", "human", "gate"]},
    "session_id": {"type": "string"}
  },
  "additionalProperties": false
}
""",
        },
        "feat(core): add triad prediction schema",
    ),
    (
        {
            "core/triad-spec/event.json": """\
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://deepiri.dev/aarflingo/triad/event.json",
  "title": "TriadEvent",
  "type": "object",
  "required": ["event_id", "session_id", "ts_ms", "clip_uri"],
  "properties": {
    "event_id": {"type": "string"},
    "session_id": {"type": "string"},
    "ts_ms": {"type": "integer", "minimum": 0},
    "clip_uri": {"type": "string"},
    "prediction": {"$ref": "prediction.json"},
    "features": {
      "type": "object",
      "properties": {
        "gaze_aversion": {"type": "number"},
        "tail_angle_deg": {"type": "number"},
        "arousal_proxy": {"type": "number"}
      }
    }
  },
  "additionalProperties": false
}
""",
        },
        "feat(core): add triad event schema",
    ),
    (
        {
            "core/triad-spec/session.json": """\
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://deepiri.dev/aarflingo/triad/session.json",
  "title": "TriadSession",
  "type": "object",
  "required": ["session_id", "dog_id", "started_at", "environment"],
  "properties": {
    "session_id": {"type": "string"},
    "dog_id": {"type": "string"},
    "started_at": {"type": "string", "format": "date-time"},
    "ended_at": {"type": "string", "format": "date-time"},
    "environment": {"type": "string", "enum": ["home", "clinic", "field", "studio"]},
    "device": {"type": "string"},
    "baseline_id": {"type": "string"},
    "notes": {"type": "string"}
  },
  "additionalProperties": false
}
""",
        },
        "feat(core): add triad session schema",
    ),
    (
        {
            "core/triad-spec/baseline.json": """\
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://deepiri.dev/aarflingo/triad/baseline.json",
  "title": "TriadBaseline",
  "type": "object",
  "required": ["baseline_id", "dog_id", "captured_at", "metrics"],
  "properties": {
    "baseline_id": {"type": "string"},
    "dog_id": {"type": "string"},
    "captured_at": {"type": "string", "format": "date-time"},
    "clip_uri": {"type": "string"},
    "metrics": {
      "type": "object",
      "required": ["resting_heart_rate_bpm", "tail_angle_mean_deg"],
      "properties": {
        "resting_heart_rate_bpm": {"type": "number", "minimum": 40, "maximum": 200},
        "tail_angle_mean_deg": {"type": "number"},
        "gaze_aversion_mean": {"type": "number", "minimum": 0, "maximum": 1},
        "arousal_index": {"type": "number", "minimum": 0, "maximum": 1}
      }
    }
  },
  "additionalProperties": false
}
""",
        },
        "feat(core): add baseline schema",
    ),
    (
        {
            "core/metrics/anticipate_fixtures.json": """\
{
  "cases": [
    {
      "name": "play_bow_high_confidence",
      "prediction": {
        "intent_id": "solicit_play",
        "emotion_id": "excited",
        "behavior_id": "play_bow",
        "confidence": 0.92,
        "ts_ms": 1000
      },
      "expected_gate": "pass"
    },
    {
      "name": "rest_with_play_bow_forbidden",
      "prediction": {
        "intent_id": "rest",
        "emotion_id": "calm",
        "behavior_id": "play_bow",
        "confidence": 0.8,
        "ts_ms": 2000
      },
      "expected_gate": "reject"
    },
    {
      "name": "low_confidence_needs_review",
      "prediction": {
        "intent_id": "explore",
        "emotion_id": "content",
        "behavior_id": "sniff_ground",
        "confidence": 0.35,
        "ts_ms": 3000
      },
      "expected_gate": "review"
    }
  ]
}
""",
        },
        "test(core): add anticipate gate fixtures",
    ),
    (
        {
            "core/metrics/test_anticipate.py": '''\
"""Anticipation / gating metric smoke tests (stdlib only)."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).with_name("anticipate_fixtures.json")


def _load_cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]


def classify(confidence: float, forbidden: bool) -> str:
    if forbidden:
        return "reject"
    if confidence < 0.5:
        return "review"
    return "pass"


def test_fixtures_resolve() -> None:
    for case in _load_cases():
        pred = case["prediction"]
        forbidden = (
            case["name"] == "rest_with_play_bow_forbidden"
        )
        got = classify(pred["confidence"], forbidden)
        assert got == case["expected_gate"], case["name"]


if __name__ == "__main__":
    test_fixtures_resolve()
    print("ok")
''',
        },
        "test(core): add anticipate classification smoke test",
    ),
    (
        {
            "docs/ARCHITECTURE.md": """\
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
""",
        },
        "docs: add architecture overview",
    ),
    (
        {
            "docs/MATH.md": """\
# Triad Model Math

## Notation

- Intent logits \\(z_I\\), emotion \\(z_E\\), behavior \\(z_B\\)
- Coupling matrix \\(C\\) from `ethogram/coupling-matrix.json`

## Softmax heads

\\[
P(k) = \\frac{e^{z_k}}{\\sum_j e^{z_j}}
\\]

## Coupling prior loss

For batch prediction \\((i, e, b)\\):

\\[
\\mathcal{L}_{couple} = -\\log \\big( C_{i,e,b} + \\epsilon \\big)
\\]

## Total objective

\\[
\\mathcal{L} = \\mathcal{L}_{CE} + \\lambda \\mathcal{L}_{couple} + \\mu \\mathcal{L}_{conf}
\\]

where \\(\\mathcal{L}_{conf}\\) penalizes over-confidence below human review threshold \\(\\tau=0.5\\).

## Gate decision

\\[
\\text{gate}(i,e,b,c) =
\\begin{cases}
\\text{reject} & (i,b) \\in \\text{forbidden} \\\\
\\text{review} & c < \\tau \\\\
\\text{pass} & \\text{otherwise}
\\end{cases}
\\]
""",
        },
        "docs: document triad loss and gating math",
    ),
    (
        {
            "docs/LABELING.md": """\
# Labeling Guide

## Triad labeling

Each clip receives **one** intent, **one** emotion, and **one** dominant behavior.

1. Watch full 3s clip at 0.5× if needed.
2. Select intent from `ethogram/intents.yaml`.
3. Select emotion valence/arousal bucket from `ethogram/emotions.yaml`.
4. Mark the most salient behavior from `ethogram/behaviors.yaml`.
5. If uncertain, set `needs_review=true` — do not guess.

## Anticipation labels

For forecast training, label the **next** expected triad 500ms ahead when motion onset is visible.

## Quality bar

- Inter-rater κ target: ≥ 0.75 on behavior axis.
- Forbidden triples (see coupling matrix) must never be submitted.
""",
        },
        "docs: add labeling guide",
    ),
    (
        {
            "docs/ROADMAP.md": """\
# AARFLingo Roadmap

## Phase 0 — Spec & ethogram (complete)
- Canonical intents, emotions, behaviors
- Coupling matrix + JSON schemas
- Gate library + fixtures

## Phase 1 — Capture & perceive
- Ingest CLI + clipper
- Perception pipeline (detect, pose, gaze proxies)
- Baseline recording scripts

## Phase 2 — Label & train
- Labeler review queue
- Forecast triad model + coupling loss
- Docker training image

## Phase 3 — Export & studio
- ONNX/CoreML artifact bridge
- aarf-studio desktop review
- CI smoke pipeline

## Phase 4 — Pocket & collar (next)
- aarf-pocket iOS CoreML
- On-device gate + intent dashboard
- See `PHASE2_COLLAR.md` for wearable path

## Phase 5 — Field validation
- 10-dog pilot, clinic partner
- Calibration per-dog baseline
- Ethics review board sign-off
""",
        },
        "docs: add condensed roadmap phases",
    ),
    (
        {
            "docs/PHASE2_COLLAR.md": """\
# Phase 2 Collar Integration

## Goal

Stream low-rate triad predictions from a wearable IMU + mic puck to aarf-pocket via BLE.

## Contract

- 1 Hz intent/emotion summary frames (CBOR)
- Clip upload on trigger (Wi-Fi)
- Baseline sync from `record-baseline.sh` output

## Safety

- No shock/vibrate actuation in v0
- Human-in-the-loop for any welfare alert
""",
        },
        "docs: outline phase-2 collar integration",
    ),
    (
        {
            "docs/ETHICS.md": """\
# Ethics

## Welfare first

AARFLingo is observational only. It does not automate punishment or restraint.

## Data

- Dog owners must opt in; clinic datasets require IRB or equivalent.
- Clips are stored encrypted; delete-on-request within 30 days.

## Bias

- Breeds and coat colors under-represented in training must be flagged in manifests.
- Low-confidence predictions default to human review, never automated action.

## Contact

security@deepiri.dev for vulnerability reports.
""",
        },
        "docs: add ethics policy",
    ),
    (
        {
            "infra/configs/default.yaml": """\
# Shared runtime defaults
project: aarflingo
version: "0.1.0"

paths:
  data_root: ./data
  artifacts_root: ./artifacts
  ethogram_root: ./ethogram

ingest:
  clip_seconds: 3.0
  pre_roll_seconds: 0.5
  sample_fps: 15

perception:
  min_dog_confidence: 0.4
  gaze_aversion_threshold: 0.6

forecast:
  review_confidence_threshold: 0.5
  coupling_loss_weight: 0.3
  batch_size: 32
  epochs: 10

gate:
  coupling_matrix: ethogram/coupling-matrix.json
""",
        },
        "infra: add default runtime config",
    ),
    (
        {
            "infra/docker/train.Dockerfile": """\
FROM python:3.11-slim

WORKDIR /workspace

RUN pip install --no-cache-dir poetry==1.8.3

COPY services/forecast/pyproject.toml services/forecast/poetry.lock* /workspace/services/forecast/
WORKDIR /workspace/services/forecast
RUN poetry config virtualenvs.create false \\
    && poetry install --no-interaction --no-ansi --no-root

COPY services/forecast /workspace/services/forecast
COPY ethogram /workspace/ethogram
COPY core /workspace/core
COPY infra/configs /workspace/infra/configs

ENV AARFLINGO_CONFIG=/workspace/infra/configs/default.yaml

ENTRYPOINT ["python", "-m", "app.cli", "train"]
""",
        },
        "infra: add forecast training Dockerfile",
    ),
    (
        {
            "services/ingest/pyproject.toml": """\
[tool.poetry]
name = "aarflingo-ingest"
version = "0.1.0"
description = "Clip capture and baseline recording for AARFLingo"
authors = ["Deepiri <dev@deepiri.dev>"]
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"

[tool.poetry.scripts]
aarflingo-ingest = "app.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",
            "services/ingest/app/__init__.py": '"""Ingest service package."""\n',
        },
        "feat(ingest): scaffold poetry package",
    ),
    (
        {
            "services/ingest/app/capture.py": '''\
"""Synthetic frame capture for dev / smoke tests."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Frame:
    index: int
    ts_ms: int
    pixels: bytes


def capture_frames(count: int = 10, interval_ms: int = 100) -> list[Frame]:
    frames: list[Frame] = []
    start = int(time.time() * 1000)
    for i in range(count):
        ts = start + i * interval_ms
        frames.append(Frame(index=i, ts_ms=ts, pixels=bytes([i % 256] * 16)))
    return frames
''',
        },
        "feat(ingest): add synthetic frame capture",
    ),
    (
        {
            "services/ingest/app/clipper.py": '''\
"""Clip windows around motion triggers."""
from __future__ import annotations

from dataclasses import dataclass

from app.capture import Frame


@dataclass
class Clip:
    start_ms: int
    end_ms: int
    frames: list[Frame]


def clip_around_trigger(
    frames: list[Frame],
    trigger_ms: int,
    pre_roll_ms: int = 500,
    clip_ms: int = 3000,
) -> Clip:
    start = trigger_ms - pre_roll_ms
    end = trigger_ms + clip_ms
    selected = [f for f in frames if start <= f.ts_ms <= end]
    if not selected:
        selected = frames[:1]
    return Clip(start_ms=start, end_ms=end, frames=selected)
''',
        },
        "feat(ingest): add clip windowing",
    ),
    (
        {
            "services/ingest/app/baseline.py": '''\
"""Baseline metric aggregation for a dog session."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class BaselineMetrics:
    resting_heart_rate_bpm: float
    tail_angle_mean_deg: float
    gaze_aversion_mean: float = 0.2
    arousal_index: float = 0.15


@dataclass
class Baseline:
    baseline_id: str
    dog_id: str
    captured_at: str
    metrics: BaselineMetrics

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def record_baseline(dog_id: str, hr_bpm: float, tail_deg: float) -> Baseline:
    return Baseline(
        baseline_id=str(uuid.uuid4()),
        dog_id=dog_id,
        captured_at=datetime.now(timezone.utc).isoformat(),
        metrics=BaselineMetrics(
            resting_heart_rate_bpm=hr_bpm,
            tail_angle_mean_deg=tail_deg,
        ),
    )
''',
        },
        "feat(ingest): add baseline recording",
    ),
    (
        {
            "services/ingest/app/cli.py": '''\
"""Typer CLI for ingest service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from app.baseline import record_baseline
from app.capture import capture_frames
from app.clipper import clip_around_trigger

app = typer.Typer(help="AARFLingo ingest CLI")


@app.command()
def capture(out: Path = typer.Option(Path("data/clips/last.json"), help="Output JSON")) -> None:
    frames = capture_frames()
    trigger = frames[len(frames) // 2].ts_ms
    clip = clip_around_trigger(frames, trigger)
    payload = {
        "start_ms": clip.start_ms,
        "end_ms": clip.end_ms,
        "frame_count": len(clip.frames),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    typer.echo(f"wrote {out}")


@app.command()
def baseline(dog_id: str, hr: float = 80.0, tail: float = 35.0) -> None:
    b = record_baseline(dog_id, hr, tail)
    typer.echo(b.to_json())


if __name__ == "__main__":
    app()
''',
        },
        "feat(ingest): add typer CLI",
    ),
    (
        {
            "services/ingest/tests/test_clipper.py": '''\
from app.capture import capture_frames
from app.clipper import clip_around_trigger


def test_clip_selects_window() -> None:
    frames = capture_frames(count=30, interval_ms=100)
    trigger = frames[15].ts_ms
    clip = clip_around_trigger(frames, trigger, pre_roll_ms=200, clip_ms=500)
    assert clip.frames
    assert clip.start_ms <= clip.frames[0].ts_ms
    assert clip.frames[-1].ts_ms <= clip.end_ms
''',
        },
        "test(ingest): add clipper unit test",
    ),
    (
        {
            "services/labeler/pyproject.toml": """\
[tool.poetry]
name = "aarflingo-labeler"
version = "0.1.0"
description = "Human review and anticipation labeling"
authors = ["Deepiri <dev@deepiri.dev>"]
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"

[tool.poetry.scripts]
aarflingo-labeler = "app.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",
            "services/labeler/app/__init__.py": '"""Labeler service package."""\n',
        },
        "feat(labeler): scaffold poetry package",
    ),
    (
        {
            "services/labeler/app/review.py": '''\
"""Review queue for low-confidence triad predictions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReviewItem:
    event_id: str
    prediction: dict
    reason: str


def needs_review(prediction: dict, threshold: float = 0.5) -> bool:
    return float(prediction.get("confidence", 0.0)) < threshold


def enqueue(event_id: str, prediction: dict, threshold: float = 0.5) -> ReviewItem | None:
    if not needs_review(prediction, threshold):
        return None
    return ReviewItem(event_id=event_id, prediction=prediction, reason="low_confidence")
''',
        },
        "feat(labeler): add review queue helpers",
    ),
    (
        {
            "services/labeler/app/anticipate.py": '''\
"""Anticipation label utilities (next-triad targets)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnticipationLabel:
    current_ts_ms: int
    horizon_ms: int
    target_intent: str
    target_emotion: str
    target_behavior: str


def build_anticipation(
    current_ts_ms: int,
    intent: str,
    emotion: str,
    behavior: str,
    horizon_ms: int = 500,
) -> AnticipationLabel:
    return AnticipationLabel(
        current_ts_ms=current_ts_ms,
        horizon_ms=horizon_ms,
        target_intent=intent,
        target_emotion=emotion,
        target_behavior=behavior,
    )
''',
        },
        "feat(labeler): add anticipation label builder",
    ),
    (
        {
            "services/labeler/app/cli.py": '''\
"""Typer CLI for labeler service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from app.anticipate import build_anticipation
from app.review import enqueue

app = typer.Typer(help="AARFLingo labeler CLI")


@app.command()
def review(
    event_id: str,
    prediction_json: str = typer.Option(..., help="JSON triad prediction"),
    threshold: float = 0.5,
) -> None:
    prediction = json.loads(prediction_json)
    item = enqueue(event_id, prediction, threshold)
    if item is None:
        typer.echo("ok: no review needed")
        raise typer.Exit(0)
    typer.echo(json.dumps({"event_id": item.event_id, "reason": item.reason}))


@app.command()
def anticipate(intent: str, emotion: str, behavior: str, ts: int = 0) -> None:
    label = build_anticipation(ts, intent, emotion, behavior)
    typer.echo(json.dumps(label.__dict__))


if __name__ == "__main__":
    app()
''',
        },
        "feat(labeler): add typer CLI",
    ),
    (
        {
            "services/perception/pyproject.toml": """\
[tool.poetry]
name = "aarflingo-perception"
version = "0.1.0"
description = "Vision perception pipeline for AARFLingo"
authors = ["Deepiri <dev@deepiri.dev>"]
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"

[tool.poetry.scripts]
aarflingo-perception = "app.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",
            "services/perception/app/__init__.py": '"""Perception service package."""\n',
        },
        "feat(perception): scaffold poetry package",
    ),
    (
        {
            "services/perception/app/dog_detect.py": '''\
"""Minimal dog detection stub using luminance threshold."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float
    confidence: float


def detect_dog(frame_bytes: bytes, width: int = 64, height: int = 64) -> BBox | None:
    if not frame_bytes:
        return None
    mean_val = sum(frame_bytes) / len(frame_bytes) / 255.0
    if mean_val < 0.05:
        return None
    return BBox(x=0.2, y=0.15, w=0.5, h=0.7, confidence=min(0.99, mean_val + 0.3))
''',
        },
        "feat(perception): add dog detection stub",
    ),
    (
        {
            "services/perception/app/pose.py": '''\
"""Pose keypoint proxy from bbox geometry."""
from __future__ import annotations

from dataclasses import dataclass

from app.dog_detect import BBox


@dataclass
class Pose:
    tail_base: tuple[float, float]
    neck: tuple[float, float]
    nose: tuple[float, float]


def estimate_pose(bbox: BBox) -> Pose:
    cx = bbox.x + bbox.w / 2
    return Pose(
        tail_base=(bbox.x + 0.1, bbox.y + bbox.h * 0.5),
        neck=(cx, bbox.y + bbox.h * 0.35),
        nose=(bbox.x + bbox.w * 0.85, bbox.y + bbox.h * 0.25),
    )
''',
        },
        "feat(perception): add pose estimation proxy",
    ),
    (
        {
            "services/perception/app/gaze.py": '''\
"""Gaze aversion proxy from nose-neck vector."""
from __future__ import annotations

import math

from app.pose import Pose


def gaze_aversion(pose: Pose) -> float:
    nx, ny = pose.nose
    cx, cy = pose.neck
    dx = nx - cx
    dy = ny - cy
    angle = abs(math.atan2(dy, dx))
    return min(1.0, angle / math.pi)
''',
        },
        "feat(perception): add gaze aversion metric",
    ),
    (
        {
            "services/perception/app/face.py": '''\
"""Face region heuristics for stress signals."""
from __future__ import annotations

from dataclasses import dataclass

from app.pose import Pose


@dataclass
class FaceSignals:
    whale_eye_likelihood: float
    lip_lick_likelihood: float


def estimate_face_signals(pose: Pose, arousal_proxy: float = 0.3) -> FaceSignals:
    return FaceSignals(
        whale_eye_likelihood=min(1.0, arousal_proxy * 0.8),
        lip_lick_likelihood=min(1.0, arousal_proxy * 0.5),
    )
''',
        },
        "feat(perception): add face signal heuristics",
    ),
    (
        {
            "services/perception/app/scene.py": '''\
"""Scene context tags from simple statistics."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SceneContext:
    indoor: bool
    motion_level: float
    tags: list[str]


def classify_scene(frame_bytes: bytes) -> SceneContext:
    mean_val = sum(frame_bytes) / max(len(frame_bytes), 1) / 255.0
    indoor = mean_val < 0.6
    motion = min(1.0, mean_val)
    tags = ["indoor"] if indoor else ["outdoor"]
    if motion > 0.5:
        tags.append("active")
    return SceneContext(indoor=indoor, motion_level=motion, tags=tags)
''',
        },
        "feat(perception): add scene classifier stub",
    ),
    (
        {
            "services/perception/app/pipeline.py": '''\
"""Compose perception modules into a feature dict."""
from __future__ import annotations

from app.dog_detect import detect_dog
from app.face import estimate_face_signals
from app.gaze import gaze_aversion
from app.pose import estimate_pose
from app.scene import classify_scene


def run_pipeline(frame_bytes: bytes) -> dict:
    scene = classify_scene(frame_bytes)
    bbox = detect_dog(frame_bytes)
    if bbox is None:
        return {"dog_present": False, "scene": scene.tags}
    pose = estimate_pose(bbox)
    ga = gaze_aversion(pose)
    face = estimate_face_signals(pose, arousal_proxy=scene.motion_level)
    return {
        "dog_present": True,
        "bbox": bbox.__dict__,
        "gaze_aversion": ga,
        "whale_eye_likelihood": face.whale_eye_likelihood,
        "lip_lick_likelihood": face.lip_lick_likelihood,
        "scene": scene.tags,
    }
''',
        },
        "feat(perception): wire perception pipeline",
    ),
    (
        {
            "services/perception/tests/test_gaze.py": '''\
from app.dog_detect import BBox
from app.gaze import gaze_aversion
from app.pose import estimate_pose


def test_gaze_aversion_in_range() -> None:
    bbox = BBox(x=0.2, y=0.1, w=0.5, h=0.6, confidence=0.9)
    pose = estimate_pose(bbox)
    score = gaze_aversion(pose)
    assert 0.0 <= score <= 1.0
''',
        },
        "test(perception): add gaze unit test",
    ),
    (
        {
            "services/forecast/pyproject.toml": """\
[tool.poetry]
name = "aarflingo-forecast"
version = "0.1.0"
description = "Triad forecast model training and inference"
authors = ["Deepiri <dev@deepiri.dev>"]
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"

[tool.poetry.scripts]
aarflingo-forecast = "app.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",
            "services/forecast/app/__init__.py": '"""Forecast service package."""\n',
        },
        "feat(forecast): scaffold poetry package",
    ),
    (
        {
            "services/forecast/app/dataset.py": '''\
"""In-memory triad dataset from feature dicts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TriadSample:
    features: dict
    intent_id: str
    emotion_id: str
    behavior_id: str


def load_demo_dataset() -> list[TriadSample]:
    return [
        TriadSample(
            features={"gaze_aversion": 0.2, "motion": 0.7},
            intent_id="solicit_play",
            emotion_id="excited",
            behavior_id="play_bow",
        ),
        TriadSample(
            features={"gaze_aversion": 0.8, "motion": 0.3},
            intent_id="avoid",
            emotion_id="fearful",
            behavior_id="tail_tucked",
        ),
    ]
''',
        },
        "feat(forecast): add demo dataset loader",
    ),
    (
        {
            "services/forecast/app/triad_model.py": '''\
"""Minimal triad classifier (rule-based for smoke tests)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TriadPrediction:
    intent_id: str
    emotion_id: str
    behavior_id: str
    confidence: float


def predict(features: dict) -> TriadPrediction:
    ga = float(features.get("gaze_aversion", 0.0))
    motion = float(features.get("motion", 0.0))
    if ga > 0.6:
        return TriadPrediction("avoid", "fearful", "tail_tucked", 0.7)
    if motion > 0.5:
        return TriadPrediction("solicit_play", "excited", "play_bow", 0.75)
    return TriadPrediction("rest", "calm", "yawning", 0.55)
''',
        },
        "feat(forecast): add rule-based triad model",
    ),
    (
        {
            "services/forecast/app/losses.py": '''\
"""Coupling-aware loss helpers."""
from __future__ import annotations

import math


def coupling_loss(weight: float, epsilon: float = 1e-6) -> float:
    if weight <= 0:
        return 10.0
    return -math.log(weight + epsilon)


def confidence_penalty(confidence: float, threshold: float = 0.5) -> float:
    if confidence >= threshold:
        return 0.0
    return (threshold - confidence) ** 2


def total_loss(ce: float, couple_w: float, conf: float, lam: float = 0.3, mu: float = 0.1) -> float:
    return ce + lam * coupling_loss(couple_w) + mu * confidence_penalty(conf)
''',
        },
        "feat(forecast): add coupling loss functions",
    ),
    (
        {
            "services/forecast/app/train.py": '''\
"""Training loop stub over demo dataset."""
from __future__ import annotations

from app.dataset import load_demo_dataset
from app.losses import total_loss
from app.triad_model import predict


def train_epoch() -> float:
    samples = load_demo_dataset()
    losses: list[float] = []
    for sample in samples:
        pred = predict(sample.features)
        ce = 0.0 if pred.intent_id == sample.intent_id else 1.0
        couple_w = 0.9 if pred.behavior_id == sample.behavior_id else 0.1
        losses.append(total_loss(ce, couple_w, pred.confidence))
    return sum(losses) / len(losses)
''',
        },
        "feat(forecast): add training epoch stub",
    ),
    (
        {
            "services/forecast/app/infer.py": '''\
"""Batch inference helper."""
from __future__ import annotations

from app.triad_model import TriadPrediction, predict


def infer_batch(feature_rows: list[dict]) -> list[TriadPrediction]:
    return [predict(row) for row in feature_rows]
''',
        },
        "feat(forecast): add inference helper",
    ),
    (
        {
            "services/forecast/app/cli.py": '''\
"""Typer CLI for forecast service."""
from __future__ import annotations

import json

import typer

from app.infer import infer_batch
from app.train import train_epoch

app = typer.Typer(help="AARFLingo forecast CLI")


@app.command()
def train() -> None:
    loss = train_epoch()
    typer.echo(json.dumps({"loss": loss}))


@app.command()
def infer(features_json: str) -> None:
    rows = json.loads(features_json)
    preds = infer_batch(rows)
    typer.echo(json.dumps([p.__dict__ for p in preds]))


if __name__ == "__main__":
    app()
''',
        },
        "feat(forecast): add typer CLI",
    ),
    (
        {
            "services/forecast/tests/test_losses.py": '''\
from app.losses import coupling_loss, total_loss


def test_coupling_loss_positive_weight() -> None:
    assert coupling_loss(0.9) < coupling_loss(0.1)


def test_total_loss_adds_terms() -> None:
    loss = total_loss(ce=0.5, couple_w=0.8, conf=0.4)
    assert loss > 0.5
''',
        },
        "test(forecast): add loss unit tests",
    ),
    (
        {
            "services/artifact-bridge/pyproject.toml": """\
[tool.poetry]
name = "aarflingo-artifact-bridge"
version = "0.1.0"
description = "Export ONNX/CoreML artifacts and manifests"
authors = ["Deepiri <dev@deepiri.dev>"]
packages = [{ include = "app" }]

[tool.poetry.dependencies]
python = "^3.11"
typer = "^0.12.0"

[tool.poetry.scripts]
aarflingo-artifact-bridge = "app.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""",
            "services/artifact-bridge/app/__init__.py": '"""Artifact bridge package."""\n',
        },
        "feat(artifact-bridge): scaffold poetry package",
    ),
    (
        {
            "services/artifact-bridge/app/export_onnx.py": '''\
"""Write a minimal ONNX placeholder bundle marker."""
from __future__ import annotations

import json
from pathlib import Path


def export_onnx(out_dir: Path, model_name: str = "triad") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    marker = out_dir / f"{model_name}.onnx.json"
    marker.write_text(
        json.dumps({"format": "onnx-placeholder", "model": model_name, "opset": 17}),
        encoding="utf-8",
    )
    return marker
''',
        },
        "feat(artifact-bridge): add ONNX export placeholder",
    ),
    (
        {
            "services/artifact-bridge/app/export_coreml.py": '''\
"""Write a minimal CoreML placeholder bundle marker."""
from __future__ import annotations

import json
from pathlib import Path


def export_coreml(out_dir: Path, model_name: str = "triad") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    marker = out_dir / f"{model_name}.mlmodel.json"
    marker.write_text(
        json.dumps({"format": "coreml-placeholder", "model": model_name}),
        encoding="utf-8",
    )
    return marker
''',
        },
        "feat(artifact-bridge): add CoreML export placeholder",
    ),
    (
        {
            "services/artifact-bridge/app/manifest.py": '''\
"""Signed manifest for artifact bundles."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Manifest:
    bundle_id: str
    created_at: str
    artifacts: list[str]
    sha256: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def build_manifest(bundle_dir: Path) -> Manifest:
    files = sorted(p.name for p in bundle_dir.iterdir() if p.is_file())
    digest = hashlib.sha256("|".join(files).encode()).hexdigest()
    return Manifest(
        bundle_id=bundle_dir.name,
        created_at=datetime.now(timezone.utc).isoformat(),
        artifacts=files,
        sha256=digest,
    )
''',
        },
        "feat(artifact-bridge): add bundle manifest builder",
    ),
    (
        {
            "services/artifact-bridge/app/cli.py": '''\
"""Typer CLI for artifact bridge."""
from __future__ import annotations

from pathlib import Path

import typer

from app.export_coreml import export_coreml
from app.export_onnx import export_onnx
from app.manifest import build_manifest

app = typer.Typer(help="AARFLingo artifact bridge CLI")


@app.command()
def export(
    out: Path = Path("artifacts/bundles/dev"),
    target: str = typer.Option("onnx", help="onnx or coreml"),
) -> None:
    if target == "coreml":
        path = export_coreml(out)
    else:
        path = export_onnx(out)
    manifest = build_manifest(out)
    (out / "manifest.json").write_text(manifest.to_json(), encoding="utf-8")
    typer.echo(f"exported {path}")


if __name__ == "__main__":
    app()
''',
        },
        "feat(artifact-bridge): add typer CLI",
    ),
    (
        {
            "lib/aarf-gate/package.json": """\
{
  "name": "@deepiri/aarf-gate",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "vitest run"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vitest": "^1.6.0"
  }
}
""",
        },
        "feat(aarf-gate): add package.json",
    ),
    (
        {
            "lib/aarf-gate/tsconfig.json": """\
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "declaration": true,
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
""",
        },
        "feat(aarf-gate): add tsconfig",
    ),
    (
        {
            "lib/aarf-gate/src/types.ts": """\
export interface TriadPrediction {
  intent_id: string;
  emotion_id: string;
  behavior_id: string;
  confidence: number;
  ts_ms: number;
}

export interface CouplingTriple {
  intent: string;
  emotion: string;
  behavior: string;
  weight: number;
}

export interface ForbiddenPair {
  intent?: string;
  emotion?: string;
  behavior?: string;
}

export interface CouplingMatrix {
  version: string;
  triples: CouplingTriple[];
  forbidden_pairs: ForbiddenPair[];
}

export type GateDecision = "pass" | "review" | "reject";
""",
        },
        "feat(aarf-gate): add TypeScript types",
    ),
    (
        {
            "lib/aarf-gate/src/gate.ts": """\
import type { CouplingMatrix, ForbiddenPair, GateDecision, TriadPrediction } from "./types.js";

export function isForbidden(
  prediction: TriadPrediction,
  forbidden: ForbiddenPair[],
): boolean {
  return forbidden.some((rule) => {
    const intentOk = rule.intent === undefined || rule.intent === prediction.intent_id;
    const emotionOk = rule.emotion === undefined || rule.emotion === prediction.emotion_id;
    const behaviorOk = rule.behavior === undefined || rule.behavior === prediction.behavior_id;
    return intentOk && emotionOk && behaviorOk;
  });
}

export function couplingWeight(
  prediction: TriadPrediction,
  matrix: CouplingMatrix,
): number {
  const hit = matrix.triples.find(
    (t) =>
      t.intent === prediction.intent_id &&
      t.emotion === prediction.emotion_id &&
      t.behavior === prediction.behavior_id,
  );
  return hit?.weight ?? 0;
}

export function gatePrediction(
  prediction: TriadPrediction,
  matrix: CouplingMatrix,
  reviewThreshold = 0.5,
): GateDecision {
  if (isForbidden(prediction, matrix.forbidden_pairs)) {
    return "reject";
  }
  if (prediction.confidence < reviewThreshold) {
    return "review";
  }
  if (couplingWeight(prediction, matrix) <= 0) {
    return "review";
  }
  return "pass";
}
""",
        },
        "feat(aarf-gate): implement ethogram coupling gate",
    ),
    (
        {
            "lib/aarf-gate/src/metrics.ts": """\
import type { GateDecision } from "./types.js";

export function summarizeDecisions(decisions: GateDecision[]): Record<GateDecision, number> {
  return decisions.reduce(
    (acc, d) => {
      acc[d] += 1;
      return acc;
    },
    { pass: 0, review: 0, reject: 0 } as Record<GateDecision, number>,
  );
}
""",
        },
        "feat(aarf-gate): add gate metrics helper",
    ),
    (
        {
            "lib/aarf-gate/src/index.ts": """\
export * from "./types.js";
export * from "./gate.js";
export * from "./metrics.js";
""",
        },
        "feat(aarf-gate): add package entrypoint",
    ),
    (
        {
            "lib/aarf-gate/vitest.config.ts": """\
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
  },
});
""",
        },
        "test(aarf-gate): add vitest config",
    ),
    (
        {
            "lib/aarf-gate/tests/gate.test.ts": """\
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { gatePrediction } from "../src/gate.js";
import type { CouplingMatrix, TriadPrediction } from "../src/types.js";

const matrix = JSON.parse(
  readFileSync(resolve(__dirname, "../../../ethogram/coupling-matrix.json"), "utf-8"),
) as CouplingMatrix;

describe("gatePrediction", () => {
  it("passes valid play bow triple", () => {
    const pred: TriadPrediction = {
      intent_id: "solicit_play",
      emotion_id: "excited",
      behavior_id: "play_bow",
      confidence: 0.9,
      ts_ms: 1,
    };
    expect(gatePrediction(pred, matrix)).toBe("pass");
  });

  it("rejects forbidden rest + play_bow", () => {
    const pred: TriadPrediction = {
      intent_id: "rest",
      emotion_id: "calm",
      behavior_id: "play_bow",
      confidence: 0.9,
      ts_ms: 2,
    };
    expect(gatePrediction(pred, matrix)).toBe("reject");
  });
});
""",
        },
        "test(aarf-gate): add coupling gate tests",
    ),
    (
        {
            "apps/aarf-studio/package.json": """\
{
  "name": "aarf-studio",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.0",
    "vite": "^5.4.0"
  }
}
""",
        },
        "feat(aarf-studio): add package.json",
    ),
    (
        {
            "apps/aarf-studio/vite.config.ts": """\
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  root: ".",
  build: {
    outDir: "dist",
  },
});
""",
        },
        "feat(aarf-studio): add vite config",
    ),
    (
        {
            "apps/aarf-studio/index.html": """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AARF Studio</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/renderer/main.tsx"></script>
  </body>
</html>
""",
        },
        "feat(aarf-studio): add index.html shell",
    ),
    (
        {
            "apps/aarf-studio/src/main/main.ts": """\
// Electron main process placeholder — studio runs as Vite web shell in dev.
export const STUDIO_APP_NAME = "AARF Studio";
""",
            "apps/aarf-studio/src/main/preload.ts": """\
// Preload bridge placeholder for future Electron APIs.
export const api = {
  version: "0.1.0",
};
""",
        },
        "feat(aarf-studio): add electron main/preload stubs",
    ),
    (
        {
            "apps/aarf-studio/src/renderer/main.tsx": """\
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(<App />);
}
""",
        },
        "feat(aarf-studio): add renderer entry",
    ),
    (
        {
            "apps/aarf-studio/src/renderer/App.tsx": """\
import React, { useState } from "react";
import { CameraView } from "./components/CameraView";
import { HistoryView } from "./components/HistoryView";
import { IntentDashboard } from "./components/IntentDashboard";

export function App() {
  const [tab, setTab] = useState<"dashboard" | "camera" | "history">("dashboard");

  return (
    <div className="app">
      <header>
        <h1>AARF Studio</h1>
        <nav>
          <button onClick={() => setTab("dashboard")}>Dashboard</button>
          <button onClick={() => setTab("camera")}>Camera</button>
          <button onClick={() => setTab("history")}>History</button>
        </nav>
      </header>
      <main>
        {tab === "dashboard" && <IntentDashboard />}
        {tab === "camera" && <CameraView />}
        {tab === "history" && <HistoryView />}
      </main>
    </div>
  );
}
""",
        },
        "feat(aarf-studio): add App shell with tabs",
    ),
    (
        {
            "apps/aarf-studio/src/renderer/components/IntentDashboard.tsx": """\
import React from "react";

const DEMO = {
  intent: "solicit_play",
  emotion: "excited",
  behavior: "play_bow",
  confidence: 0.88,
  gate: "pass",
};

export function IntentDashboard() {
  return (
    <section className="card">
      <h2>Intent dashboard</h2>
      <dl>
        <dt>Intent</dt>
        <dd>{DEMO.intent}</dd>
        <dt>Emotion</dt>
        <dd>{DEMO.emotion}</dd>
        <dt>Behavior</dt>
        <dd>{DEMO.behavior}</dd>
        <dt>Confidence</dt>
        <dd>{(DEMO.confidence * 100).toFixed(0)}%</dd>
        <dt>Gate</dt>
        <dd className={`gate-${DEMO.gate}`}>{DEMO.gate}</dd>
      </dl>
    </section>
  );
}
""",
        },
        "feat(aarf-studio): add IntentDashboard component",
    ),
    (
        {
            "apps/aarf-studio/src/renderer/components/CameraView.tsx": """\
import React from "react";

export function CameraView() {
  return (
    <section className="card">
      <h2>Camera</h2>
      <p>Connect capture device or load clip JSON from ingest.</p>
      <div className="camera-placeholder">No signal</div>
    </section>
  );
}
""",
        },
        "feat(aarf-studio): add CameraView component",
    ),
    (
        {
            "apps/aarf-studio/src/renderer/components/HistoryView.tsx": """\
import React from "react";

const EVENTS = [
  { id: "evt-1", intent: "explore", confidence: 0.62 },
  { id: "evt-2", intent: "rest", confidence: 0.71 },
];

export function HistoryView() {
  return (
    <section className="card">
      <h2>History</h2>
      <ul>
        {EVENTS.map((e) => (
          <li key={e.id}>
            {e.id}: {e.intent} ({(e.confidence * 100).toFixed(0)}%)
          </li>
        ))}
      </ul>
    </section>
  );
}
""",
        },
        "feat(aarf-studio): add HistoryView component",
    ),
    (
        {
            "apps/aarf-studio/src/renderer/styles.css": """\
body {
  font-family: system-ui, sans-serif;
  margin: 0;
  background: #0f1419;
  color: #e7ecf3;
}

.app header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #2a3441;
}

nav button {
  margin-right: 0.5rem;
  background: #1c2530;
  color: inherit;
  border: 1px solid #3a4a5c;
  padding: 0.4rem 0.8rem;
  cursor: pointer;
}

main {
  padding: 1rem;
}

.card {
  background: #151c24;
  border-radius: 8px;
  padding: 1rem;
  max-width: 480px;
}

.gate-pass {
  color: #3dd68c;
}

.camera-placeholder {
  height: 180px;
  background: #0a0e12;
  display: grid;
  place-items: center;
  border: 1px dashed #3a4a5c;
}
""",
        },
        "feat(aarf-studio): add base styles",
    ),
    (
        {
            "apps/aarf-pocket/AARFPocket/App.swift": """\
import SwiftUI

@main
struct AARFPocketApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
""",
        },
        "feat(aarf-pocket): add SwiftUI app entry",
    ),
    (
        {
            "apps/aarf-pocket/AARFPocket/ContentView.swift": """\
import SwiftUI

struct ContentView: View {
    @StateObject private var vm = IntentViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Text("AARF Pocket")
                    .font(.title2)
                Label(vm.intent, systemImage: "pawprint")
                Text("Emotion: \\(vm.emotion)")
                Text("Behavior: \\(vm.behavior)")
                Text(String(format: "Confidence: %.0f%%", vm.confidence * 100))
                Text("Gate: \\(vm.gateStatus)")
                    .foregroundStyle(vm.gateStatus == "pass" ? .green : .orange)
                Button("Run inference") {
                    vm.runInference()
                }
            }
            .padding()
        }
    }
}

#Preview {
    ContentView()
}
""",
        },
        "feat(aarf-pocket): add ContentView",
    ),
    (
        {
            "apps/aarf-pocket/AARFPocket/IntentViewModel.swift": """\
import Foundation

@MainActor
final class IntentViewModel: ObservableObject {
    @Published var intent: String = "rest"
    @Published var emotion: String = "calm"
    @Published var behavior: String = "yawning"
    @Published var confidence: Double = 0.55
    @Published var gateStatus: String = "review"

    private let coreML = CoreMLService()

    func runInference() {
        let result = coreML.predict(features: ["gaze_aversion": 0.2, "motion": 0.8])
        intent = result.intent
        emotion = result.emotion
        behavior = result.behavior
        confidence = result.confidence
        gateStatus = confidence >= 0.5 ? "pass" : "review"
    }
}
""",
        },
        "feat(aarf-pocket): add IntentViewModel",
    ),
    (
        {
            "apps/aarf-pocket/AARFPocket/CoreMLService.swift": """\
import Foundation

struct TriadResult {
    let intent: String
    let emotion: String
    let behavior: String
    let confidence: Double
}

struct CoreMLService {
    func predict(features: [String: Double]) -> TriadResult {
        let motion = features["motion"] ?? 0
        if motion > 0.5 {
            return TriadResult(intent: "solicit_play", emotion: "excited", behavior: "play_bow", confidence: 0.82)
        }
        return TriadResult(intent: "rest", emotion: "calm", behavior: "yawning", confidence: 0.58)
    }
}
""",
        },
        "feat(aarf-pocket): add CoreMLService stub",
    ),
    (
        {
            "apps/aarf-pocket/AARFPocket/Info.plist": """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>AARFPocket</string>
    <key>CFBundleIdentifier</key>
    <string>dev.deepiri.aarfpocket</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>UILaunchScreen</key>
    <dict/>
</dict>
</plist>
""",
        },
        "feat(aarf-pocket): add Info.plist",
    ),
    (
        {
            "scripts/setup.sh": """\
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Python services"
for svc in ingest labeler perception forecast artifact-bridge; do
  if command -v poetry >/dev/null 2>&1; then
    (cd "services/$svc" && poetry install --no-interaction)
  else
    echo "poetry not found; pip install typer in each service manually"
  fi
done

echo "==> aarf-gate"
if command -v npm >/dev/null 2>&1; then
  (cd lib/aarf-gate && npm install && npm run build)
fi

echo "==> aarf-studio"
if command -v npm >/dev/null 2>&1; then
  (cd apps/aarf-studio && npm install)
fi

echo "setup complete"
""",
        },
        "chore(scripts): add setup.sh",
    ),
    (
        {
            "scripts/record-baseline.sh": """\
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOG_ID="${1:-dog-demo}"
HR="${2:-80}"
TAIL="${3:-35}"
cd "$ROOT/services/ingest"
if command -v poetry >/dev/null 2>&1; then
  poetry run aarflingo-ingest baseline "$DOG_ID" --hr "$HR" --tail "$TAIL"
else
  PYTHONPATH=. python -m app.cli baseline "$DOG_ID" --hr "$HR" --tail "$TAIL"
fi
""",
        },
        "chore(scripts): add record-baseline.sh",
    ),
    (
        {
            "scripts/smoke_pipeline.sh": """\
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> core metrics"
python core/metrics/test_anticipate.py

echo "==> ingest capture"
cd services/ingest
PYTHONPATH=. python -m app.cli capture --out /tmp/aarf_clip.json
cat /tmp/aarf_clip.json

echo "==> perception pipeline"
cd "$ROOT/services/perception"
PYTHONPATH=. python -c "from app.pipeline import run_pipeline; print(run_pipeline(bytes([128]*64)))"

echo "==> forecast train"
cd "$ROOT/services/forecast"
PYTHONPATH=. python -m app.cli train

echo "smoke ok"
""",
        },
        "chore(scripts): add smoke_pipeline.sh",
    ),
    (
        {
            "scripts/demo_protocol.sh": """\
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

./scripts/setup.sh
./scripts/record-baseline.sh dog-demo 78 32
./scripts/smoke_pipeline.sh

echo "Demo protocol complete — open apps/aarf-studio with npm run dev"
""",
        },
        "chore(scripts): add demo_protocol.sh",
    ),
    (
        {
            ".github/workflows/ci.yml": """\
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  python:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [ingest, perception, forecast]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: pip install typer pytest
      - name: Unit tests
        working-directory: services/${{ matrix.service }}
        run: |
          if [ -d tests ]; then PYTHONPATH=. pytest -q; fi

  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Test aarf-gate
        working-directory: lib/aarf-gate
        run: |
          npm install
          npm test
""",
        },
        "ci: add GitHub Actions workflow",
    ),
    (
        {
            "artifacts/manifests/.gitkeep": "",
            "artifacts/bundles/.gitkeep": "",
        },
        "chore: add artifacts directory placeholders",
    ),
]

assert len(ALL_COMMITS) >= 55, f"expected >= 55 commits, got {len(ALL_COMMITS)}"

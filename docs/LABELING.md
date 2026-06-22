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

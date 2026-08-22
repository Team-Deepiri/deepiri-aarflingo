# RESULTS (generated — do not hand-edit)

Regenerate: `python3 scripts/v1_gate.py`.

The v1.0 accuracy bar is **dog-held-out** intent accuracy ≥ 0.95 on ≥ 3 dogs.
Numbers below that are context only and do **not** count.

| Metric | Value | Split | Counts toward v1.0? |
|--------|------:|-------|---------------------|
| Home dog-split accuracy | — | dog-held-out | yes |
| Home dog-split macro-F1 | — | dog-held-out | yes |
| Home dogs / rows | 0 / 0 | dog-held-out | yes |
| Triad best_val_acc | 1.0 | synthetic-or-unknown | no |
| Vocal best_val_acc | 0.18333333333333332 | mixed-or-unknown | no |

**bar_met:** `False`

## Blockers

- home dog-split eval missing or below 95% with ≥3 dogs (write data/dog/eval/dog_split.jsonl)

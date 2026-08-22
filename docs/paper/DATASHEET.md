# DATASHEET

## Motivation

Home canine intent forecasting for owners and researchers. Not a shock collar.

## Composition

| Corpus | Role | Split rule |
|--------|------|------------|
| Home sessions | v1.0 bar | by `dog_id` |
| Stanford Dogs | breed pre-train | public photo set |
| Barkopedia | vocal pre-train | clip-level, not dog-level |
| Synthetic triad rows | smoke / CI | do not report as field acc |

Home rows live in `data/dog/eval/dog_split.jsonl` once labeled:

```json
{"dog_id":"ada","y_true":"play","y_pred":"play","ts_ms":0}
```

## Collection

Owner opt-in. Clinic data needs IRB or equivalent. Delete-on-request in 30 days ([ETHICS.md](../ETHICS.md)).

## Known gaps

- N dogs in the home eval is currently 0
- Breed under-representation is not yet flagged per-manifest
- No inter-rater κ logged yet (target ≥ 0.75 on behavior)

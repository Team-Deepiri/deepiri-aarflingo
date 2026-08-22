# Dog-held-out eval

Put labeled windows in `dog_split.jsonl`, one JSON object per line:

```json
{"dog_id":"ada","y_true":"play","y_pred":"play","ts_ms":1710000000000}
```

`y_true` / `y_pred` must be intent ids from `ethogram/`. Split by `dog_id`.
Score with `python3 scripts/v1_gate.py --require-bar`.

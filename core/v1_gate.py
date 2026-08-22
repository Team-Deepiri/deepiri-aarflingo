"""Honest v1.0 gate.

The 95% bar counts only a dog-held-out home eval (N≥3 dogs).
Synthetic triad val_acc, public-photo breed acc, and mixed vocal acc do not count.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ACCURACY_BAR = 0.95
MIN_DOGS = 3
PAPER_FILES = ("METHODS.md", "RESULTS.md", "DATASHEET.md", "reproduce.md", "PAPER.md", "aarflingo.tex")
EVAL_JSONL = Path("data/dog/eval/dog_split.jsonl")
MANIFEST = Path("artifacts/manifests/aarflingo-multimodal.json")
JETSON_DOCKER = Path("infra/docker/jetson.Dockerfile")


def _labels(rows: list[dict[str, Any]]) -> list[str]:
    found: set[str] = set()
    for row in rows:
        found.add(str(row.get("y_true", "")))
        found.add(str(row.get("y_pred", "")))
    found.discard("")
    return sorted(found)


def dog_split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dogs = {str(r.get("dog_id", "")) for r in rows if r.get("dog_id")}
    collar_rows = sum(1 for r in rows if isinstance(r.get("collar"), dict))
    if not rows:
        return {
            "n_dogs": 0,
            "n_rows": 0,
            "collar_rows": 0,
            "accuracy": None,
            "macro_f1": None,
            "split": "dog-held-out",
        }
    correct = sum(1 for r in rows if r.get("y_true") == r.get("y_pred"))
    acc = correct / len(rows)
    labels = _labels(rows)
    f1s: list[float] = []
    for lab in labels:
        tp = sum(1 for r in rows if r.get("y_pred") == lab and r.get("y_true") == lab)
        fp = sum(1 for r in rows if r.get("y_pred") == lab and r.get("y_true") != lab)
        fn = sum(1 for r in rows if r.get("y_pred") != lab and r.get("y_true") == lab)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1s.append(0.0 if (prec + rec) == 0 else 2 * prec * rec / (prec + rec))
    return {
        "n_dogs": len(dogs),
        "n_rows": len(rows),
        "collar_rows": collar_rows,
        "accuracy": acc,
        "macro_f1": sum(f1s) / len(f1s) if f1s else 0.0,
        "split": "dog-held-out",
        "per_dog_n": {d: sum(1 for r in rows if str(r.get("dog_id")) == d) for d in sorted(dogs)},
    }


def meets_accuracy_bar(metrics: dict[str, Any]) -> bool:
    acc = metrics.get("accuracy")
    n_dogs = int(metrics.get("n_dogs") or 0)
    return acc is not None and n_dogs >= MIN_DOGS and float(acc) + 1e-12 >= ACCURACY_BAR


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(json.loads(line))
    return rows


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def paper_ready(root: Path) -> dict[str, Any]:
    paper = root / "docs" / "paper"
    present = [name for name in PAPER_FILES if (paper / name).is_file()]
    return {
        "dir": str(paper),
        "required": list(PAPER_FILES),
        "present": present,
        "ok": set(present) >= set(PAPER_FILES),
    }


def jetson_ready(root: Path) -> dict[str, Any]:
    path = root / JETSON_DOCKER
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    ok = bool(
        path.is_file()
        and "edge-runtime" in text
        and "l4t" in text.lower()
        and "app.cli" in text
    )
    return {
        "ok": ok,
        "path": str(path),
        "is_wearable": False,
        "role": "Jetson Orin-class home hub — not the ESP32 collar",
    }


def hardware_ready(root: Path) -> dict[str, Any]:
    pins = root / "firmware" / "collar" / "include" / "pins.h"
    product = root / "firmware" / "collar" / "include" / "product.h"
    nets = root / "scripts" / "aarf_sch" / "nets.py"
    bom = root / "hardware" / "collar-reva" / "BOM.csv"
    features = root / "core" / "collar_features.py"
    pins_txt = pins.read_text(encoding="utf-8") if pins.is_file() else ""
    product_txt = product.read_text(encoding="utf-8") if product.is_file() else ""
    nets_txt = nets.read_text(encoding="utf-8") if nets.is_file() else ""
    checks = {
        "pins_skin": "PIN_SKIN_SENSE" in pins_txt,
        "adv_name": "aarf-collar" in product_txt,
        "nets_skin": "SKIN_SENSE" in nets_txt,
        "board": 'BOARD = "collar-reva"' in nets_txt,
        "bom": bom.is_file(),
        "features": features.is_file(),
    }
    return {
        "ok": all(checks.values()),
        "board": "collar-reva",
        "checks": checks,
        "role": "ESP32-S3 puck — BLE CBOR into existing triad slots",
    }


def collect_report(root: Path) -> dict[str, Any]:
    manifest = _load_manifest(root)
    home = dog_split_metrics(_load_jsonl(root / EVAL_JSONL))
    triad_acc = (manifest.get("triad_train") or {}).get("best_val_acc")
    vocal_acc = (manifest.get("audio") or {}).get("best_val_acc")
    physio_acc = (manifest.get("physio") or {}).get("best_val_acc")
    paper = paper_ready(root)
    jetson = jetson_ready(root)
    hardware = hardware_ready(root)
    acc_ok = meets_accuracy_bar(home)
    blockers: list[str] = []
    if not acc_ok:
        blockers.append(
            f"home dog-split eval missing or below {ACCURACY_BAR:.0%} with ≥{MIN_DOGS} dogs "
            f"(write {EVAL_JSONL})"
        )
    if not paper["ok"]:
        missing = [n for n in PAPER_FILES if n not in paper["present"]]
        blockers.append(f"paper files missing: {', '.join(missing)}")
    if not jetson["ok"]:
        blockers.append("jetson.Dockerfile is not a working edge-runtime hub image")
    if not hardware["ok"]:
        missing = [k for k, v in hardware["checks"].items() if not v]
        blockers.append(f"Rev-A puck contract incomplete: {', '.join(missing)}")
    return {
        "bar": {
            "name": "v1.0",
            "accuracy_target": ACCURACY_BAR,
            "min_dogs": MIN_DOGS,
            "split": "dog-held-out",
        },
        "metrics": {
            "home_dog_split": {**home, "counts_toward_bar": True},
            "triad": {
                "best_val_acc": triad_acc,
                "split": "synthetic-or-unknown",
                "counts_toward_bar": False,
            },
            "vocal": {
                "best_val_acc": vocal_acc,
                "split": "mixed-or-unknown",
                "counts_toward_bar": False,
            },
            "physio": {
                "best_val_acc": physio_acc,
                "split": "synthetic-or-unknown",
                "counts_toward_bar": False,
            },
        },
        "paper": paper,
        "jetson": jetson,
        "hardware": hardware,
        "bar_met": acc_ok and paper["ok"] and jetson["ok"] and hardware["ok"],
        "blockers": blockers,
    }


def render_results_md(report: dict[str, Any]) -> str:
    home = report["metrics"]["home_dog_split"]
    acc = home.get("accuracy")
    acc_s = "—" if acc is None else f"{float(acc):.3f}"
    f1 = home.get("macro_f1")
    f1_s = "—" if f1 is None else f"{float(f1):.3f}"
    triad = report["metrics"]["triad"].get("best_val_acc")
    vocal = report["metrics"]["vocal"].get("best_val_acc")
    lines = [
        "# RESULTS (generated — do not hand-edit)",
        "",
        "Regenerate: `python3 scripts/v1_gate.py`.",
        "",
        "The v1.0 accuracy bar is **dog-held-out** intent accuracy ≥ 0.95 on ≥ 3 dogs.",
        "Numbers below that are context only and do **not** count.",
        "",
        "| Metric | Value | Split | Counts toward v1.0? |",
        "|--------|------:|-------|---------------------|",
        f"| Home dog-split accuracy | {acc_s} | dog-held-out | yes |",
        f"| Home dog-split macro-F1 | {f1_s} | dog-held-out | yes |",
        f"| Home dogs / rows | {home.get('n_dogs', 0)} / {home.get('n_rows', 0)} | dog-held-out | yes |",
        f"| Home rows with collar CBOR | {home.get('collar_rows', 0)} | dog-held-out | no |",
        f"| Rev-A puck contract | {'ok' if report.get('hardware', {}).get('ok') else 'missing'} | hardware | yes |",
        f"| Triad best_val_acc | {triad if triad is not None else '—'} | synthetic-or-unknown | no |",
        f"| Vocal best_val_acc | {vocal if vocal is not None else '—'} | mixed-or-unknown | no |",
        "",
        f"**bar_met:** `{report['bar_met']}`",
        "",
        "## Blockers",
        "",
    ]
    if report["blockers"]:
        lines.extend(f"- {b}" for b in report["blockers"])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, report: dict[str, Any]) -> None:
    paper = root / "docs" / "paper"
    paper.mkdir(parents=True, exist_ok=True)
    (paper / "RESULTS.md").write_text(render_results_md(report), encoding="utf-8")
    out = root / "artifacts" / "eval"
    out.mkdir(parents=True, exist_ok=True)
    (out / "v1_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

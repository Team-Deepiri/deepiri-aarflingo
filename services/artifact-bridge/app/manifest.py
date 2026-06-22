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

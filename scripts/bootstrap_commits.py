#!/usr/bin/env python3
"""Bootstrap deepiri-aarflingo with many atomic git commits."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], check: bool = True) -> None:
    subprocess.run(cmd, cwd=ROOT, check=check)


def commit(paths: list[str], message: str) -> None:
    for p in paths:
        path = ROOT / p
        if path.exists():
            run(["git", "add", p])
    run(["git", "commit", "-m", message])


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- file contents will be added by bootstrap_commits_data module inline below ---

COMMITS: list[tuple[list[str], str, dict[str, str] | None]] = []


def register(files: dict[str, str], message: str) -> None:
    COMMITS.append((list(files.keys()), message, files))


def main() -> None:
    from bootstrap_commits_data import ALL_COMMITS  # noqa: F401

    for files, message in ALL_COMMITS:
        for rel, content in files.items():
            write(rel, content)
        commit(list(files.keys()), message)

    count = subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=ROOT, text=True).strip()
    print(f"Total commits: {count}")


if __name__ == "__main__":
    main()

"""Isolated loader for sibling service packages.

AARFLingo services all use `app` as their top-level package name. When the
voice CLI needs the audio vocal encoder (or any other service), importing
`app.synth` directly would collide with voice's own `app`. This loader mounts
a service's `app/` directory under a unique package name (`aarf_audio_*`) —
the same strategy `services/runtime/app/engine.py` uses.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def load_service(service: str, module: str):
    app_dir = ROOT / "services" / service / "app"
    pkg_name = f"aarf_{service}"

    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(app_dir)]  # type: ignore[attr-defined]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg

    pending: list[tuple[object, object]] = []
    for py in sorted(app_dir.glob("*.py")):
        if py.name == "__init__.py":
            continue
        mod_name = f"{pkg_name}.{py.stem}"
        if mod_name in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(
            mod_name,
            py,
            submodule_search_locations=[str(app_dir)],
        )
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = pkg_name
        sys.modules[mod_name] = mod
        pending.append((spec, mod))

    loaded: set[object] = set()
    for _ in range(len(pending) + 2):
        for spec, mod in pending:
            if mod in loaded:
                continue
            try:
                spec.loader.exec_module(mod)
                loaded.add(mod)
            except ImportError:
                continue
        if len(loaded) == len(pending):
            break
    if len(loaded) != len(pending):
        raise ImportError(f"Failed to load all modules for services/{service}/app")

    key = f"{pkg_name}.{module}"
    if key not in sys.modules:
        raise ImportError(f"Module {key} not found under services/{service}/app")
    return sys.modules[key]

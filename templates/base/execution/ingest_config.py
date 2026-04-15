"""Loader + validator for config/ingest_sources.json (#128)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "ingest_sources.json"
SCHEMA_PATH = ROOT / "config" / "ingest_sources.schema.json"

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_ALLOWED_TYPES = {"x", "youtube"}
_ALLOWED_CADENCE = {"hourly", "daily", "weekly"}


@dataclass
class LoadResult:
    config: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _structural_validate(cfg: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Light structural validator that doesn't require jsonschema."""
    errors: list[str] = []
    warnings: list[str] = []

    if cfg.get("version") != 1:
        errors.append(f"version must be 1, got {cfg.get('version')!r}")
    sources = cfg.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be a list")
        return errors, warnings

    seen_ids: set[str] = set()
    for i, src in enumerate(sources):
        tag = f"sources[{i}]"
        if not isinstance(src, dict):
            errors.append(f"{tag} must be an object")
            continue
        sid = src.get("id")
        if not isinstance(sid, str) or not _ID_RE.match(sid):
            errors.append(f"{tag}.id must match {_ID_RE.pattern}")
        elif sid in seen_ids:
            errors.append(f"{tag}.id duplicate: {sid!r}")
        else:
            seen_ids.add(sid)

        stype = src.get("type")
        if stype not in _ALLOWED_TYPES:
            errors.append(f"{tag}.type must be one of {sorted(_ALLOWED_TYPES)}, got {stype!r}")

        if not isinstance(src.get("handle"), str) or not src["handle"]:
            errors.append(f"{tag}.handle required, non-empty string")

        notebooks = src.get("notebooks")
        if not isinstance(notebooks, list) or not notebooks or not all(
            isinstance(n, str) and n for n in notebooks
        ):
            errors.append(f"{tag}.notebooks must be a non-empty list of strings")

        if "enabled" not in src or not isinstance(src["enabled"], bool):
            errors.append(f"{tag}.enabled required, bool")

        if "cadence" in src and src["cadence"] not in _ALLOWED_CADENCE:
            errors.append(
                f"{tag}.cadence must be one of {sorted(_ALLOWED_CADENCE)}, got {src['cadence']!r}"
            )

        # Warnings (non-blocking)
        if src.get("enabled") and "cadence" not in src and "schedule" not in src:
            warnings.append(f"{tag} enabled without cadence/schedule — will only run on manual invocation")
        if src.get("cadence") and src.get("schedule"):
            warnings.append(f"{tag} has both cadence and schedule; schedule wins")
        nb_ids = src.get("notebook_ids", {})
        for name in notebooks or []:
            if nb_ids and name not in nb_ids:
                warnings.append(f"{tag}.notebook_ids missing entry for {name!r} — will be resolved on next run")

    return errors, warnings


def load_config(path: Path = DEFAULT_CONFIG) -> LoadResult:
    """Load + validate an ingest_sources.json config."""
    if not path.exists():
        return LoadResult({}, [], [f"config not found: {path}"])
    try:
        cfg = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return LoadResult({}, [], [f"invalid JSON in {path}: {e}"])
    if not isinstance(cfg, dict):
        return LoadResult({}, [], ["config must be a JSON object"])
    errors, warnings = _structural_validate(cfg)
    return LoadResult(cfg if not errors else {}, warnings, errors)


def enabled_sources(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only enabled sources from a validated config."""
    return [s for s in cfg.get("sources", []) if s.get("enabled")]


def find_source(cfg: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    for s in cfg.get("sources", []):
        if s.get("id") == source_id:
            return s
    return None


def persist_notebook_id(config_path: Path, source_id: str, notebook_name: str, notebook_id: str) -> None:
    """Atomically record a resolved notebook id back to config (mirror of
    what ensure_notebook.py does; kept here so the dispatcher can call it
    without importing from skills/)."""
    cfg = json.loads(config_path.read_text())
    for s in cfg.get("sources", []):
        if s.get("id") == source_id:
            s.setdefault("notebook_ids", {})[notebook_name] = notebook_id
            break
    tmp = config_path.with_suffix(config_path.suffix + ".tmp")
    tmp.write_text(json.dumps(cfg, indent=2) + "\n")
    tmp.replace(config_path)

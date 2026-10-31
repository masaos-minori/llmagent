#!/usr/bin/env python3
"""_contract_manifests.py — Shared contract-manifest infrastructure.

Private module for tools/generate_reference_table.py: the manifest envelope
model, JSON Schema validation, YAML load/write, and the shared entry->markdown
renderers. Committed manifests live in registry/manifests/ and are validated
against schemas/contract_manifest.json before every write; generated_at is
never written so committed YAML stays byte-stable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "contract_manifest.json"

MANIFEST_VERSION = 1
GENERATED_BY = "tools/generate_reference_table.py"


class ManifestError(RuntimeError):
    """A manifest failed schema validation or an internal consistency rule."""


def envelope(
    manifest: str, sources: list[str], entries: list[dict[str, Any]]
) -> dict[str, Any]:
    """Return the validated manifest envelope for *manifest*.

    generated_at is deliberately absent: committed manifests must be
    byte-stable for the git-diff freshness step.
    """
    data: dict[str, Any] = {
        "manifest": manifest,
        "version": MANIFEST_VERSION,
        "generated_by": GENERATED_BY,
        "sources": sources,
        "entries": entries,
    }
    return validate_manifest(data)


_schema: dict[str, Any] | None = None


def _load_schema() -> dict[str, Any]:
    global _schema
    if _schema is None:
        _schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return _schema


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return *manifest* after validating it against the contract schema."""
    try:
        jsonschema.validate(manifest, _load_schema())
    except jsonschema.ValidationError as exc:
        raise ManifestError(
            f"manifest {manifest.get('manifest')!r} rejected by "
            f"{SCHEMA_PATH.relative_to(REPO_ROOT)}: {exc.message}"
        ) from exc
    return manifest


def dump_manifest(manifest: dict[str, Any]) -> str:
    """Return the canonical YAML text for *manifest* (byte-stable output)."""
    text: str = yaml.safe_dump(manifest, sort_keys=True)
    return text


def write_manifest(
    manifest: dict[str, Any], manifest_dir: Path, *, dry_run: bool = False
) -> Path:
    """Validate and write registry/manifests/<name>.yaml; return its path."""
    validate_manifest(manifest)
    path = manifest_dir / f"{manifest['manifest']}.yaml"
    if not dry_run:
        manifest_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(dump_manifest(manifest), encoding="utf-8")
    return path


def load_manifest(name: str, manifest_dir: Path) -> dict[str, Any] | None:
    """Return the committed manifest for *name*, or None when it is absent."""
    path = manifest_dir / f"{name}.yaml"
    if not path.is_file():
        return None
    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data


def escape_table_cell(value: str) -> str:
    """Escape `|` so *value* cannot be mistaken for a Markdown table column
    separator (e.g. a `X | None` union-type annotation inside a signature)."""
    return value.replace("|", "\\|")


def render_symbol_table(entries: list[dict[str, Any]]) -> str:
    """Render a `| File | Class/Function | Signature | Summary |` table from
    symbol-manifest entries (agent_api/eventbus_api/memory_api shape).

    Entries arrive grouped by file in source order; the File cell is left
    blank after a file's first row, matching the historical table layout.
    """
    lines = ["| File | Class/Function | Signature | Summary |", "|---|---|---|---|"]
    current_file: str | None = None
    for entry in entries:
        file_cell = f"`{entry['file']}`" if entry["file"] != current_file else ""
        current_file = entry["file"]
        signature = escape_table_cell(entry["signature"])
        summary = escape_table_cell(entry["summary"])
        lines.append(f"| {file_cell} | `{entry['name']}` | `{signature}` | {summary} |")
    return "\n".join(lines)

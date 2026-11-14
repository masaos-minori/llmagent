#!/usr/bin/env python3
"""scripts/shared/execution_snapshot.py — Execution-snapshot builder/comparator.

Captures a component-keyed fingerprint of the running deployment at call start
(toolexec001 input to the replay-equality decision):

- ``deployed_rev``: SHA-256 of the raw ``/opt/llm/DEPLOYED_REV`` bytes, computed
  only when the file parses as JSON (producer: ``tools/manage_binaries.py
  record-revision``).
- ``git_sha``: the file's ``commit`` field.
- ``config_hash``: SHA-256 over the ``config/*.toml`` tree (path-delimited,
  sorted), resolved via ``shared.runtime_paths.resolve_config_dir``.
- ``schema_versions``: the ``user_version`` header field (offset 60, 4-byte big
  endian) of each known DB file; no sqlite3 connection is opened (scripts/shared
  boundary rule); equals ``PRAGMA user_version`` for committed databases.

Equality is per component; each differing component is named by
``mismatching_components`` so audit can distinguish a config-only change from a
code-revision change. Every reader is tolerant and never raises: missing inputs
yield ``"unknown"`` (rev file) or ``"absent"`` (DB). Snapshot values are hashes,
never config contents or result bodies.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path

from shared.runtime_paths import resolve_config_dir

# Deployed revision file written by `tools/manage_binaries.py record-revision`
# (REVISION_FILE under the install root). The one documented absolute read.
DEFAULT_DEPLOYED_REV_PATH = "/opt/llm/DEPLOYED_REV"

COMPONENT_KEYS: tuple[str, ...] = (
    "deployed_rev",
    "git_sha",
    "config_hash",
    "schema_versions",
)

_UNKNOWN = "unknown"
_ABSENT = "absent"

# agent.toml keys and fallbacks mirroring db.config.DbConfig; the shared-leaf
# import contract forbids importing db from here.
_DB_PATH_KEYS: dict[str, str] = {
    "rag": "rag_db_path",
    "session": "session_db_path",
    "workflow": "workflow_db_path",
}
_DB_PATH_DEFAULTS: dict[str, str] = {
    "rag": "",
    "session": "",
    "workflow": "/opt/llm/db/workflow.sqlite",
}


def _read_deployed_rev(path: Path) -> tuple[str, str]:
    """Return ``(deployed_rev, git_sha)`` from the DEPLOYED_REV file, tolerantly."""
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return _UNKNOWN, _UNKNOWN
    if not isinstance(data, dict):
        return _UNKNOWN, _UNKNOWN
    deployed_rev = hashlib.sha256(raw).hexdigest()
    commit = data.get("commit")
    git_sha = commit if isinstance(commit, str) and commit else _UNKNOWN
    return deployed_rev, git_sha


def _config_hash(config_dir: Path) -> str:
    """SHA-256 over the sorted config/*.toml tree, path-delimited."""
    digest = hashlib.sha256()
    try:
        files = sorted(config_dir.glob("*.toml"), key=lambda p: p.name)
    except OSError:
        files = []
    for path in files:
        try:
            content = path.read_bytes()
        except OSError:
            content = b"<unreadable>"
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
    return digest.hexdigest()


def _db_paths_from_config(config_dir: Path) -> dict[str, str]:
    """Return the ``label -> db path`` mapping read from agent.toml, tolerantly."""
    data: dict[str, object] = {}
    try:
        data = tomllib.loads((config_dir / "agent.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        data = {}
    paths: dict[str, str] = {}
    for label, key in _DB_PATH_KEYS.items():
        value = data.get(key)
        if not isinstance(value, str) or not value:
            value = _DB_PATH_DEFAULTS[label]
        if value:
            paths[label] = value
    return paths


def _user_version(path_str: str) -> str:
    """Return the database's ``user_version`` from the file header, or ``absent``.

    Reads the 4-byte big-endian field at offset 60 of the SQLite file header,
    which equals ``PRAGMA user_version`` for committed databases. No database
    connection is opened: the scripts/shared boundary rule forbids direct
    SQLite connections in this layer.
    """
    try:
        with open(path_str, "rb") as fh:
            header = fh.read(64)
    except OSError:
        return _ABSENT
    if len(header) < 64 or header[:16] != b"SQLite format 3\x00":
        return _ABSENT
    return str(int.from_bytes(header[60:64], "big"))


def _schema_versions(db_paths: Mapping[str, str]) -> str:
    """Join ``label=version`` segments in sorted label order."""
    if not db_paths:
        return "none"
    return ";".join(
        f"{label}={_user_version(db_paths[label])}" for label in sorted(db_paths)
    )


def build_execution_snapshot(
    *,
    deployed_rev_path: str | Path | None = None,
    config_dir: str | Path | None = None,
    db_paths: Mapping[str, str | Path] | Iterable[str | Path] | None = None,
) -> dict[str, str]:
    """Build the four-component execution snapshot. Never raises.

    Keyword seams (row 18 test contract): ``deployed_rev_path``, ``config_dir``
    and ``db_paths`` override the deployed defaults; ``db_paths`` accepts a
    ``label -> path`` mapping or a plain iterable of paths (labels are then the
    file stems).
    """
    rev_path = (
        Path(deployed_rev_path)
        if deployed_rev_path is not None
        else Path(DEFAULT_DEPLOYED_REV_PATH)
    )
    cfg_dir = resolve_config_dir(config_dir)
    deployed_rev, git_sha = _read_deployed_rev(rev_path)
    if db_paths is None:
        resolved_db_paths = _db_paths_from_config(cfg_dir)
    elif isinstance(db_paths, Mapping):
        resolved_db_paths = {str(label): str(path) for label, path in db_paths.items()}
    else:
        resolved_db_paths = {Path(path).stem: str(path) for path in db_paths}
    return {
        "deployed_rev": deployed_rev,
        "git_sha": git_sha,
        "config_hash": _config_hash(cfg_dir),
        "schema_versions": _schema_versions(resolved_db_paths),
    }


def snapshot_json(snapshot: Mapping[str, str]) -> str:
    """Canonical sorted-JSON encoding for storage."""
    return json.dumps(
        dict(snapshot), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )


def mismatching_components(a: Mapping[str, str], b: Mapping[str, str]) -> list[str]:
    """Name every component that differs or is missing on either side."""
    mismatches: list[str] = []
    for key in COMPONENT_KEYS:
        if key not in a or key not in b or a[key] != b[key]:
            mismatches.append(key)
    return mismatches


def snapshots_equal(a: Mapping[str, str], b: Mapping[str, str]) -> bool:
    """True only when all four components are present on both sides and equal."""
    return not mismatching_components(a, b)

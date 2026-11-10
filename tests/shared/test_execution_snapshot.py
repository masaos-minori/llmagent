"""Tests for scripts/shared/execution_snapshot.py (toolexec001 row 18).

Covers the four-component build, snapshot equality, per-component mismatch
reporting, missing DEPLOYED_REV tolerance, and cross-process/cross-cwd
determinism. SQLite fixtures are file-backed with a committed header because
schema_versions reads the file header (offset 28), which :memory: DBs lack.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from shared.execution_snapshot import (
    COMPONENT_KEYS,
    build_execution_snapshot,
    mismatching_components,
    snapshot_json,
    snapshots_equal,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_TYPE = dict[str, str]


def _make_db(path: Path, user_version: int = 1) -> Path:
    """Create a file-backed sqlite DB with a committed user_version header."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(f"PRAGMA user_version = {user_version}")
        conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()
    return path


@pytest.fixture
def fx(tmp_path: Path) -> dict[str, Any]:
    """Self-contained fixture set: DEPLOYED_REV, config dir, three versioned DBs."""
    deploy_rev = tmp_path / "DEPLOYED_REV"
    deploy_rev.write_text(
        json.dumps(
            {
                "commit": "abc123def456",
                "dirty": False,
                "deployed_at": "2026-10-31T00:00:00Z",
                "binaries": {"agent_main": "deadbeef"},
            }
        )
    )
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    rag_db = _make_db(tmp_path / "rag.sqlite", user_version=7)
    session_db = _make_db(tmp_path / "session.sqlite", user_version=3)
    workflow_db = _make_db(tmp_path / "workflow.sqlite", user_version=1)
    (config_dir / "agent.toml").write_text(
        f'rag_db_path = "{rag_db}"\n'
        f'session_db_path = "{session_db}"\n'
        f'workflow_db_path = "{workflow_db}"\n'
    )
    (config_dir / "rag.toml").write_text('search_provider = "openai"\n')
    return {
        "tmp": tmp_path,
        "deploy_rev": deploy_rev,
        "config_dir": config_dir,
        "db_paths": {"rag": rag_db, "session": session_db, "workflow": workflow_db},
    }


def _build(fx: dict[str, Any], **overrides: object) -> SNAPSHOT_TYPE:
    kwargs: dict[str, Any] = {
        "deployed_rev_path": fx["deploy_rev"],
        "config_dir": fx["config_dir"],
        "db_paths": fx["db_paths"],
    }
    kwargs.update(overrides)
    return build_execution_snapshot(**kwargs)


class TestBuild:
    def test_component_shape(self, fx: dict[str, Any]) -> None:
        snap = _build(fx)
        assert set(snap) == set(COMPONENT_KEYS)
        assert snap["git_sha"] == "abc123def456"
        assert len(snap["deployed_rev"]) == 64
        assert len(snap["config_hash"]) == 64

    def test_schema_versions_label_join(self, fx: dict[str, Any]) -> None:
        snap = _build(fx)
        assert snap["schema_versions"] == "rag=7;session=3;workflow=1"

    def test_missing_db_reads_absent(self, fx: dict[str, Any]) -> None:
        snap = _build(fx, db_paths={"rag": fx["tmp"] / "nope.sqlite"})
        assert snap["schema_versions"] == "rag=absent"

    def test_foreign_file_reads_absent(self, fx: dict[str, Any]) -> None:
        bogus = fx["tmp"] / "bogus.sqlite"
        bogus.write_bytes(b"not a sqlite file")
        snap = _build(fx, db_paths={"rag": bogus})
        assert snap["schema_versions"] == "rag=absent"

    def test_default_db_paths_from_agent_toml(self, fx: dict[str, Any]) -> None:
        # agent.toml in the fixture config dir carries the top-level db path keys.
        snap = _build(fx, db_paths=None)
        assert snap["schema_versions"] == "rag=7;session=3;workflow=1"


class TestEquality:
    def test_identical_inputs_are_equal(self, fx: dict[str, Any]) -> None:
        assert snapshots_equal(_build(fx), _build(fx))
        assert snapshot_json(_build(fx)) == snapshot_json(_build(fx))

    def test_any_component_difference_breaks_equality(self, fx: dict[str, Any]) -> None:
        base = _build(fx)
        other = _build(fx, deployed_rev_path=None)
        assert not snapshots_equal(base, other)

    def test_snapshot_json_is_canonical_sorted(self, fx: dict[str, Any]) -> None:
        encoded = snapshot_json(_build(fx))
        assert encoded == json.dumps(
            json.loads(encoded), sort_keys=True, separators=(",", ":")
        )


class TestPerComponentMismatch:
    def test_config_byte_flip_flags_only_config_hash(self, fx: dict[str, Any]) -> None:
        base = _build(fx)
        (fx["config_dir"] / "rag.toml").write_text('search_provider = "local"\n')
        other = _build(fx)
        assert mismatching_components(base, other) == ["config_hash"]

    def test_user_version_flip_flags_only_schema_versions(
        self, fx: dict[str, Any]
    ) -> None:
        base = _build(fx)
        _make_db(fx["db_paths"]["rag"], user_version=8)
        other = _build(fx)
        assert mismatching_components(base, other) == ["schema_versions"]

    def test_rev_regeneration_flags_only_deployed_rev(self, fx: dict[str, Any]) -> None:
        base = _build(fx)
        # Same commit, new deployed_at: only the raw-bytes hash changes.
        fx["deploy_rev"].write_text(
            json.dumps(
                {
                    "commit": "abc123def456",
                    "dirty": False,
                    "deployed_at": "2026-11-01T00:00:00Z",
                }
            )
        )
        other = _build(fx)
        assert mismatching_components(base, other) == ["deployed_rev"]

    def test_commit_flip_flags_deployed_rev_and_git_sha(
        self, fx: dict[str, Any]
    ) -> None:
        base = _build(fx)
        fx["deploy_rev"].write_text(json.dumps({"commit": "def456abc123"}))
        other = _build(fx)
        assert mismatching_components(base, other) == ["deployed_rev", "git_sha"]

    def test_no_difference_returns_empty_list(self, fx: dict[str, Any]) -> None:
        assert mismatching_components(_build(fx), _build(fx)) == []


class TestTolerance:
    def test_json_non_object_rev_yields_unknown(self, fx: dict[str, Any]) -> None:
        fx["deploy_rev"].write_text("[1, 2, 3]")
        snap = _build(fx)
        assert snap["deployed_rev"] == "unknown"
        assert snap["git_sha"] == "unknown"

    def test_unreadable_config_dir_hashes_empty(self, fx: dict[str, Any]) -> None:
        cfg: Path = fx["config_dir"]
        cfg.chmod(0)
        try:
            snap = _build(fx)
        finally:
            cfg.chmod(0o755)
        assert len(snap["config_hash"]) == 64

    def test_unreadable_toml_is_hashed_as_unreadable_marker(
        self, fx: dict[str, Any]
    ) -> None:
        toml_path: Path = fx["config_dir"] / "rag.toml"
        toml_path.chmod(0)
        try:
            snap = _build(fx)
        finally:
            toml_path.chmod(0o644)
        assert len(snap["config_hash"]) == 64

    def test_missing_agent_toml_falls_back_to_defaults(
        self, fx: dict[str, Any]
    ) -> None:
        empty_cfg = fx["tmp"] / "empty_cfg"
        empty_cfg.mkdir()
        snap = _build(fx, config_dir=empty_cfg, db_paths=None)
        labels = [seg.split("=")[0] for seg in snap["schema_versions"].split(";")]
        # rag/session have no default path (dropped); workflow does.
        assert labels == ["workflow"]

    def test_partial_agent_toml_falls_back_per_label(self, fx: dict[str, Any]) -> None:
        partial_cfg = fx["tmp"] / "partial_cfg"
        partial_cfg.mkdir()
        (partial_cfg / "agent.toml").write_text(
            f'rag_db_path = "{fx["db_paths"]["rag"]}"\n'
        )
        (partial_cfg / "rag.toml").write_bytes(
            (fx["config_dir"] / "rag.toml").read_bytes()
        )
        snap = _build(fx, config_dir=partial_cfg, db_paths=None)
        labels = [seg.split("=")[0] for seg in snap["schema_versions"].split(";")]
        assert labels == ["rag", "workflow"]

    def test_malformed_agent_toml_falls_back_to_defaults(
        self, fx: dict[str, Any]
    ) -> None:
        bad_cfg = fx["tmp"] / "bad_cfg"
        bad_cfg.mkdir()
        (bad_cfg / "agent.toml").write_text("not = valid = toml")
        snap = _build(fx, config_dir=bad_cfg, db_paths=None)
        labels = [seg.split("=")[0] for seg in snap["schema_versions"].split(";")]
        assert labels == ["workflow"]

    def test_empty_db_paths_schema_versions_none(self, fx: dict[str, Any]) -> None:
        snap = _build(fx, db_paths={})
        assert snap["schema_versions"] == "none"

    def test_iterable_db_paths_uses_stem_labels(self, fx: dict[str, Any]) -> None:
        snap = _build(fx, db_paths=[fx["db_paths"]["rag"], fx["db_paths"]["workflow"]])
        assert snap["schema_versions"] == "rag=7;workflow=1"


class TestMissingDeployedRev:
    @pytest.mark.parametrize("variant", ["missing", "unreadable", "malformed"])
    def test_build_succeeds_with_unknown_identity(
        self, fx: dict[str, Any], tmp_path: Path, variant: str
    ) -> None:
        if variant == "missing":
            path: Path = fx["tmp"] / "absent_REV"
        elif variant == "unreadable":
            path = tmp_path / "rev_no_access"
            path.write_text('{"commit": "x"}')
            path.chmod(0)
        else:
            path = tmp_path / "rev_garbage"
            path.write_text("not json at all")
        snap = _build(fx, deployed_rev_path=path)
        assert snap["deployed_rev"] == "unknown"
        assert snap["git_sha"] == "unknown"
        if variant == "unreadable":
            path.chmod(0o644)  # allow tmp_path cleanup

    def test_comparator_flags_rev_components_only(self, fx: dict[str, Any]) -> None:
        real = _build(fx)
        without = _build(fx, deployed_rev_path=None)
        assert mismatching_components(real, without) == ["deployed_rev", "git_sha"]


class TestDeterminism:
    _SNIPPET = (
        "import json, sys; "
        "sys.path.insert(0, str(sys.argv[1]) + '/scripts'); "
        "from shared.execution_snapshot import build_execution_snapshot, snapshot_json; "
        "print(snapshot_json(build_execution_snapshot("
        "deployed_rev_path=sys.argv[2], config_dir=sys.argv[3], "
        "db_paths=json.loads(sys.argv[4]))))"
    )

    def _canonical_via_subprocess(self, cwd: Path, fx: dict[str, Any]) -> str:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                self._SNIPPET,
                str(REPO_ROOT),
                str(fx["deploy_rev"]),
                str(fx["config_dir"]),
                json.dumps({k: str(v) for k, v in fx["db_paths"].items()}),
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def test_same_inputs_same_hash_across_processes(self, fx: dict[str, Any]) -> None:
        first = self._canonical_via_subprocess(REPO_ROOT, fx)
        second = self._canonical_via_subprocess(REPO_ROOT, fx)
        assert first == second
        assert json.loads(first)["config_hash"]

    def test_different_cwd_same_hash(self, fx: dict[str, Any]) -> None:
        from_repo = self._canonical_via_subprocess(REPO_ROOT, fx)
        from_tmp = self._canonical_via_subprocess(fx["tmp"], fx)
        assert from_repo == from_tmp

    def test_injected_build_matches_subprocess_build(self, fx: dict[str, Any]) -> None:
        subprocess_json = self._canonical_via_subprocess(REPO_ROOT, fx)
        assert subprocess_json == snapshot_json(_build(fx))

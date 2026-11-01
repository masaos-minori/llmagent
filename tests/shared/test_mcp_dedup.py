"""Tests for shared.mcp_dedup: tool_call_state store (toolexec001 Phase 3).

All SQLite access is on tmp_path files; /opt/llm/db/ is never touched.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest
from shared.config_errors import ConfigMissingError, ConfigParseError
from shared.mcp_dedup import (
    DedupStore,
    classify_interrupted,
    load_dedup_config,
    open_dedup_store,
    retry_class,
)

_SNAP = {
    "deployed_rev": "deadbeef",
    "git_sha": "abcdef1",
    "config_hash": "cafef00d",
    "schema_versions": "rag=17;skill=8",
    "user_version": "42",
}


@pytest.fixture()
def store(tmp_path):
    s = DedupStore(str(tmp_path / "dedup.sqlite"))
    yield s
    s.close()


class TestStateMachine:
    def test_pending_to_completed(self, store):
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        assert store.lookup("k1").status == "pending"
        store.record_completed("k1", _SNAP, {"ok": True})
        row = store.lookup("k1")
        assert row.status == "completed"
        assert row.result == {"ok": True}

    def test_terminal_states_never_regress(self, store):
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        store.record_completed("k1", _SNAP, "done")
        # A late record_failed on a completed row must not move it out of 'completed'.
        store.record_failed("k1", "timeout")
        assert store.lookup("k1").status == "completed"
        # Same for pending->failed then a delayed completed write.
        store.record_pending("k2", "web_search", "hash2", _SNAP)
        store.record_failed("k2", "timeout")
        store.record_completed("k2", _SNAP, "late")
        assert store.lookup("k2").status == "failed"

    def test_result_truncation(self, store):
        big = "x" * 9000
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        store.record_completed("k1", _SNAP, big)
        result = store.lookup("k1").result
        assert result["truncated"] is True
        assert len(result["preview"]) < len(big)
        assert result["sha256"]

    def test_unknown_key_lookup_returns_none(self, store):
        assert store.lookup("absent") is None

    def test_force_resets_completed_row(self, store):
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        store.record_completed("k1", _SNAP, "done")
        # Default: completed stays. With force=True the dispatcher's policy-allowed
        # fresh attempt (REQ-005 snapshot mismatch) may reset it to pending.
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        assert store.lookup("k1").status == "completed"
        store.record_pending("k1", "web_search", "hash1", _SNAP, force=True)
        row = store.lookup("k1")
        assert row.status == "pending"
        assert row.result is None

    def test_clear_removes_row(self, store):
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        store.clear("k1")
        assert store.lookup("k1") is None


class TestReopenDurability:
    def test_survives_reopen(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        s = DedupStore(path)
        s.record_pending("k1", "web_search", "hash1", _SNAP)
        s.record_completed("k1", _SNAP, "done")
        s.close()

        s2 = DedupStore(path)
        row = s2.lookup("k1")
        s2.close()
        assert row.status == "completed"
        assert row.result == "done"
        assert row.snapshot["deployed_rev"] == "deadbeef"

    def test_interrupted_survives_reopen(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        s = DedupStore(path)
        past = time.time() - 3600
        s.record_pending("k1", "web_search", "hash1", _SNAP, now_epoch=past)
        s.close()
        # Simulate a fresh process after the timeout window.
        s2 = DedupStore(path)
        row = s2.lookup("k1")
        status = classify_interrupted(row, pending_timeout_minutes=10)
        s2.close()
        assert status == "interrupted"


class TestCrossProcessSharing:
    def test_second_process_sees_first_writes(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        s = DedupStore(path)
        s.record_pending("k1", "web_search", "hash1", _SNAP)
        s.record_completed("k1", _SNAP, "done")
        s.close()

        scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
        code = (
            "import sys; sys.path.insert(0, " + repr(scripts_dir) + ");"
            "from shared.mcp_dedup import DedupStore;"
            "s = DedupStore(" + repr(path) + ");"
            "row = s.lookup('k1');"
            "assert row is not None and row.status == 'completed' and row.result == 'done';"
            "s.close()"
        )
        subprocess.run([sys.executable, "-c", code], check=True, timeout=30)

    def test_first_process_sees_second_writes(self, tmp_path):
        path = str(tmp_path / "dedup.sqlite")
        scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
        code = (
            "import sys; sys.path.insert(0, " + repr(scripts_dir) + ");"
            "from shared.mcp_dedup import DedupStore;"
            "s = DedupStore(" + repr(path) + ");"
            "s.record_pending('k2', 'web_search', 'hash2', {'deployed_rev': 'x'});"
            "s.close()"
        )
        subprocess.run([sys.executable, "-c", code], check=True, timeout=30)
        s = DedupStore(path)
        row = s.lookup("k2")
        s.close()
        assert row is not None and row.status == "pending"


class TestTtlPurge:
    def test_expired_terminal_rows_purged(self, store):
        now = time.time()
        old = now - 15 * 86400
        store.record_pending("k1", "web_search", "hash1", _SNAP, now_epoch=old)
        store.record_completed("k1", _SNAP, "done", now_epoch=old)
        store.record_pending("k2", "web_search", "hash2", _SNAP, now_epoch=now)
        store.record_completed("k2", _SNAP, "fresh", now_epoch=now)
        purged = store.purge_expired(retention_days=14, now_epoch=now)
        assert purged == 1
        assert store.lookup("k1") is None
        assert store.lookup("k2") is not None

    def test_pending_rows_never_purged(self, store):
        now = time.time()
        old = now - 30 * 86400
        store.record_pending("k1", "web_search", "hash1", _SNAP, now_epoch=old)
        assert store.purge_expired(retention_days=14, now_epoch=now) == 0
        assert store.lookup("k1").status == "pending"


class TestInterruptedClassification:
    def test_pending_past_timeout_is_interrupted_without_mutation(self, store):
        now = time.time()
        store.record_pending(
            "k1", "web_search", "hash1", _SNAP, now_epoch=now - 15 * 60
        )
        row = store.lookup("k1")
        status = classify_interrupted(row, pending_timeout_minutes=10, now_epoch=now)
        assert status == "interrupted"
        # Classification must not write: the stored row is still 'pending'.
        assert store.lookup("k1").status == "pending"

    def test_pending_within_timeout_stays_pending(self, store):
        now = time.time()
        store.record_pending("k1", "web_search", "hash1", _SNAP, now_epoch=now - 60)
        row = store.lookup("k1")
        assert (
            classify_interrupted(row, pending_timeout_minutes=10, now_epoch=now)
            == "pending"
        )

    def test_terminal_rows_are_not_reclassified(self, store):
        now = time.time()
        store.record_pending(
            "k1", "web_search", "hash1", _SNAP, now_epoch=now - 15 * 60
        )
        store.record_completed("k1", _SNAP, "done", now_epoch=now)
        row = store.lookup("k1")
        assert (
            classify_interrupted(row, pending_timeout_minutes=10, now_epoch=now)
            == "completed"
        )

    def test_explicit_mark_interrupted(self, store):
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        store.mark_interrupted("k1")
        assert store.lookup("k1").status == "interrupted"


class TestConfigValidation:
    def test_missing_file_raises_typed_error(self, tmp_path):
        with pytest.raises(ConfigMissingError):
            load_dedup_config(tmp_path / "absent.toml")

    def test_malformed_toml_raises_parse_error(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text("[[ broken toml", encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad)

    def test_wrong_type_raises_parse_error(self, tmp_path):
        bad = tmp_path / "mcp_dedup.toml"
        bad.write_text('[dedup]\nretention_days = "fourteen"\n', encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad)

    def test_bad_section_types_raise_parse_error(self, tmp_path):
        bad1 = tmp_path / "mcp_dedup.toml"
        bad1.write_text('dedup = "not a table"\n', encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad1)
        bad2 = tmp_path / "mcp_dedup.toml"
        bad2.write_text('[dedup]\ndb_path = ""\n', encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad2)
        bad3 = tmp_path / "mcp_dedup.toml"
        bad3.write_text("[dedup]\n[retry_class]\nweb_search = 5\n", encoding="utf-8")
        with pytest.raises(ConfigParseError):
            load_dedup_config(bad3)

    def test_partial_config_gets_defaults(self, tmp_path):
        partial = tmp_path / "mcp_dedup.toml"
        partial.write_text('[dedup]\ndb_path = "/tmp/x.sqlite"\n', encoding="utf-8")
        cfg = load_dedup_config(partial)
        assert cfg.retention_days == 14
        assert cfg.pending_timeout_minutes == 10
        assert cfg.retry_class == {}

    def test_retry_class_lookup(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text(
            '[dedup]\n[retry_class]\nweb_search = "retryable"\nmdq_rag_query = "retryable"\n',
            encoding="utf-8",
        )
        cfg = load_dedup_config(cfg_file)
        assert retry_class("web_search", cfg) == "retryable"
        # Unknown tools are never retried blindly.
        assert retry_class("some_new_tool", cfg) == "non_retryable"

    def test_store_opens_from_config_db_path(self, tmp_path):
        cfg_file = tmp_path / "mcp_dedup.toml"
        cfg_file.write_text(
            f'[dedup]\ndb_path = "{tmp_path / "from_cfg.sqlite"}"\n', encoding="utf-8"
        )
        cfg = load_dedup_config(cfg_file)
        store = open_dedup_store(cfg)
        store.record_pending("k1", "web_search", "hash1", _SNAP)
        assert store.lookup("k1").status == "pending"
        store.close()
        assert (tmp_path / "from_cfg.sqlite").exists()

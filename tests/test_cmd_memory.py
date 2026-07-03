"""tests/test_cmd_memory.py
Tests for _MemoryMixin._cmd_memory() CLI help and rebuild/import-jsonl behavior.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


def _make_mixin():
    """Return a _MemoryMixin instance with minimal stubs."""
    from agent.commands.cmd_memory import _MemoryMixin

    ctx = SimpleNamespace(
        cfg=SimpleNamespace(memory=SimpleNamespace(memory_embed_enabled=True)),
        services=SimpleNamespace(audit_logger=None),
        stats=SimpleNamespace(stat_memory_consistency_failures=0),
    )
    messages: list[str] = []
    out = SimpleNamespace(
        write=lambda msg: messages.append(msg),
        write_success=lambda msg: messages.append(msg),
        write_validation_error=lambda msg: messages.append(msg),
        write_table=lambda header, rows: messages.append(
            "TABLE:" + " | ".join(str(r) for r in rows)
        ),
    )

    class _ConcreteMemoryMixin(_MemoryMixin):
        pass

    mixin = _ConcreteMemoryMixin.__new__(_ConcreteMemoryMixin)
    mixin._ctx = ctx
    mixin._out = out
    return mixin, messages


def _make_memory_store():
    """Return a mock MemoryStore with import_from_jsonl stub."""
    store = SimpleNamespace()

    def _import(jsonl_store, dry_run=False):
        if dry_run:
            return (5, 0)
        return (5, 5)

    store.import_from_jsonl = _import

    # Mock the JSONL ingestion layer
    jsonl = SimpleNamespace()
    ingestion = SimpleNamespace(_jsonl=jsonl)

    mem = SimpleNamespace(
        store=store,
        ingestion=ingestion,
    )
    return mem


class TestMemoryHelp:
    def test_memory_help_describes_jsonl_as_archive(self):
        """CLI help should describe JSONL as archive, not source of truth."""
        mixin, messages = _make_mixin()
        mixin._cmd_memory("help")

        help_text = " ".join(messages)
        assert "archive" in help_text.lower(), (
            f"Help text should mention 'archive', got: {help_text}"
        )
        assert "source of truth" not in help_text.lower(), (
            f"Help text must not describe JSONL as source of truth, got: {help_text}"
        )

    def test_memory_rebuild_help_mentions_archive(self):
        """The rebuild subcommand help line should mention archive."""
        mixin, messages = _make_mixin()
        mixin._cmd_memory("help")

        help_text = " ".join(messages)
        assert "archive" in help_text.lower(), (
            f"Rebuild help should mention 'archive', got: {help_text}"
        )


class TestMemoryRebuild:
    def test_memory_rebuild_dry_run_mentions_archive(self):
        """Dry-run rebuild output should reference JSONL archive."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        with patch("agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 0)):
            mixin._cmd_memory("rebuild --dry-run")

        assert any("archive" in msg.lower() for msg in messages), (
            f"Dry-run output should mention 'archive', got: {messages}"
        )

    def test_memory_rebuild_actual_mentions_archive(self):
        """Actual rebuild output should reference JSONL archive."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        with patch("agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)):
            mixin._cmd_memory("rebuild")

        assert any("archive" in msg.lower() for msg in messages), (
            f"Rebuild output should mention 'archive', got: {messages}"
        )

    def test_memory_rebuild_mentions_not_replayed(self):
        """Actual rebuild output should clarify what is NOT replayed."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        with patch("agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)):
            mixin._cmd_memory("rebuild")

        assert any(
            "NOT replayed" in msg or "not replayed" in msg for msg in messages
        ), f"Rebuild output should mention what is NOT replayed, got: {messages}"


class TestMemoryImportJsonlAlias:
    def test_memory_import_jsonl_alias_if_added(self):
        """The import-jsonl subcommand should work as an alias for rebuild."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        with patch("agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)):
            mixin._cmd_memory("import-jsonl")

        # Should produce the same output as /memory rebuild
        assert any("Imported" in msg for msg in messages), (
            f"import-jsonl should produce import confirmation, got: {messages}"
        )


class TestMemoryCheckConsistency:
    def test_memory_check_consistency_does_not_recommend_jsonl_import_for_index_repair(
        self,
    ):
        """Consistency output must not recommend JSONL import for FTS/vector repair."""
        from agent.memory.models import ConsistencyReport

        mixin, messages = _make_mixin()
        mem = SimpleNamespace(
            store=SimpleNamespace(
                check_consistency=lambda: ConsistencyReport(memories=10, fts=8, vec=9),
            ),
            ingestion=SimpleNamespace(_jsonl=SimpleNamespace(count_all=lambda: 12)),
        )
        mixin._ctx.services.memory = mem

        mixin._cmd_memory("check-consistency")

        full_output = " ".join(messages)
        assert (
            "rebuild" not in full_output.lower() or "rebuild-fts" in full_output.lower()
        ), f"Should not recommend /memory rebuild for index repair, got: {full_output}"

    def test_memory_check_consistency_reports_jsonl_count_as_info_only(self):
        """JSONL count should be reported as info only, not as a repair target."""
        from agent.memory.models import ConsistencyReport

        mixin, messages = _make_mixin()
        mem = SimpleNamespace(
            store=SimpleNamespace(
                check_consistency=lambda: ConsistencyReport(memories=10, fts=8, vec=9),
            ),
            ingestion=SimpleNamespace(_jsonl=SimpleNamespace(count_all=lambda: 12)),
        )
        mixin._ctx.services.memory = mem

        mixin._cmd_memory("check-consistency")

        assert any("info" in msg.lower() for msg in messages), (
            f"JSONL count should be labeled as info only, got: {messages}"
        )

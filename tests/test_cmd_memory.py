"""tests/test_cmd_memory.py
Tests for _MemoryMixin._cmd_memory() CLI help and rebuild/import-jsonl behavior.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest


def _make_mixin():
    """Return a _MemoryMixin instance with minimal stubs."""
    from agent.commands.cmd_memory import _MemoryMixin

    ctx = SimpleNamespace(
        cfg=SimpleNamespace(memory=SimpleNamespace(memory_embed_enabled=True)),
        services=SimpleNamespace(audit_logger=None),
    )
    messages: list[str] = []
    out = SimpleNamespace(
        write=lambda msg: messages.append(msg),
        write_success=lambda msg: messages.append(msg),
        write_validation_error=lambda msg: messages.append(msg),
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

        mixin._cmd_memory("rebuild --dry-run")

        assert any("archive" in msg.lower() for msg in messages), (
            f"Dry-run output should mention 'archive', got: {messages}"
        )

    def test_memory_rebuild_actual_mentions_archive(self):
        """Actual rebuild output should reference JSONL archive."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        mixin._cmd_memory("rebuild")

        assert any("archive" in msg.lower() for msg in messages), (
            f"Rebuild output should mention 'archive', got: {messages}"
        )

    def test_memory_rebuild_mentions_not_replayed(self):
        """Actual rebuild output should clarify what is NOT replayed."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        mixin._cmd_memory("rebuild")

        assert any("NOT replayed" in msg or "not replayed" in msg for msg in messages), (
            f"Rebuild output should mention what is NOT replayed, got: {messages}"
        )


class TestMemoryImportJsonlAlias:
    def test_memory_import_jsonl_alias_if_added(self):
        """The import-jsonl subcommand should work as an alias for rebuild."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services.memory = mem

        mixin._cmd_memory("import-jsonl")

        # Should produce the same output as /memory rebuild
        assert any("Imported" in msg for msg in messages), (
            f"import-jsonl should produce import confirmation, got: {messages}"
        )

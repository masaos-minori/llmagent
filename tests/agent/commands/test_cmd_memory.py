"""tests/test_cmd_memory.py
Tests for _MemoryMixin._cmd_memory() dispatch: no-args→status, disabled→M-02,
removed-subcommand rejection, and reindex routing.
"""

from __future__ import annotations

import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.agent._config_test_defaults import MIN_DB_CONFIG

# Backing dir for rebuild backup writes in unit tests.
_TMP_JSONL_DIR = tempfile.mkdtemp(prefix="mem-cmd-test-jsonl-")


class _MockRebuildOps:
    """Minimal mock of MemoryRebuildOps that delegates to the real implementation."""

    def __init__(self, out):
        self._out = out
        self.reindex_calls: list[tuple[object, list]] = []

    def rebuild(self, mem, sub_tokens=None):
        from agent.commands.memory_rebuild_ops import MemoryRebuildOps

        # Create a minimal context for the real implementation
        ctx = SimpleNamespace(
            cfg=SimpleNamespace(
                memory=SimpleNamespace(
                    memory_embed_enabled=True,
                    memory_jsonl_dir=_TMP_JSONL_DIR,
                )
            ),
            services=SimpleNamespace(audit_logger=None),
            services_required=SimpleNamespace(memory=mem, audit_logger=None),
            stats=SimpleNamespace(stat_memory_consistency_failures=0),
        )
        ops = MemoryRebuildOps(ctx, self._out)
        ops.rebuild(mem, sub_tokens)

    def reindex(self, mem, sub_tokens=None):
        self.reindex_calls.append((mem, list(sub_tokens or [])))


class _MockDataOps:
    """Minimal mock of MemoryDataOps."""

    def __init__(self, out):
        self._out = out
        self.awaited: list[tuple[str, list[str]]] = []

    def memory_list(self, mem, sub_tokens=None):
        pass

    def memory_search(self, mem, sub_tokens=None):
        pass

    def memory_show(self, mem, sub_tokens=None):
        pass

    def memory_pin(self, mem, sub_tokens=None, pin=None):
        pass

    async def memory_delete(self, mem, sub_tokens=None):
        self.awaited.append(("delete", list(sub_tokens or [])))

    async def memory_prune(self, mem, ctx, sub_tokens=None):
        self.awaited.append(("prune", list(sub_tokens or [])))


def _make_mixin():
    """Return a _MemoryMixin instance with minimal stubs."""
    from agent.commands.cmd_memory import _MemoryMixin

    ctx = SimpleNamespace(
        cfg=SimpleNamespace(
            # The command receives the typed configuration from the process that owns
            # the file; the fixture supplies it directly instead of reading a config file.
            db=MIN_DB_CONFIG,
            memory=SimpleNamespace(memory_embed_enabled=True, memory_max_pinned=10),
        ),
        services=SimpleNamespace(audit_logger=None),
        services_required=SimpleNamespace(memory=_make_memory_store()),
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
    mixin._rebuild_ops = _MockRebuildOps(out)
    mixin._data_ops = _MockDataOps(out)
    return mixin, messages


def _make_memory_store():
    """Return a mock MemoryStore with import_from_jsonl stub."""
    store = SimpleNamespace()

    def _import(jsonl_store, dry_run=False):
        if dry_run:
            return (5, 0)
        return (5, 5)

    store.import_from_jsonl = _import
    store.check_consistency = lambda: SimpleNamespace(memories=3, fts=3, vec=0)
    # Entries whose ids all exist in the archive below (SQLite-only count is 0).
    store.list_entries = lambda limit=50: [
        SimpleNamespace(memory_id="m1"),
        SimpleNamespace(memory_id="m2"),
    ]

    # Mock the JSONL ingestion layer
    jsonl = SimpleNamespace(
        count_all=lambda: 5,
        iter_records=lambda: [
            ("memory", {"memory_id": "m1"}),
            ("memory", {"memory_id": "m2"}),
        ],
    )
    ingestion = SimpleNamespace(_jsonl=jsonl)

    mem = SimpleNamespace(
        store=store,
        ingestion=ingestion,
    )
    return mem


class TestMemoryRebuild:
    async def test_memory_rebuild_dry_run_mentions_archive(self):
        """Dry-run rebuild output should reference JSONL archive."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services_required.memory = mem

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 0)
        ):
            await mixin._cmd_memory("rebuild --dry-run")

        assert any("archive" in msg.lower() for msg in messages), (
            f"Dry-run output should mention 'archive', got: {messages}"
        )

    async def test_memory_rebuild_actual_mentions_archive(self):
        """Actual rebuild output should reference JSONL archive."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services_required.memory = mem

        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl", return_value=(5, 5)
        ):
            await mixin._cmd_memory("rebuild --confirm")

        assert any("archive" in msg.lower() for msg in messages), (
            f"Rebuild output should mention 'archive', got: {messages}"
        )


class TestMemoryDispatch:
    """No-args→status, disabled→M-02, removed-subcommand rejection, reindex routing."""

    async def test_no_args_runs_status(self):
        """A bare /memory runs status (not help)."""
        mixin, messages = _make_mixin()
        # Provide a mem whose embed_client is absent so status takes the
        # enabled-but-no-client branch (distinct from the disabled/help paths).
        mixin._ctx.services_required.memory = SimpleNamespace(
            retriever=SimpleNamespace(
                embed_client=None, fts_fallback_count=0, last_retrieval_mode=""
            ),
            get_stats=lambda: {
                "total": 0,
                "semantic": 0,
                "episodic": 0,
                "by_source": {},
            },
            get_activation_mode=lambda: "",
        )

        await mixin._cmd_memory("")

        joined = " ".join(messages)
        assert "embed_client not available" in joined, (
            f"Expected status output, got: {messages}"
        )

    async def test_disabled_non_status_writes_m02(self):
        """With the layer disabled, a non-status subcommand prints M-02 and changes nothing."""
        mixin, messages = _make_mixin()
        mixin._ctx.services_required.memory = None  # type: ignore[attr-defined] — ctx is a SimpleNamespace stub; memory assigned dynamically

        await mixin._cmd_memory("list")

        joined = " ".join(messages)
        assert "M-02" in joined, f"Expected M-02, got: {messages}"

    async def test_status_runs_even_when_disabled(self):
        """status remains reachable when the layer is disabled."""
        mixin, messages = _make_mixin()
        mixin._ctx.services_required.memory = None  # type: ignore[attr-defined] — ctx is a SimpleNamespace stub; memory assigned dynamically

        await mixin._cmd_memory("status")

        assert any("disabled" in m.lower() for m in messages), (
            f"status should report disabled, got: {messages}"
        )

    async def test_removed_subcommand_raises(self):
        """A removed subcommand raises UnknownSubcommandError over the reduced set."""
        from agent.commands.exceptions import UnknownSubcommandError

        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services_required.memory = mem

        with pytest.raises(UnknownSubcommandError) as exc_info:
            await mixin._cmd_memory("search")

        assert exc_info.value.sub == "search"
        for kept in ("list", "delete", "pin", "unpin", "prune", "reindex", "rebuild"):
            assert kept in exc_info.value.valid, (
                f"{kept} should remain a valid subcommand"
            )
        assert "search" not in exc_info.value.valid

    async def test_reindex_routes_to_rebuild_ops(self):
        """reindex routes to MemoryRebuildOps.reindex with the sub tokens."""
        mixin, messages = _make_mixin()
        mem = _make_memory_store()
        mixin._ctx.services_required.memory = mem

        await mixin._cmd_memory("reindex --fts")

        assert mixin._rebuild_ops.reindex_calls == [(mem, ["--fts"])], (
            f"reindex should route to rebuild_ops.reindex, got: {mixin._rebuild_ops.reindex_calls}"
        )


class TestAsyncHandlersAreAwaited:
    async def test_delete_and_prune_coroutines_are_awaited(self):
        mixin, _messages = _make_mixin()
        await mixin._cmd_memory("delete abc123")
        await mixin._cmd_memory("prune --days 7")
        assert mixin._data_ops.awaited == [
            ("delete", ["abc123"]),
            ("prune", ["--days", "7"]),
        ]

    async def test_sync_handlers_still_work_without_awaiting(self):
        mixin, _messages = _make_mixin()
        await mixin._cmd_memory("list")
        assert mixin._data_ops.awaited == []

    def test_cmd_memory_is_a_coroutine_function_matching_its_command_def(self):
        import inspect

        from agent.commands.cmd_memory import _MemoryMixin
        from agent.commands.command_defs_list import _COMMANDS

        memory = next(c for c in _COMMANDS if c.name == "/memory")
        assert memory.is_async is True
        assert inspect.iscoroutinefunction(_MemoryMixin._cmd_memory)

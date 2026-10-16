"""tests/agent/commands/test_memory_data_ops.py

Characterization tests for MemoryDataOps.memory_list / memory_search.

These two methods previously had no direct test coverage (only exercised via
stubbed test doubles in cmd_memory.py's dispatch tests) — added here to lock
behavior before extracting the shared summary-preview formatting logic.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from agent.commands.memory_data_ops import MemoryDataOps
from db.maintenance import MaintenanceMode, MaintenanceResult


def _make_entry(
    *,
    memory_id: str = "id1",
    memory_type: str = "semantic",
    importance: float = 0.5,
    pinned: bool = False,
    summary: str = "",
    content: str = "hello world",
) -> MagicMock:
    entry = MagicMock()
    entry.memory_id = memory_id
    entry.memory_type = memory_type
    entry.importance = importance
    entry.pinned = pinned
    entry.summary = summary
    entry.content = content
    return entry


def _make_ops() -> tuple[MemoryDataOps, MagicMock]:
    ctx = MagicMock()
    out = MagicMock()
    return MemoryDataOps(ctx, out), out


class TestMemoryListSummaryPreview:
    def test_uses_summary_when_present(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(summary="a short summary", content="ignored content")
        mem.store.search_by_type.side_effect = lambda memory_type, limit: (
            [entry] if memory_type == "semantic" else []
        )

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("a short summary" in line for line in lines)

    def test_falls_back_to_truncated_content_when_summary_empty(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        long_content = "x" * 100
        entry = _make_entry(summary="", content=long_content)
        mem.store.search_by_type.side_effect = lambda memory_type, limit: (
            [entry] if memory_type == "semantic" else []
        )

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any(("x" * 60) in line for line in lines)
        assert not any(("x" * 61) in line for line in lines)

    def test_no_entries_writes_no_data_message(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.search_by_type.return_value = []

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("No entries found" in line for line in lines)


class TestMemorySearchSummaryPreview:
    def test_uses_summary_when_present(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(summary="a short summary", content="ignored content")
        hit = MagicMock()
        hit.entry = entry
        hit.score = 0.9
        mem.retriever.search.return_value = [hit]

        ops.memory_search(mem, ["some", "query"])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("a short summary" in line for line in lines)

    def test_falls_back_to_truncated_content_when_summary_empty(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        long_content = "y" * 100
        entry = _make_entry(summary="", content=long_content)
        hit = MagicMock()
        hit.entry = entry
        hit.score = 0.1
        mem.retriever.search.return_value = [hit]

        ops.memory_search(mem, ["query"])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert any(("y" * 60) in line for line in lines)
        assert not any(("y" * 61) in line for line in lines)

    def test_empty_query_writes_validation_error(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()

        ops.memory_search(mem, [])

        out.write_validation_error.assert_called_once()
        mem.retriever.search.assert_not_called()


class TestResolveId:
    def test_full_id_resolves_directly(self) -> None:
        ops, _ = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = _make_entry(memory_id="full-id")
        assert ops._resolve_id(mem, "full-id") == ("full-id", "")
        mem.store.list_entries.assert_not_called()

    def test_short_unambiguous(self) -> None:
        ops, _ = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        assert ops._resolve_id(mem, "abcdef12") == ("abcdef1234", "")

    def test_ambiguous_prefix(self) -> None:
        ops, _ = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="abcdef12aa"),
            _make_entry(memory_id="abcdef12bb"),
        ]
        assert ops._resolve_id(mem, "abcdef12") == ("", "ambiguous")

    def test_unknown_prefix(self) -> None:
        ops, _ = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="zzzz9999")]
        assert ops._resolve_id(mem, "abcdef12") == ("", "unknown")

    def test_short_token_below_min_is_unknown(self) -> None:
        ops, _ = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        # len("abc") < 8 -> unknown without scanning the store
        assert ops._resolve_id(mem, "abc") == ("", "unknown")
        mem.store.list_entries.assert_not_called()


class TestMemoryDeleteShortId:
    def test_unknown_writes_m03(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = []
        with patch("agent.commands.memory_data_ops.write_delete", return_value=False):
            ops.memory_delete(mem, ["abcdef12"])
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-03" in line for line in lines)

    def test_ambiguous_writes_m04(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="abcdef12aa"),
            _make_entry(memory_id="abcdef12bb"),
        ]
        with patch("agent.commands.memory_data_ops.write_delete", return_value=False):
            ops.memory_delete(mem, ["abcdef12"])
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-04" in line for line in lines)

    def test_short_id_resolves_before_delete(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        with (
            patch("builtins.input", return_value="y"),
            patch(
                "agent.commands.memory_data_ops.write_delete", return_value=True
            ) as wd,
        ):
            ops.memory_delete(mem, ["abcdef12"])
        wd.assert_called_once_with("abcdef1234")
        # no M-code emitted on success path
        lines = [c.args[0] for c in out.write.call_args_list]
        assert not any(m in "\n".join(lines) for m in ("M-03", "M-04"))


class TestMemoryPinShortId:
    def test_unknown_writes_m03(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = []
        with patch("agent.commands.memory_data_ops.pin_mem", return_value=True):
            ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-03" in line for line in lines)

    def test_short_id_resolves_before_pin(self) -> None:
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 10
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        with patch.object(ops, "_count_pinned", return_value=0):
            with patch(
                "agent.commands.memory_data_ops.pin_mem", return_value=True
            ) as pm:
                ops.memory_pin(mem, ["abcdef12"], pin=True)
        pm.assert_called_once_with("abcdef1234")

    def test_ambiguous_writes_m04(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="abcdef12aa"),
            _make_entry(memory_id="abcdef12bb"),
        ]
        with patch("agent.commands.memory_data_ops.pin_mem", return_value=True):
            ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-04" in line for line in lines)


class TestCountPinned:
    def test_returns_pinned_count(self) -> None:
        ops, _ = _make_ops()
        with (
            patch(  # mock-patch-ok: _count_pinned binds SQLiteHelper via a local import inside the function
                "db.helper.SQLiteHelper"
            ) as sh
        ):
            sh.return_value.open.return_value.__enter__.return_value.fetchall.return_value = [
                ("3",)
            ]
            assert ops._count_pinned() == 3

    def test_returns_zero_when_empty(self) -> None:
        ops, _ = _make_ops()
        with (
            patch(  # mock-patch-ok: _count_pinned binds SQLiteHelper via a local import inside the function
                "db.helper.SQLiteHelper"
            ) as sh
        ):
            sh.return_value.open.return_value.__enter__.return_value.fetchall.return_value = []
            assert ops._count_pinned() == 0


class TestMemoryListPinnedFilter:
    def test_pinned_filter_keeps_only_pinned(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.search_by_type.return_value = [
            _make_entry(memory_id="entry-a", pinned=True),
            _make_entry(memory_id="entry-b", pinned=False),
            _make_entry(memory_id="entry-c", pinned=True),
        ]
        ops.memory_list(mem, ["--pinned"])
        lines = [c.args[0] for c in out.write.call_args_list]
        joined = "\n".join(lines)
        assert "entry-a" in joined
        assert "entry-c" in joined
        assert "entry-b" not in joined

    def test_no_flag_lists_all(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.search_by_type.return_value = [
            _make_entry(memory_id="entry-a", pinned=False),
            _make_entry(memory_id="entry-b", pinned=False),
        ]
        ops.memory_list(mem, [])
        lines = [c.args[0] for c in out.write.call_args_list]
        joined = "\n".join(lines)
        assert "entry-a" in joined
        assert "entry-b" in joined


class TestMemoryPinLimit:
    def test_pin_at_limit_writes_m05(self) -> None:
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 1
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        with patch.object(ops, "_count_pinned", return_value=1):
            with patch(
                "agent.commands.memory_data_ops.pin_mem", return_value=True
            ) as pm:
                ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-05" in line for line in lines)
        pm.assert_not_called()

    def test_pin_below_limit_proceeds(self) -> None:
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 10
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        with patch.object(ops, "_count_pinned", return_value=0):
            with patch(
                "agent.commands.memory_data_ops.pin_mem", return_value=True
            ) as pm:
                ops.memory_pin(mem, ["abcdef12"], pin=True)
        pm.assert_called_once_with("abcdef1234")
        lines = [c.args[0] for c in out.write.call_args_list]
        assert not any(m in "\n".join(lines) for m in ("M-03", "M-04", "M-05"))


class TestMemoryPruneEvents:
    def test_prune_appends_delete_event_per_id(self) -> None:
        ops, _ = _make_ops()
        ctx = SimpleNamespace(
            cfg=SimpleNamespace(memory=SimpleNamespace(memory_retention_days=30)),
            services_required=SimpleNamespace(audit_logger=None),
        )
        prune_result = MaintenanceResult(
            success=True,
            action="prune",
            mode=MaintenanceMode.STRICT,
            data={"deleted": 2, "pruned_ids": ["id-aaa", "id-bbb"]},
        )
        with (
            patch(  # mock-patch-ok: memory_prune binds SQLiteHelper via a local import (line 360); prune_old_memories is fully mocked in this test
                "db.helper.SQLiteHelper"
            ) as mock_helper_cls,
            patch(  # mock-patch-ok: collect_prunable_ids is bound via a local import in memory_prune (line 362)
                "db.store_impl.SQLiteMemoryDeleteStore.collect_prunable_ids",
                return_value=["id-aaa", "id-bbb"],
            ),
            patch("db.maintenance.prune_old_memories", return_value=prune_result),
            patch("builtins.input", return_value="y"),
            patch("agent.commands.memory_data_ops._emit_prune_event") as emit,
        ):
            mock_h = MagicMock()
            mock_h.__enter__ = MagicMock(return_value=mock_h)
            mock_h.__exit__ = MagicMock(return_value=False)
            mock_h.open.return_value = mock_h
            mock_helper_cls.return_value = mock_h
            ops.memory_prune(MagicMock(), ctx, ["--days", "14"])
        emit.assert_has_calls([call("id-aaa"), call("id-bbb")])

    def test_prune_no_pruned_ids_emits_no_events(self) -> None:
        ops, out = _make_ops()
        ctx = SimpleNamespace(
            cfg=SimpleNamespace(memory=SimpleNamespace(memory_retention_days=30)),
            services_required=SimpleNamespace(audit_logger=None),
        )
        prune_result = MaintenanceResult(
            success=True,
            action="prune",
            mode=MaintenanceMode.STRICT,
            data={"deleted": 0, "pruned_ids": []},
        )
        with (
            patch(  # mock-patch-ok: memory_prune binds SQLiteHelper via a local import (line 360); prune_old_memories is fully mocked in this test
                "db.helper.SQLiteHelper"
            ) as mock_helper_cls,
            patch(  # mock-patch-ok: collect_prunable_ids is bound via a local import in memory_prune (line 362)
                "db.store_impl.SQLiteMemoryDeleteStore.collect_prunable_ids",
                return_value=[],
            ),
            patch("db.maintenance.prune_old_memories", return_value=prune_result),
            patch("agent.commands.memory_data_ops._emit_prune_event") as emit,
        ):
            mock_h = MagicMock()
            mock_h.__enter__ = MagicMock(return_value=mock_h)
            mock_h.__exit__ = MagicMock(return_value=False)
            mock_h.open.return_value = mock_h
            mock_helper_cls.return_value = mock_h
            ops.memory_prune(MagicMock(), ctx, ["--days", "14"])
        emit.assert_not_called()
        # count==0 path writes a plain message and returns before write_success
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("Nothing is prunable" in line for line in lines)
        assert not out.write_success.called


class TestEmitPruneEvent:
    def test_appends_delete_event_from_config_dir(self) -> None:
        from agent.commands.memory_data_ops import _emit_prune_event

        fake_store = MagicMock()
        with (
            patch(  # mock-patch-ok: _emit_prune_event binds ConfigLoader through a local import
                "shared.config_loader.ConfigLoader"
            ) as cl,
            patch(
                "agent.memory.jsonl_store.JsonlMemoryStore",
                return_value=fake_store,
            ) as store_cls,
        ):
            cl.return_value.load.return_value = {
                "memory": {"memory_jsonl_dir": "/tmp/mem"}
            }
            _emit_prune_event("id-xyz")
        store_cls.assert_called_once_with(Path("/tmp/mem") / "memories.jsonl")
        fake_store.append_event.assert_called_once_with("delete", "id-xyz")

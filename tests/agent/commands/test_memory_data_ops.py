"""tests/agent/commands/test_memory_data_ops.py

Characterization tests for MemoryDataOps.memory_list / memory_search.

These two methods previously had no direct test coverage (only exercised via
stubbed test doubles in cmd_memory.py's dispatch tests) — added here to lock
behavior before extracting the shared summary-preview formatting logic.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from agent.commands.memory_data_ops import MemoryDataOps
from agent.memory.models import MemoryMaintenanceResult
from agent.memory.store import MemoryStore
from agent.repl_input_controller import (
    InputBusyError,
    InputOutcome,
    InputRequest,
    InputResult,
    PromptKind,
)
from agent.services.maintenance_jobs import (
    ApprovalDecision,
    ApprovalLevel,
    JobState,
    MaintenanceJobRegistry,
    StoreTarget,
)
from db.config import DbConfig
from db.helper import SQLiteHelper
from shared.config_loader import ConfigLoader

from tests.agent._config_test_defaults import PERMISSIVE_SQLITE_VEC_SO


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


def _controller_answering(
    text: str, outcome: InputOutcome = InputOutcome.COMPLETED
) -> MagicMock:
    """A stand-in input controller whose submit returns one scripted result."""
    ctl = MagicMock()
    ctl.submit = AsyncMock(
        return_value=InputResult(InputRequest(PromptKind.NORMAL, ""), outcome, text)
    )
    return ctl


def _make_ops() -> tuple[MemoryDataOps, MagicMock]:
    ctx = MagicMock()
    out = MagicMock()
    return MemoryDataOps(ctx, out), out


def _make_ops_with_registry() -> tuple[
    MemoryDataOps, MagicMock, MaintenanceJobRegistry
]:
    """Ops whose context carries the one registry instance the command path uses (REQ-005).

    A real `MaintenanceJobRegistry` is attached so the approval decision the handler reads is
    the registry's own, not a stand-in.
    """
    ops, out = _make_ops()
    registry = MaintenanceJobRegistry()
    ops._ctx.services_required.job_registry = registry
    return ops, out, registry


_SCHEMA_SQL = """
CREATE TABLE memories (
    memory_id   TEXT PRIMARY KEY,
    memory_type TEXT NOT NULL CHECK(memory_type IN ('semantic','episodic')),
    source_type TEXT NOT NULL DEFAULT 'conversation',
    session_id  INTEGER,
    turn_id     TEXT,
    project     TEXT NOT NULL DEFAULT '',
    repo        TEXT NOT NULL DEFAULT '',
    branch      TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL,
    summary     TEXT NOT NULL DEFAULT '',
    tags        TEXT NOT NULL DEFAULT '[]',
    importance  REAL NOT NULL DEFAULT 0.5,
    pinned      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE VIRTUAL TABLE memories_fts USING fts5(memory_id UNINDEXED, content, summary, tags);
CREATE TABLE memories_vec (memory_id TEXT PRIMARY KEY, embedding BLOB);
CREATE TABLE memory_links (src_id TEXT, dst_id TEXT);
"""


def _session_config(tmp_path: Path) -> DbConfig:
    """The typed configuration whose session DB is the temp file the store runs against."""
    return DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=str(tmp_path / "session.sqlite"),
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
        sqlite_vec_so=PERMISSIVE_SQLITE_VEC_SO,
    )


def _session_store(tmp_path: Path) -> MemoryStore:
    """A real `MemoryStore` on a temp session DB: the boundary the handler must use (REQ-005)."""
    cfg = _session_config(tmp_path)
    with SQLiteHelper("session", db_config=cfg).open(write_mode=True) as db:
        db.executescript(_SCHEMA_SQL)
        db.commit()
    return MemoryStore(db_config=cfg)


def _isolate_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ConfigLoader at a temp root whose memory_jsonl_dir is under tmp_path."""
    archive_dir = tmp_path / "archive"
    (tmp_path / "agent.toml").write_text(f'memory_jsonl_dir = "{archive_dir}"\n')
    monkeypatch.setattr(
        "shared.config_loader.resolve_config_dir",
        lambda config_dir=None: tmp_path,
    )
    monkeypatch.setattr(ConfigLoader, "_allowed_files", None)
    return archive_dir


def _mem_for(store: MemoryStore) -> MagicMock:
    """A `MemoryServices` stand-in that carries the store the run executes on."""
    mem = MagicMock()
    mem.store = store
    return mem


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


class TestMemoryListLimit:
    """Numeric-limit cases for `memory_list`: bound enforcement and shared-parser grammar."""

    @pytest.mark.parametrize("tokens", [["0"], ["201"]])
    def test_rejects_out_of_range(self, tokens) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.search_by_type.return_value = [_make_entry(summary="x")]
        ops.memory_list(mem, tokens)
        out.write_validation_error.assert_called_once()
        out.write.assert_not_called()

    @pytest.mark.parametrize(
        ("tokens", "expected_limit"),
        [
            (["5"], 5),
            (["+5"], 5),
            (["٣"], 3),
        ],
    )
    def test_applies_limit(self, tokens, expected_limit) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entries = [_make_entry(summary=f"s{i}") for i in range(10)]
        mem.store.search_by_type.return_value = entries
        ops.memory_list(mem, tokens)
        written = " ".join(c.args[0] for c in out.write.call_args_list)
        shown = sum(f"s{i}" in written for i in range(10))
        assert shown == expected_limit


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


class TestMemoryDisplayMasking:
    """REQ-005 (AC-1): stored user data is masked before it reaches normal CLI output."""

    def test_list_preview_is_masked_before_the_cap(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        # The leading credential is inside the 60-character window only if masking
        # happens before the cap.
        entry = _make_entry(
            summary="token=SECRETVALUE " + "z" * 100, content="ignored content"
        )
        mem.store.search_by_type.side_effect = lambda memory_type, limit: (
            [entry] if memory_type == "semantic" else []
        )

        ops.memory_list(mem, [])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert "SECRETVALUE" not in " ".join(lines)
        assert any("***MASKED***" in line for line in lines)

    def test_search_preview_is_masked(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(summary="api_key=SECRETVALUE", content="ignored content")
        hit = MagicMock()
        hit.entry = entry
        hit.score = 0.9
        mem.retriever.search.return_value = [hit]

        ops.memory_search(mem, ["query"])

        lines = [c.args[0] for c in out.write.call_args_list]
        assert "SECRETVALUE" not in " ".join(lines)
        assert any("***MASKED***" in line for line in lines)

    def test_show_writes_masked_summary_and_content(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(
            summary="summary with password=SECRETVALUE",
            content="body line\nanother password=SECRETVALUE",
        )
        mem.store.get_by_id.return_value = entry

        ops.memory_show(mem, ["id1"])

        lines = [c.args[0] for c in out.write.call_args_list]
        joined = "\n".join(lines)
        assert "SECRETVALUE" not in joined
        assert joined.count("***MASKED***") == 2
        # Non-sensitive text is displayed unchanged.
        assert "body line" in joined
        assert "another password=" in joined

    def test_show_path_valued_content_becomes_a_logical_identifier(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        entry = _make_entry(summary="", content="/opt/llm/rag.sqlite")
        mem.store.get_by_id.return_value = entry

        ops.memory_show(mem, ["id1"])

        joined = "\n".join(c.args[0] for c in out.write.call_args_list)
        assert "content:\nrag.sqlite" in joined
        assert "/opt/llm" not in joined


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
    async def test_unknown_writes_m03(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = []
        await ops.memory_delete(mem, ["abcdef12"])
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-03" in line for line in lines)
        # An unresolved id never reaches the write path.
        mem.store.delete.assert_not_called()

    async def test_ambiguous_writes_m04(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="abcdef12aa"),
            _make_entry(memory_id="abcdef12bb"),
        ]
        await ops.memory_delete(mem, ["abcdef12"])
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-04" in line for line in lines)
        mem.store.delete.assert_not_called()

    async def test_short_id_resolves_before_delete(self) -> None:
        ops, out, _registry = _make_ops_with_registry()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        mem.store.delete.return_value = MemoryMaintenanceResult(
            operation="delete", count=1, verified=True, ids=("abcdef1234",)
        )
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=_controller_answering("y"),
        ):
            await ops.memory_delete(mem, ["abcdef12"])
        # The write goes through the store accessor, not a connection the handler opens.
        mem.store.delete.assert_called_once_with("abcdef1234", stop=ANY)
        # no M-code emitted on success path
        lines = [c.args[0] for c in out.write.call_args_list]
        assert not any(m in "\n".join(lines) for m in ("M-03", "M-04"))


class TestMemoryPinShortId:
    def test_unknown_writes_m03(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = []
        ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-03" in line for line in lines)
        mem.store.pin.assert_not_called()

    def test_short_id_resolves_before_pin(self) -> None:
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 10
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        mem.store.pin.return_value = MemoryMaintenanceResult(
            operation="pin", count=1, verified=True, ids=("abcdef1234",)
        )
        ops.memory_pin(mem, ["abcdef12"], pin=True)
        # The write goes through the store accessor, which evaluates the limit inside
        # its own transaction (row 15), so the handler reads no count first.
        mem.store.pin.assert_called_once_with("abcdef1234", max_pinned=10)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert not any(m in "\n".join(lines) for m in ("M-03", "M-04", "M-05"))

    def test_ambiguous_writes_m04(self) -> None:
        ops, out = _make_ops()
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [
            _make_entry(memory_id="abcdef12aa"),
            _make_entry(memory_id="abcdef12bb"),
        ]
        ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-04" in line for line in lines)
        mem.store.pin.assert_not_called()


class TestAtomicPinLimit:
    """The limit is evaluated inside the write transaction, not before it (REQ-008).

    A handler that counts on a second connection can be overtaken by another run between the
    count and the write, so the limit is only atomic when the check and the write share the
    transaction the store owns.
    """

    def test_limit_is_never_exceeded_by_two_concurrent_pins(
        self, tmp_path: Path
    ) -> None:
        store = _session_store(tmp_path)
        for mid in ("pin-a", "pin-b"):
            with SQLiteHelper("session", db_config=_session_config(tmp_path)).open(
                write_mode=True
            ) as db:
                db.execute(
                    "INSERT INTO memories (memory_id, memory_type, content, updated_at, pinned) "
                    "VALUES (?, 'semantic', 'x', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), 0)",
                    (mid,),
                )
                db.commit()
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 1
        mem = _mem_for(store)

        def pin(mid: str) -> None:
            ops.memory_pin(mem, [mid], pin=True)

        threads = [
            threading.Thread(target=pin, args=(mid,)) for mid in ("pin-a", "pin-b")
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly one row is pinned: the second run evaluated the limit against the state the
        # first transaction committed, not against the state before it.
        assert store.pinned_count() == 1
        lines = [c.args[0] for c in out.write.call_args_list]
        assert sum(1 for line in lines if "M-05" in line) == 1

    def test_refused_pin_writes_m05(self) -> None:
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 1
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        mem.store.pin.return_value = MemoryMaintenanceResult(
            operation="pin", refused=True, ids=()
        )
        ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("M-05" in line for line in lines)

    def test_accepted_pin_writes_the_pinned_line(self) -> None:
        ops, out = _make_ops()
        ops._ctx.cfg.memory.memory_max_pinned = 10
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        mem.store.pin.return_value = MemoryMaintenanceResult(
            operation="pin", count=1, verified=True, ids=("abcdef1234",)
        )
        ops.memory_pin(mem, ["abcdef12"], pin=True)
        lines = [c.args[0] for c in out.write.call_args_list]
        assert not any(m in "\n".join(lines) for m in ("M-03", "M-04", "M-05"))
        assert any("pinned: abcdef1234" in line for line in lines)


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


class TestMemoryPruneEvents:
    async def test_prune_appends_delete_event_per_id(self) -> None:
        ops, _out, _registry = _make_ops_with_registry()
        mem = MagicMock()
        mem.store.prune.return_value = MemoryMaintenanceResult(
            operation="prune", count=2, verified=True, ids=("id-aaa", "id-bbb")
        )
        with (
            patch(
                "agent.commands.memory_data_ops.get_input_controller",
                return_value=_controller_answering("y"),
            ),
            patch("agent.commands.memory_data_ops._emit_prune_event") as emit,
        ):
            await ops.memory_prune(mem, ops._ctx, ["--days", "14"])
        emit.assert_has_calls([call("id-aaa"), call("id-bbb")])

    async def test_prune_no_pruned_ids_emits_no_events(self) -> None:
        ops, out, _registry = _make_ops_with_registry()
        mem = MagicMock()
        mem.store.prune.return_value = MemoryMaintenanceResult(operation="prune")
        with patch("agent.commands.memory_data_ops._emit_prune_event") as emit:
            await ops.memory_prune(mem, ops._ctx, ["--days", "14"])
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
            # Flat real shape: resolve_memory_jsonl_dir reads cfg["memory_jsonl_dir"].
            cl.return_value.load.return_value = {"memory_jsonl_dir": "/tmp/mem"}
            _emit_prune_event("id-xyz")
        store_cls.assert_called_once_with(Path("/tmp/mem") / "memories.jsonl")
        fake_store.append_event.assert_called_once_with("delete", "id-xyz")

    def test_real_loader_writes_prune_event_under_temp_root(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Real resolver + real JsonlMemoryStore, no mocks (REQ-005).

        Fails if the nested ``{"memory": {"memory_jsonl_dir": ...}}`` shape is
        reintroduced: the real resolver would then miss the flat key and fall
        back to ``/opt/llm/memory``, which the autouse guard rejects.
        """
        from agent.commands.memory_data_ops import _emit_prune_event

        archive_dir = tmp_path / "archive"
        (tmp_path / "agent.toml").write_text(f'memory_jsonl_dir = "{archive_dir}"\n')
        monkeypatch.setattr(
            "shared.config_loader.resolve_config_dir",
            lambda config_dir=None: tmp_path,
        )
        monkeypatch.setattr(ConfigLoader, "_allowed_files", None)

        _emit_prune_event("id-xyz")

        # Read the resolved dir back from the real loader, then assert the event
        # landed under the isolated temp root (never /opt/llm).
        cfg = ConfigLoader().load("agent.toml")
        memory_dir = Path(cfg["memory_jsonl_dir"])
        assert str(memory_dir).startswith(str(tmp_path))
        archive_file = memory_dir / "memories.jsonl"
        lines = [
            ln for ln in archive_file.read_text().strip().splitlines() if ln.strip()
        ]
        events = [json.loads(ln) for ln in lines]
        assert any(
            e["event"] == "delete" and e["memory_id"] == "id-xyz" for e in events
        )


class TestMemoryPruneRealLoader:
    """Exercise the real resolver + JSONL append through ``memory_prune`` (REQ-004, REQ-008).

    Isolates ``ConfigLoader`` to a temp root whose flat ``memory_jsonl_dir`` points
    under ``tmp_path``, and runs the prune for real through a ``MemoryStore`` on a temp-file
    DB. Asserts one ``delete`` event per pruned id lands under the isolated archive and the
    success line prints the count the transaction deleted.
    """

    def _seed(self, cfg: DbConfig) -> None:
        with SQLiteHelper("session", db_config=cfg).open(write_mode=True) as db:
            db.executescript(_SCHEMA_SQL)
            db.executemany(
                "INSERT INTO memories (memory_id, memory_type, content, updated_at) "
                "VALUES (?, ?, 'x', ?)",
                [
                    ("old-1", "semantic", "2025-01-01T00:00:00Z"),
                    ("old-2", "episodic", "2025-01-01T00:00:00Z"),
                ],
            )
            # recent-1 is anchored to SQL now so the row never ages out of the retention
            # window; a hardcoded date made this test fail once real time passed it.
            db.execute(
                "INSERT INTO memories (memory_id, memory_type, content, updated_at) "
                "VALUES ('recent-1', 'semantic', 'x', strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-1 days'))"
            )
            db.commit()

    async def test_prune_appends_delete_event_per_id(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        archive_dir = _isolate_config(tmp_path, monkeypatch)
        cfg = _session_config(tmp_path)
        self._seed(cfg)
        ops, out, _registry = _make_ops_with_registry()
        ops._ctx.cfg.db = cfg
        mem = _mem_for(MemoryStore(db_config=cfg))
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=_controller_answering("y"),
        ):
            await ops.memory_prune(mem, ops._ctx, ["--days", "14"])

        # One delete event per pruned id lands under the resolved archive.
        archive_file = archive_dir / "memories.jsonl"
        lines = [
            ln for ln in archive_file.read_text().strip().splitlines() if ln.strip()
        ]
        assert len(lines) == 2
        events = sorted(json.loads(ln)["memory_id"] for ln in lines)
        assert events == ["old-1", "old-2"]

        # Success line printed after the archive append.
        success_lines = [c.args[0] for c in out.write_success.call_args_list]
        assert any("Pruned 2 entries" in s for s in success_lines)

        # Rows actually deleted from the DB by the real prune.
        with SQLiteHelper("session", db_config=cfg).open() as db:
            remaining = db.fetchall("SELECT count(*) FROM memories")[0][0]
        assert remaining == 1

    async def test_reported_count_is_the_count_the_transaction_deleted(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A concurrent writer cannot change what the run reports (REQ-008).

        The prompt's count is read before the confirmation; the reported count is the count
        the run's own transaction deleted. When the two disagree, the transaction wins.
        """
        archive_dir = _isolate_config(tmp_path, monkeypatch)
        cfg = _session_config(tmp_path)
        self._seed(cfg)
        ops, out, _registry = _make_ops_with_registry()
        ops._ctx.cfg.db = cfg
        mem = _mem_for(MemoryStore(db_config=cfg))

        def concurrent_writer(request: InputRequest) -> InputResult:
            # A second writer removes one candidate between the count and the delete.
            with SQLiteHelper("session", db_config=cfg).open(write_mode=True) as db:
                db.execute("DELETE FROM memories WHERE memory_id = 'old-2'")
                db.commit()
            return InputResult(
                InputRequest(PromptKind.MEMORY_PRUNE, "prune:14d"),
                InputOutcome.COMPLETED,
                "y",
            )

        ctl = MagicMock()
        ctl.submit = AsyncMock(side_effect=concurrent_writer)
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=ctl,
        ):
            await ops.memory_prune(mem, ops._ctx, ["--days", "14"])

        # The prompt counted 2 candidates; the transaction deleted 1.
        success_lines = [c.args[0] for c in out.write_success.call_args_list]
        assert any("Pruned 1 entries" in s for s in success_lines)
        lines = [
            ln
            for ln in (archive_dir / "memories.jsonl").read_text().strip().splitlines()
            if ln.strip()
        ]
        assert [json.loads(ln)["memory_id"] for ln in lines] == ["old-1"]


def _job_id_from_output(out: MagicMock) -> str:
    """Read the job id the handler reported for the run it recorded."""
    for line in _reported_lines(out):
        if line.startswith("  job "):
            return line.split()[1]
    raise AssertionError("the handler did not report a job")


def _reported_lines(out: MagicMock) -> list[str]:
    """Every line the handler printed, including the refusals it printed as errors."""
    lines = [c.args[0] for c in out.write.call_args_list]
    lines += [c.args[0] for c in out.write_error.call_args_list]
    return lines


class TestDeleteConfirmationThroughController:
    @staticmethod
    def _mem() -> MagicMock:
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        mem.store.delete.return_value = MemoryMaintenanceResult(
            operation="delete", count=1, verified=True, ids=("abcdef1234",)
        )
        return mem

    @pytest.mark.parametrize(
        "outcome",
        [
            InputOutcome.TIMED_OUT,
            InputOutcome.CANCELLED,
            InputOutcome.EOF,
            InputOutcome.SHUTDOWN,
        ],
    )
    async def test_non_completed_outcome_never_deletes(
        self, outcome: InputOutcome
    ) -> None:
        ops, out, _registry = _make_ops_with_registry()
        mem = self._mem()
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=_controller_answering("y", outcome),
        ):
            await ops.memory_delete(mem, ["abcdef12"])
        mem.store.delete.assert_not_called()
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("Cancelled" in line for line in lines)

    async def test_other_answer_does_not_delete(self) -> None:
        ops, _out, _registry = _make_ops_with_registry()
        mem = self._mem()
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=_controller_answering("n"),
        ):
            await ops.memory_delete(mem, ["abcdef12"])
        mem.store.delete.assert_not_called()

    async def test_request_is_destructive_and_bound_to_the_memory_id(self) -> None:
        ops, _out, _registry = _make_ops_with_registry()
        ctl = _controller_answering("yes")
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=ctl,
        ):
            await ops.memory_delete(self._mem(), ["abcdef12"])
        request = ctl.submit.await_args.args[0]
        assert request.prompt_kind is PromptKind.MEMORY_DELETE
        assert request.operation_id == "abcdef1234"
        assert request.destructive is True

    async def test_busy_stdin_refuses_the_confirmation(self) -> None:
        ops, out, _registry = _make_ops_with_registry()
        mem = self._mem()
        ctl = MagicMock()
        ctl.submit = AsyncMock(side_effect=InputBusyError("unresolved"))
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=ctl,
        ):
            await ops.memory_delete(mem, ["abcdef12"])
        mem.store.delete.assert_not_called()
        lines = [c.args[0] for c in out.write.call_args_list]
        assert any("busy" in line for line in lines)
        assert any("Cancelled" in line for line in lines)

    def test_no_direct_input_call_remains(self) -> None:
        import agent.commands.memory_data_ops as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "input(" not in source.replace("get_input_controller(", "")


class TestDeleteRunThroughRegistry:
    """The destructive run is a job the registry decides, not a flag the handler reads (REQ-003)."""

    @staticmethod
    def _mem() -> MagicMock:
        mem = MagicMock()
        mem.store.get_by_id.return_value = None
        mem.store.list_entries.return_value = [_make_entry(memory_id="abcdef1234")]
        mem.store.delete.return_value = MemoryMaintenanceResult(
            operation="delete", count=1, verified=True, ids=("abcdef1234",)
        )
        return mem

    async def test_the_run_is_recorded_as_a_session_write_job(self) -> None:
        ops, out, registry = _make_ops_with_registry()
        mem = self._mem()
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=_controller_answering("y"),
        ):
            await ops.memory_delete(mem, ["abcdef1234"])
        job = registry.lookup(_job_id_from_output(out))
        assert job is not None
        assert job.operation == "delete"
        assert job.store is StoreTarget.SESSION
        # The confirmation the handler obtained is recorded as the grant for this run.
        assert job.grants == ["confirm"]
        assert job.state is JobState.COMPLETED
        assert job.verified is True

    async def test_a_run_the_registry_refuses_writes_nothing(self) -> None:
        ops, out, registry = _make_ops_with_registry()
        mem = self._mem()
        decision = ApprovalDecision(
            "job", ApprovalLevel.CONFIRM, False, detail="no grant recorded for this run"
        )
        with (
            patch(
                "agent.commands.memory_data_ops.get_input_controller",
                return_value=_controller_answering("y"),
            ),
            patch.object(registry, "authorize", return_value=decision),
        ):
            await ops.memory_delete(mem, ["abcdef1234"])
        mem.store.delete.assert_not_called()
        assert any(
            "no grant recorded for this run" in line for line in _reported_lines(out)
        )

    async def test_a_second_writer_on_the_same_store_is_refused(self) -> None:
        ops, out, registry = _make_ops_with_registry()
        mem = self._mem()
        running = registry.register(operation="prune", store=StoreTarget.SESSION)
        registry.authorize(running, confirmed=True)
        registry.start(running)
        with patch(
            "agent.commands.memory_data_ops.get_input_controller",
            return_value=_controller_answering("y"),
        ):
            await ops.memory_delete(mem, ["abcdef1234"])
        mem.store.delete.assert_not_called()
        assert any(running.job_id in line for line in _reported_lines(out))


class _FirstStepStore(MemoryStore):
    """Store whose cancellation hook fires on the first VM step, so a short statement stops.

    `interrupt_when` checks the event every 1000 VM steps, so a single-statement run finishes
    before the event is observed; the test needs the hook to fire at the start of the statement.
    """

    @contextmanager
    def _maintenance_connection(
        self, stop: threading.Event | None
    ) -> Generator[SQLiteHelper]:
        with SQLiteHelper("session", db_config=self._db_config).open(
            write_mode=True, row_factory=True
        ) as db:
            if stop is not None:
                db.interrupt_when(stop, check_every=1)
            yield db


class TestDeleteConsistencyUnderInterruption:
    """A rolled-back run reports nothing it did not commit (REQ-008)."""

    async def test_interrupted_delete_emits_no_event_and_keeps_the_row(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        archive_dir = _isolate_config(tmp_path, monkeypatch)
        cfg = _session_config(tmp_path)
        with SQLiteHelper("session", db_config=cfg).open(write_mode=True) as db:
            db.executescript(_SCHEMA_SQL)
            db.execute(
                "INSERT INTO memories (memory_id, memory_type, content, updated_at) "
                "VALUES ('m1', 'semantic', 'x', strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))"
            )
            db.commit()
        ops, _out, registry = _make_ops_with_registry()
        ops._ctx.cfg.db = cfg
        mem = _mem_for(_FirstStepStore(db_config=cfg))
        job = registry.register(operation="delete", store=StoreTarget.SESSION)
        job.stop_event.set()
        with (
            patch.object(ops, "_register_run", return_value=job),
            patch(
                "agent.commands.memory_data_ops.get_input_controller",
                return_value=_controller_answering("y"),
            ),
        ):
            await ops.memory_delete(mem, ["m1"])

        # The transaction rolled back, so the row is still there and the archive has no line
        # describing a change that never happened.
        assert mem.store.get_by_id("m1") is not None
        archive_file = archive_dir / "memories.jsonl"
        assert not archive_file.exists() or not archive_file.read_text().strip()
        recorded = registry.lookup(job.job_id)
        assert recorded is not None
        assert recorded.state is JobState.CANCELLED
        assert recorded.verified is False

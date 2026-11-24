"""tests/test_memory_rebuild_guard.py
Tests for the memory rebuild guard: the approval level declared for the operation decides
the run, the flag forms are recorded grants on the job record, and the run reports its job
id and terminal state.

Contracts under test (REQ-003, REQ-006; AC-3, AC-6):
- a rebuild run is registered as a job and the registry's approval level is the authority;
  `--confirm` and `--allow-loss` are recorded as grants, not an untracked bypass;
- a run with no recorded grant is refused and changes nothing, which is the summary the
  command has always shown for that case;
- the run reports the job id and the terminal state the registry recorded, including the
  paths that abort before any write.

The transaction boundary and the verified count measured after the commit are asserted with
the store accessor (`tests/agent/memory/test_memory_store.py`), and the postcondition before
the success line is the Phase 4 contract; neither is locked here.
"""

from __future__ import annotations

import inspect
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.commands.memory_rebuild_ops import MemoryRebuildOps
from agent.memory.models import MemoryImportResult
from agent.services.maintenance_jobs import (
    ApprovalLevel,
    JobState,
    MaintenanceJob,
    MaintenanceJobRegistry,
)

# Backing dir for rebuild backup writes in unit tests.
_TMP_JSONL_DIR = tempfile.mkdtemp(prefix="mem-guard-test-jsonl-")


@dataclass
class _Entry:
    """One stored memory, as the backup writer sees it."""

    memory_id: str


def _import_result(jsonl_count: int, inserted: int) -> MemoryImportResult:
    """The outcome the import path reports for one run (row 16's result shape)."""
    return MemoryImportResult(jsonl_count=jsonl_count, inserted=inserted, verified=True)


def _make_mem(jsonl_count: int = 5, sqlite_count: int = 3) -> MagicMock:
    mem = MagicMock()
    mem.ingestion._jsonl.count_all.return_value = jsonl_count
    mem.store.check_consistency.return_value = SimpleNamespace(
        memories=sqlite_count, fts=sqlite_count, vec=0
    )
    return mem


def _make_ops(
    jsonl_dir: str = _TMP_JSONL_DIR,
) -> tuple[MemoryRebuildOps, MagicMock, MaintenanceJobRegistry]:
    """Build one handler with the single registry instance the command path reaches."""
    registry = MaintenanceJobRegistry()
    ctx = MagicMock()
    ctx.services_required.audit_logger = None
    ctx.services_required.job_registry = registry
    ctx.cfg.memory.memory_embed_enabled = False
    ctx.cfg.memory.memory_jsonl_dir = jsonl_dir
    out = MagicMock()
    return MemoryRebuildOps(ctx, out), out, registry


def _recorded(registry: MaintenanceJobRegistry, job_id: str) -> MaintenanceJob:
    """Return the job the run recorded, so the assertions read one record."""
    job = registry.lookup(job_id)
    assert job is not None
    return job


def _lines(out: MagicMock) -> list[str]:
    """Collect every line the handler emitted, whichever output method wrote it."""
    calls = [
        call
        for name in ("write", "write_error", "write_success")
        for call in getattr(out, name).call_args_list
    ]
    return [str(call[0][0]) for call in calls]


# --- The run is a registered job ---


def test_handlers_are_async_so_the_run_can_be_tracked() -> None:
    assert inspect.iscoroutinefunction(MemoryRebuildOps.rebuild)
    assert inspect.iscoroutinefunction(MemoryRebuildOps.reindex)


async def test_run_is_recorded_as_a_job() -> None:
    ops, _, registry = _make_ops()
    mem = _make_mem()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 5),
    ):
        result = await ops.rebuild(mem, ["--confirm"])
    job = _recorded(registry, result.job_id)
    assert job.operation == "rebuild"
    assert job.session_target


# --- The flags are recorded grants, not the authority ---


async def test_flags_are_recorded_as_grants_on_the_job() -> None:
    ops, _, registry = _make_ops()
    mem = _make_mem()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 5),
    ):
        result = await ops.rebuild(mem, ["--confirm", "--allow-loss"])
    job = _recorded(registry, result.job_id)
    assert job.grants == ["confirm", "allow_loss"]
    decision = registry.grant(result.job_id)
    assert decision is not None
    assert decision.approved is True


async def test_run_with_no_recorded_grant_is_refused_and_changes_nothing() -> None:
    ops, _, registry = _make_ops()
    mem = _make_mem()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 0),
    ) as mock_import:
        result = await ops.rebuild(mem, [])
        mock_import.assert_not_called()
    assert result.dry_run is True
    decision = registry.grant(result.job_id)
    assert decision is not None
    assert decision.approved is False
    assert decision.level is ApprovalLevel.CONFIRM


async def test_refusal_names_the_job_id() -> None:
    ops, out, _ = _make_ops()
    mem = _make_mem()
    result = await ops.rebuild(mem, [])
    assert any(f"job {result.job_id}" in line for line in _lines(out))
    # The pre-run summary is still shown for the refused run.
    _, rows = out.write_table.call_args[0]
    assert any("5" in str(row) for row in rows)


async def test_run_reports_the_job_id_and_the_terminal_state() -> None:
    ops, out, registry = _make_ops()
    mem = _make_mem()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 5),
    ):
        result = await ops.rebuild(mem, ["--confirm"])
    assert _recorded(registry, result.job_id).state is JobState.COMPLETED
    assert any(
        f"job {result.job_id} {JobState.COMPLETED}" in line for line in _lines(out)
    )


# --- The run's own guards still report through the job ---


async def test_backup_failure_ends_the_run_as_failed_naming_the_job_id() -> None:
    # A path that exists as a file cannot be the backup dir, so the backup raises.
    handle = tempfile.NamedTemporaryFile(prefix="mem-guard-not-a-dir-", delete=False)
    ops, out, registry = _make_ops(jsonl_dir=handle.name)
    mem = _make_mem()
    mem.store.list_entries.return_value = [_Entry(memory_id="m1")]
    try:
        with patch(
            "agent.commands.memory_rebuild_ops.import_from_jsonl",
            return_value=_import_result(5, 5),
        ) as mock_import:
            result = await ops.rebuild(mem, ["--confirm"])
            mock_import.assert_not_called()
    finally:
        Path(handle.name).unlink()
    assert result.error is not None
    assert _recorded(registry, result.job_id).state is JobState.FAILED
    assert any(f"job {result.job_id}" in line for line in _lines(out))


async def test_import_without_a_recorded_loss_grant_is_refused() -> None:
    """The `backup` without `allow_loss` ValueError is surfaced with the job id (row 16)."""
    ops, out, registry = _make_ops()
    mem = _make_mem()

    def _import(*args, **kwargs):
        raise ValueError("backup without allow_loss: memories would be lost")

    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl", side_effect=_import
    ):
        result = await ops.rebuild(mem, ["--confirm"])
    assert result.error is not None
    assert _recorded(registry, result.job_id).state is JobState.FAILED
    assert any(f"job {result.job_id}" in line for line in _lines(out))


async def test_loss_without_a_recorded_grant_is_refused() -> None:
    ops, out, registry = _make_ops()
    mem = _make_mem(jsonl_count=5, sqlite_count=3)
    mem.store.list_entries.return_value = [_Entry(memory_id="not-in-archive")]
    mem.ingestion._jsonl.iter_records.return_value = []
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 5),
    ) as mock_import:
        result = await ops.rebuild(mem, ["--confirm"])
        mock_import.assert_not_called()
    assert result.loss_blocked is True
    assert any("would be lost" in line for line in _lines(out))
    assert any(f"job {result.job_id}" in line for line in _lines(out))
    assert _recorded(registry, result.job_id).state is JobState.FAILED


async def test_loss_grant_lets_the_run_proceed() -> None:
    ops, _, registry = _make_ops()
    mem = _make_mem(jsonl_count=5, sqlite_count=3)
    mem.store.list_entries.return_value = [_Entry(memory_id="not-in-archive")]
    mem.ingestion._jsonl.iter_records.return_value = []
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 5),
    ):
        result = await ops.rebuild(mem, ["--confirm", "--allow-loss"])
    assert result.loss_blocked is False
    assert result.inserted == 5


# --- The pre-run summary ---


async def test_summary_reports_the_archive_and_the_current_counts() -> None:
    ops, out, _ = _make_ops()
    mem = _make_mem(jsonl_count=42, sqlite_count=17)
    await ops.rebuild(mem, [])
    _, rows = out.write_table.call_args[0]
    assert any("42" in str(row) for row in rows)
    assert any("17" in str(row) for row in rows)


async def test_refused_run_shows_the_dry_run_message() -> None:
    ops, out, _ = _make_ops()
    mem = _make_mem()
    await ops.rebuild(mem, [])
    assert any("dry-run" in line.lower() for line in _lines(out))


# --- The postcondition still runs for the granted run (Phase 4 locks its order) ---


async def test_granted_run_runs_the_consistency_check() -> None:
    ops, _, _ = _make_ops()
    mem = _make_mem()
    with patch(
        "agent.commands.memory_rebuild_ops.import_from_jsonl",
        return_value=_import_result(5, 5),
    ):
        await ops.rebuild(mem, ["--confirm"])
    assert mem.store.check_consistency.call_count >= 2


async def test_refused_run_does_not_run_the_extra_consistency_check() -> None:
    ops, _, _ = _make_ops()
    mem = _make_mem()
    await ops.rebuild(mem, [])
    assert mem.store.check_consistency.call_count == 1

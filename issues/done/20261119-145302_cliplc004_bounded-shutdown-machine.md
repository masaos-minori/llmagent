# Implement one bounded shutdown state machine across jobs, persistence, WAL, and MCP processes

## Priority
High

## Summary
Apply one global deadline to REPL shutdown, stop every writer before the final checkpoint, publish backups atomically, and pass the remaining deadline into MCP process termination.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 4). Related archived work: `issues/done/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`, `issues/done/20261021-220228_star001_clarify-mcp-subprocess-termination-ownership-and-remove-unused-spawned-subprocess-list-return.md`, `issues/done/20261021-093421_turn005_background-tasks-not-cancelled-at-shutdown.md`.

Evidence (`Explicit in code`, by `rg` and reading): `scripts/agent/resource_shutdown_coordinator.py` bounds the WAL checkpoint and backup with `asyncio.wait_for(..., timeout=_SHUTDOWN_TIMEOUT_S)` (lines 84-113); `scripts/agent/wal_checkpoint_manager.py:183` copies the WAL with `shutil.copy2(wal_file, wal_backup_path)` straight to the final filename, and the name includes a session tag (line 181); `backup_sync` runs `_backup_step` in `asyncio.to_thread` (line 132). The claims about unbounded persistence, task gathering, HTTP close, and hooks, checkpoint ordering, and the HTTP lifecycle's own signal windows are from the backlog and `Needs confirmation`.

## Problem
Local timeouts coexist with unbounded steps; a timed-out async wrapper does not stop its worker thread; a checkpoint can run before every writer has stopped; an interrupted backup can leave a partial file under its final name; MCP termination has its own windows rather than the REPL's overall deadline.

## Reason for Change
Data-integrity and process-lifecycle risk; documentation claims bounded exit while maintenance documentation says workers are joined until completion.

## Implementation Intent
One state machine and one deadline: close the write gate, settle writers and jobs, persist one immutable snapshot, run the final checkpoint and backup, then shut down MCP, HTTP clients, and hooks with the remaining time. Unfinished work stays tracked and is reported as unknown, never as success.

## Target Files or Areas
- `scripts/agent/resource_shutdown_coordinator.py`, `repl.py`, `session_persister.py`, `wal_checkpoint_manager.py`
- `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `http_lifecycle_process_terminator.py`
- The maintenance job registry of `issues/20261119-145301_cliplc003_maintenance-job-framework.md`; shutdown integration tests under `tests/agent/`

## Required Changes
- A configurable global deadline; stop accepting turns, commands, transitions, approvals, and DB writes first; stop or settle jobs and background writers; persist one snapshot; checkpoint and back up after writers settle; shut down MCP, HTTP clients, and close hooks using remaining time; run blocking hooks off the event loop.
- WAL and backup: stop support in the synchronous checkpoint with progress-handler cancellation; stop-aware retry waits; wait for worker completion before advancing; copy to a temporary file in the destination directory, flush, fsync, verify size or hash, rename atomically, delete temporaries on failure; remove the session id from database-wide backup names.
- MCP: pass an absolute deadline or remaining timeout into `shutdown_all()`; bound SIGTERM and SIGKILL confirmation by it; keep process ownership when termination tasks time out or are cancelled; report per-server outcomes; define second-SIGINT force exit.
- Result model per step: `completed`, `timed_out`, `failed`, `not_started`, `outcome_unknown`; redact paths and raw exceptions in user output.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change (governance_01, governance_05); do not write or simulate that approval.
- No writer may run after the final checkpoint starts.

## Acceptance Criteria
- [ ] Shutdown returns within the configured global deadline; MCP shutdown cannot extend it.
- [ ] No writer runs after the final checkpoint starts.
- [ ] Partial backups never appear under final names.
- [ ] Timed-out workers and processes remain tracked; user output distinguishes incomplete work from success.

## Testing Expectations
- Non-cooperative task and active maintenance worker; session persistence timeout; WAL timeout with worker cancellation.
- Backup interruption and atomic publication; multiple MCP servers under one deadline; second-SIGINT behavior.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Replace contradictory bounded-shutdown statements with the implemented guarantee; document step ordering and outcome states.

## Out of Scope
- MCP process ownership and restart (`issues/20261119-145305_cliplc007_mcp-process-ownership.md`); log redaction (`issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`).

## Dependencies
- Depends on `issues/20261119-145301_cliplc003_maintenance-job-framework.md` (jobs must be tracked to be stopped). Blocks `issues/20261119-145305_cliplc007_mcp-process-ownership.md` and `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`.

## Unresolved Questions
- `不明`: default global deadline value.
- `不明`: whether a non-interruptible worker should be abandoned (marked `outcome_unknown`) or waited for.

## AI Implementation Instruction
Add the no-writer-after-checkpoint and partial-backup tests first. Keep ADR text unchanged unless an approval record is part of the change. Stop and report if a step cannot report `outcome_unknown` truthfully.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145302
- **Related target files**: `scripts/agent/resource_shutdown_coordinator.py`, `scripts/agent/repl.py`, `scripts/agent/session_persister.py`, `scripts/agent/wal_checkpoint_manager.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `scripts/agent/http_lifecycle_process_terminator.py`

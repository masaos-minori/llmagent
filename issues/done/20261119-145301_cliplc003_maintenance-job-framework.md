# Consolidate Session, RAG, and Memory maintenance into verified, cancellable jobs

## Priority
High

## Summary
Create one maintenance-job framework for Session database work, RAG consistency and rebuild operations, and Memory rebuild, reindex, prune, and recovery, with job ids, cancelability, approval levels, progress states, and verified results.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 3). Related archived work: `issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md`, `plans/done/20261115-050112_dbreview006_maintenance-error-semantics.md`.

Evidence (`Explicit in code`, by listing): `scripts/agent/services/db_maintenance_service.py`, `rag_maintenance_service.py`, `scripts/agent/commands/memory_rebuild_ops.py`, `memory_data_ops.py`, `scripts/db/maintenance.py`, `recovery.py`, and `helper.py` exist; `scripts/agent/services/maintenance_jobs.py` does not exist (to be created). The behavior claims (`to_thread` workers surviving cancellation, synchronous Memory rebuild, success before postcondition checks, misleading RAG and Memory repair names, direct SQLite access in the Memory CLI) are from the backlog and `Needs confirmation`.

## Problem
Long-running operations have inconsistent execution and safety: workers can outlive their cancelled awaiters, Memory rebuild and reindex may block the event loop, a `--confirm` flag may stand in for approval, success may be reported before verification, command names overstate what they do, and the Memory CLI couples directly to the schema, allowing pin and prune races.

## Reason for Change
Data-safety and operability risk; shutdown (`issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`) must manage every tracked job.

## Implementation Intent
Every long-running action has a job id, target store, cancelability classification, approval level, state, and verified result; CLI commands use service APIs; success is emitted only after postconditions pass.

## Target Files or Areas
- `scripts/agent/commands/cmd_session.py`, `memory_rebuild_ops.py`, `memory_data_ops.py`
- `scripts/agent/services/db_maintenance_service.py`, `rag_maintenance_service.py`, Memory services and stores
- `scripts/db/maintenance.py`, `recovery.py`, `helper.py`
- New `scripts/agent/services/maintenance_jobs.py` and tests (the backlog's `scripts/agent/memory/rebuild_ops.py`, `import_ops.py`, `write_ops.py` locations are `不明`)

## Required Changes
- A job registry (id, operation, target store, state, start time, cancelability, session generation, structured result); `/jobs`, `/jobs status <id>`, `/jobs cancel <id>`; integration with Ctrl-C and shutdown; states `completed`, `cancelled`, `failed`, `outcome_unknown`.
- Move Memory rebuild and reindex off the event loop; pass stop events where SQLite progress handlers apply; define cancellation for integrity check, purge, FTS rebuild, vector cleanup, `VACUUM`, restore, and JSONL import; consider a separate process for non-interruptible operations; never leave an untracked worker after caller cancellation.
- Memory: dry-run does not mutate; `--confirm` alone is not approval; loss-permitting rebuild needs HIGH-equivalent request-bound confirmation; preview counts with safe identifiers; portable, atomic, verified backup; success only after consistency checks; verify FTS and vector counts after reindex; move pinned count, prune selection, delete, and pin updates behind `MemoryServices` with atomic pin-limit and prune selection.
- RAG and repair: rename the vector operation to orphan pruning unless real regeneration is implemented; report removed and remaining rows; verify FTS counts after rebuild; replace nonexistent repair command guidance; add a structured `repairable` state.

## Constraints
- Uses the request-bound confirmation of `issues/20261119-145259_cliplc001_repl-input-controller.md` and session ownership of `issues/20261119-145300_cliplc002_session-transition-generation.md`.
- Renaming commands is user-visible; document it.

## Acceptance Criteria
- [ ] Every long-running maintenance operation is tracked; cancelling the CLI task cannot leave an untracked writer.
- [ ] Destructive Memory rebuild requires request-bound approval and a verified complete backup before destructive work.
- [ ] Success appears only after postconditions pass.
- [ ] CLI Memory commands do not access SQLite directly; RAG and Memory command names match behavior.

## Testing Expectations
- Cancellation for each maintenance category; shutdown with active jobs; Memory rebuild backup, data-loss confirmation, rollback, and verification.
- Memory pin and prune concurrency; RAG FTS count verification and vector-prune semantics; repair-guidance command existence.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Job states and cancellation guarantees; corrected Memory and RAG repair descriptions; replace "REPL remains responsive" with precise job behavior.

## Out of Scope
- Global shutdown deadline and WAL checkpoint (`issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`).

## Dependencies
- Depends on `issues/20261119-145259_cliplc001_repl-input-controller.md` and `issues/20261119-145300_cliplc002_session-transition-generation.md`. Blocks `issues/20261119-145302_cliplc004_bounded-shutdown-machine.md`.

## Unresolved Questions
- `不明`: which operations can be interrupted safely and which need a separate process.
- `不明`: existing job manager or scheduler infrastructure (none was found by listing).
- `不明`: exact Memory transaction boundaries (the Memory internals are not read yet).

## AI Implementation Instruction
Read the Memory service and store code before designing job boundaries. Add cancellation and no-untracked-writer tests first. Do not change data semantics beyond what is listed. Stop and report any operation that cannot be made safely cancellable.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145301
- **Related target files**: `scripts/agent/commands/cmd_session.py`, `scripts/agent/commands/memory_rebuild_ops.py`, `scripts/agent/commands/memory_data_ops.py`, `scripts/agent/services/db_maintenance_service.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/db/maintenance.py`, `scripts/db/recovery.py`, `scripts/db/helper.py`

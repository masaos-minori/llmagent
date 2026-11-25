## Goal

Create the reload transaction that owns the snapshot, the commit, the reverse-order rollback, and the
degraded state, so a failed commit restores every reversible service (REQ-005, stage reporting;
REQ-006, snapshot and restore; REQ-007, irreversible services gated before commit; REQ-012, degraded
guard).

## Scope
**Release unit**: R4-transaction-and-restore

## Assumptions
- No snapshot or undo model exists anywhere in `scripts/agent/services/` today; `ConfigReloadOutcome`
  has no stage field (`config_reload.py:43`).
- Restore writes values back into the same section object, because `LlmHotConfigHandler`,
  `HistoryManager`, `ServiceSyncer`, and the display commands hold references to the section
  instances (Plan `Assumptions`).
- The MCP lifecycle is not reversible and is gated before any live mutation (OD-06); the transaction
  records which path applied rather than undoing it.
- The snapshot type lives here, not in `scripts/agent/history.py`, which is 21501 B against the
  24576 B module-size gate.

## Design decisions
- Undo tokens are captured during commit and replayed in reverse order (OD-05), combined with a
  section-value snapshot; a full `AgentConfig` rebuild cannot restore a service that derived state
  from the old values.
- `degraded` is a stage, not an exception: a failing rollback reports the services left inconsistent
  and the guard refuses a later `/reload`.

## Alternatives considered
- Rebuilding `AgentConfig` from the previous raw dict — rejected (OD-05).
- Snapshotting every attribute of every service — rejected as unmaintainable across three services
  and four sections.

## Implementation
### Target file
`scripts/agent/services/config_reload_transaction.py` (new)

### Procedure
Define `ReloadTransaction` (new), `ReloadStage` (new), and `UndoToken` (new) with the section and
conversation snapshot, `prepare()`, `commit()`, reverse-order `rollback()`, and degraded reporting.

### Method
- `ReloadStage` (new) is a `StrEnum` with `prepared`, `committed`, `rolled_back` (new), `degraded`.
- `prepare()` takes the typed candidates from row 5 and the prompt-source read from
  `scripts/agent/prompt_source.py`; it performs no mutation.
- `commit()` applies in a fixed order and records one `UndoToken` (new) per applied step.
- `rollback()` replays the tokens in reverse order and names each service whose restore failed.

### Details
- The transaction holds no socket, no file lock, and no database handle; `/reload` stays a
  single-threaded CLI operation.
- The degraded guard is read by row 8 and refuses a later `/reload` after a `degraded` stage.

## Compatibility considerations
- New module; no existing caller. `config_reload.py` (row 6) becomes its only driver.

## Security considerations
- Rollback reporting names services and fields, never configuration values.

## Rollback considerations
- Revert the Phase 4 commit.

## Validation plan
- `uv run pytest tests/agent/services/test_config_reload_transaction.py -q` (row 26)
- `uv run python tools/check_module_size.py`
- `uv run ruff check scripts tests`, `uv run mypy scripts`, `uv run lint-imports`

## Completion criteria
- Every commit-failure point restores all reversible services in reverse order; a rollback failure
  yields `degraded` and names the services left inconsistent.

## Out of Scope
- The per-service snapshot and restore APIs (rows 16, 17, 18).
- The CLI reporting (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-194130 | 20261125-194130 | R4-transaction-and-restore 20261125: implemented as recorded in this procedure's Blocker Log |
| 2 | Add or update tests per Validation plan | Completed | 20261125-194130 | 20261125-194130 | row 26 R4 20261125: targeted run tests/agent/services tests/agent/commands tests/shared tests/agent/test_history_manager.py = 2821 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-194130 | 20261125-194130 | R4 gate 20261125: full suite 14722 passed 5 skipped, diff-cover 100 percent over 482 lines, integration 146 passed 1 skipped, mypy 466 files clean, lint-imports 6 kept, ruff format and check clean, check_module_size OK, generate_reference_table --check no drift, check_docs_structure OK |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | R4 execution (2026-11-25): the snapshot model lives in the new leaf module `scripts/shared/config_undo.py`, not here. `.importlinter`'s `shared-is-leaf` contract forbids `shared` importing `agent`, and rows 16, 17, 18 return the token from `scripts/shared/`. This module owns `ReloadStage`, `CommitPhase`, `PreparedStep`, and `ReloadTransaction` only, and holds no `ctx` reference | Yes | 2026-11-25 |
| 1 | R4 execution (2026-11-25): `prepare()` is not a transaction method. Prepare runs in `scripts/agent/services/config_reload.py` and `ServiceSyncer.prepare_llm` / `prepare_runtime_tools`, which capture the snapshot before any mutation and register one `PreparedStep` per reversible service | Yes | 2026-11-25 |
| 1 | R4 execution (2026-11-25): the degraded guard is interim. `ReloadTransaction` refuses a further step or commit once degraded, and `ConfigReloadService._degraded_services` refuses the next reload on the same instance. The cross-command guard needs `PendingConfigState` (row 8, R5) because `scripts/agent/commands/cmd_config.py` builds a new service per command | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 (reload transaction and stage), REQ-006 (service snapshot and restore), REQ-007 (no live lifecycle call), REQ-012 (degraded guard); AC-3, AC-5
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `scripts/agent/services/config_reload_transaction.py`
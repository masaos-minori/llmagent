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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 26 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

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

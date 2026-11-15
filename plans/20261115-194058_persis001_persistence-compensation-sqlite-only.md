# Turn persistence compensation only fires on `sqlite3.Error`, leaving partial turns on other exceptions

## Goal
Make a turn's persistence all-or-nothing for every in-turn exception after at least one
write has committed, not only for `sqlite3.Error`: a turn that has persisted at least one row
must guarantee that a later in-turn exception either completes the turn's persistence or
compensates it — never leave half of it.

## Priority
Medium

## Scope
- **In-Scope**:
  - Ensure a non-`sqlite3.Error` exception raised after a successful in-turn write triggers
    the same compensation as `sqlite3.Error` (delete-above-marker or restore-pre-rewrite-image
    plus memory-snapshot restore), so no partial turn survives.
  - Preserve the `ConversationPersistenceError` semantics: it still means nothing was
    persisted (`is_partial=False`), while a mid-turn exception that committed rows is recorded
    as partial (`is_partial=True`).
  - Keep `BaseException`/`CancelledError` propagation semantics intact (AC-5): propagation
    must still escape `execute_all_tool_calls` and `orchestrator`; only the persistence side
    effect changes.
  - Add unit tests covering a non-`sqlite3.Error` exception after a partial commit and confirm
    the DB is left without the partial turn's rows.
- **Out-of-Scope**:
  - Changes to repository write transactions, connection handling, or the append-only
    compensation-delete mechanics.
  - Any change to tool-execution gating, approval, or loop-detection logic.
  - Broadening compensation to startup or recovery paths outside a running turn.
  - Changing the disabled-by-default guard policies or unrelated tool-execution paths.

- **Dependencies**: `N/A: none`

## Background
`scripts/agent/turn_persistence.py` implements the turn-persistence boundary that makes one
agent turn's session-DB persistence all-or-nothing (AC-001). Every turn write is delegated to
`AgentSession._message_repo` on a worker thread. Each public write method (`save`,
`save_many`, `save_phase_grouped`, `replace_messages`) wraps the worker call in
`try/except sqlite3.Error` and routes to `_fail_from_error` (`scripts/agent/turn_persistence.py:107-108`,
`:121-122`, `:138-139`, `:156-157`), which calls `_compensate` (`scripts/agent/turn_persistence.py:180`),
restores `conv.history` to the turn-start snapshot element-wise and resets `undo_floor`
(`scripts/agent/turn_persistence.py:222-223`), and raises `ConversationPersistenceError`
chaining the underlying error (`scripts/agent/turn_persistence.py:224-226`).

`orchestrator._execute_turn` (`scripts/agent/orchestrator.py:168`) distinguishes two cases on
failure: a caught `ConversationPersistenceError` (which knows compensation already ran,
`is_partial=False`, `scripts/agent/orchestrator.py:183-190`) and a generic
`except BaseException` (`scripts/agent/orchestrator.py:192-199`) that only records
`error_kind`/`is_partial` (via `partial_text`) and re-raises. The generic branch never calls
compensation.

Callers of the persistence symbols (verified): `TurnPersistence` is bound by
`scripts/agent/context.py` and `scripts/agent/session.py`; `ConversationPersistenceError` is
caught by `scripts/agent/orchestrator.py` and `scripts/agent/repl_input_loop.py`. The
`is_partial` signal is derived from `partial_text`, set by
`scripts/agent/error_injection_service.py` and `scripts/agent/llm_turn_executor.py`.

## Problem
The compensation trigger is scoped to `sqlite3.Error` alone. When a turn raises any other
exception after at least one write already committed successfully, neither `TurnPersistence`
nor `orchestrator._execute_turn` compensates:

- The committed rows remain in the session DB (append-only rows past the turn marker are
  never deleted).
- `conv.history` is restored to the turn-start snapshot in memory.
- The result is a permanent divergence: the persisted DB contains the partial turn while the
  in-memory conversation does not. On the next load, the turn is reconstructed from DB rows
  that memory has forgotten.

Evidence: `turn_persistence.py` methods catch only `sqlite3.Error` (lines for
`save`/`save_many`/`save_phase_grouped`/`replace_messages`); `_fail_from_error` is the sole
compensation entry point and is only reached from those handlers. `orchestrator.py`
`_execute_turn` catches `ConversationPersistenceError` and then `BaseException` with no
compensation call.

## Reason for Change
The all-or-nothing contract documented at the top of `turn_persistence.py` ("a whole turn is
either fully persisted or fully compensated") is violated for every non-`sqlite3.Error`
failure after a partial commit. Such exceptions are plausible: a worker-thread write can
succeed and a later phase in the same turn raise `RuntimeError`/`ValueError`, or an
`asyncio.CancelledError` can land after a commit. No production occurrence is known yet, so
this is preventive, but the divergence is silent and accumulates across turns.

## Implementation Intent
Make compensation independent of the exception type once a write has committed. At the
responsibility level: a turn that has persisted at least one row must guarantee that a later
in-turn exception either completes the turn's persistence or compensates it — never leave half
of it. Decide at the boundary whether (a) broaden the `except` in each `TurnPersistence`
write method to also catch and compensate non-`sqlite3.Error` exceptions, or (b) centralize
the decision in `orchestrator._execute_turn` so any post-commit exception routes through the
same compensation path as `ConversationPersistenceError`. Preserve the distinction that
`ConversationPersistenceError` means "nothing persisted" (`is_partial=False`) while a
mid-turn exception may have committed rows (`is_partial=True`). Do not change the
transactional guarantees of the repository writes themselves.

## Requirements
- `REQ-001`: A non-`sqlite3.Error` exception raised after a successful in-turn write triggers
  the same compensation as `sqlite3.Error` (delete-above-marker or restore-pre-rewrite-image
  plus memory-snapshot restore), so no partial turn survives.
- `REQ-002`: `ConversationPersistenceError` still means nothing was persisted
  (`is_partial=False`); a mid-turn exception that committed rows is recorded as partial
  (`is_partial=True`).
- `REQ-003`: `BaseException`/`CancelledError` propagation still escapes
  `execute_all_tool_calls` and `orchestrator`; only the persistence side effect changes.
- `REQ-004`: Compensation does not fire on exceptions raised before any write committed; those
  keep propagating unchanged.
- `REQ-005`: Existing `sqlite3.Error` compensation behavior and the
  `ConversationPersistenceError` `is_partial=False` contract are unchanged.
- `REQ-006`: Compensation runs on a worker thread like the writes (single-connection
  invariant).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/turn_persistence.py` | Modify | Make compensation independent of the exception type once a write has committed: route non-`sqlite3.Error` exceptions after a committed write through the same `_compensate` + memory-snapshot restore path, expose a committed-state signal the orchestrator can read, and keep compensation on a worker thread. | REQ-001, REQ-002, REQ-004, REQ-006 | Four write methods catch only `sqlite3.Error` and route to `_fail_from_error`→`_compensate` (`scripts/agent/turn_persistence.py:107-108,121-122,138-139,156-157,207-226`) | `tests/agent/test_turn_persistence.py` | Verified |
| `scripts/agent/orchestrator.py` | Modify | Route any post-commit in-turn exception through the same compensation path as `ConversationPersistenceError`, preserving `is_partial=True` for a mid-turn exception that committed rows and `is_partial=False` otherwise. | REQ-001, REQ-002 | `_execute_turn` catches `ConversationPersistenceError` (183) then `BaseException` (192) with no compensation call; `is_partial` derived from `partial_text` (194) | `tests/agent/test_orchestrator.py` | Verified |
| `tests/agent/test_turn_persistence.py` | Modify | Add a non-`sqlite3.Error` exception after a partial commit and confirm the partial rows are deleted and the memory snapshot restored; regression-confirm the current `sqlite3.Error` path. | REQ-001, REQ-005 | Existing compensation tests for the `sqlite3.Error` path (`scripts/agent/turn_persistence.py`) | `tests/agent/test_turn_persistence.py` | Verified |
| `tests/agent/test_orchestrator.py` | Modify | Confirm a non-`sqlite3.Error` exception after a commit is compensated end-to-end through the orchestrator and that propagation still escapes. | REQ-001, REQ-003 | Existing orchestrator compensation/propagation tests (`scripts/agent/orchestrator.py:168`) | `tests/agent/test_orchestrator.py` | Verified |

Rules:
- One row per file. A directory, glob pattern, component/module name, file group, or vague
  phrase MUST NOT appear as a row.
- Test, configuration, schema, migration, deployment, and documentation files are their own
  rows when they require modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/context.py` | `restore_messages`/`undo_floor` semantics used by the memory-snapshot restore in compensation. | `scripts/agent/turn_persistence.py` / REQ-001 |
| `scripts/agent/error_injection_service.py` | How `partial_text` (the `is_partial` signal) is set on exceptions. | `scripts/agent/orchestrator.py` / REQ-002 |
| `scripts/agent/llm_turn_executor.py` | Where a mid-turn exception can be raised after a write committed and how `partial_text` is attached. | `scripts/agent/turn_persistence.py` / REQ-001 |
| `scripts/agent/repl_input_loop.py` | Another `ConversationPersistenceError` consumer whose propagation semantics must be preserved. | `scripts/agent/orchestrator.py` / REQ-003 |
| `scripts/db/` message repository | The append-only compensation-delete-above-marker and single-transaction write guarantees that must not change. | `scripts/agent/turn_persistence.py` / REQ-004, REQ-006 |

## Acceptance Criteria
- A turn that commits at least one row then raises a non-`sqlite3.Error` exception is
  compensated: no rows above the turn-start marker remain in the session DB. (REQ-001)
- `conv.history` is restored to the turn-start snapshot on that failure path. (REQ-001)
- The exception still propagates end-to-end (observable by callers). (REQ-003)
- Existing `sqlite3.Error` compensation behavior and the `ConversationPersistenceError`
  `is_partial=False` contract are unchanged. (REQ-005)
- Compensation does not fire on an exception raised before any write committed. (REQ-004)

## Tests
- Unit tests in `tests/agent/test_turn_persistence.py`: simulate a successful write followed
  by a `RuntimeError`/`ValueError`/`CancelledError` and assert the partial rows are deleted
  and the memory snapshot is restored. (REQ-001)
- Regression tests confirm the current `sqlite3.Error` path is unchanged. (REQ-005)
- Orchestrator-level tests confirm a non-`sqlite3.Error` exception after a partial commit is
  compensated end-to-end and still propagates. (REQ-001, REQ-003)
- Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on the two touched files,
  plus `uv run pytest` on the persistence and orchestrator test trees. (REQ-005, REQ-006)

## Documentation Impact
Update the failure-behavior description in turn-persistence documentation if it currently
states compensation is limited to SQLite errors; restate it as applying to any in-turn
exception after a partial commit. Do not add implementation-level details forbidden by
`skills/DESIGN.md` "Docs content policy — remove". Driven by REQ-001.

## Assumptions
- The non-`sqlite3.Error` exception that must be compensated is raised inside the turn after
  a write committed, not during startup/recovery outside a running turn (out of scope).
- A committed-state signal can be exposed by `TurnPersistence` without changing the
  repository's transactional behavior.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which exception types actually reach the turn after a partial commit in practice (e.g. `RuntimeError`, `ValueError`, `CancelledError`). | Observed exception types on the partial-commit path. | Choose the broadest safe handler consistent with the constraint not to fire before any write committed; confirm the realistic trigger set from the current source. | False |
| UNK-02 | Should compensation for a mid-turn exception attempt to complete the turn's remaining writes first, or always roll back? | Operational preference for partial-vs-rollback on mid-turn failure. | Default to roll back (match the existing `sqlite3.Error` behavior); note as a design choice if completion-first is desired. | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`' rows.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/turn_persistence.py` | Modify | Medium | 4 | N/A | None |
| `scripts/agent/orchestrator.py` | Modify | High | 12 | N/A | None |
| `tests/agent/test_turn_persistence.py` | Modify | Low | 3 | N/A | None |
| `tests/agent/test_orchestrator.py` | Modify | Low | 21 | N/A | None |

## Design
Classification: Path B. The change alters the runtime all-or-nothing persistence contract
(AC-001) across two modules and leaves an open design decision about where the compensation
decision lives; it touches a runtime-facing boundary, so Path B analysis applies. No
persisted-schema change is involved.

**Architecture / dependency findings.** `orchestrator._execute_turn`
(`scripts/agent/orchestrator.py:168`) imports `ConversationPersistenceError` from
`turn_persistence` and handles it at `scripts/agent/orchestrator.py:183`; the fallback
`except BaseException` at `scripts/agent/orchestrator.py:192` records `is_partial` from
`partial_text` (`scripts/agent/orchestrator.py:194`) and re-raises without compensating.
`turn_persistence` has few imports (asyncio, sqlite3, logging) and no internal callers of
`_compensate` besides `_fail_from_error`. `orchestrator.py` is the higher-churn file (12
commits vs 4 in 30 days), so most of the behavioral surface area to protect in tests lives in
`tests/agent/test_orchestrator.py` (21 commits in 30 days).

**Open design decision — where compensation is decided.** Two valid approaches:
- **(a) Broaden the per-method `except` in `TurnPersistence`.** Each write method already
  knows whether its own write committed. Catching non-`sqlite3.Error` there compensates
  exceptions raised *inside* the write call. Limitation: a post-commit exception raised later
  in the turn (during tool execution, compression, or cancellation) is outside every write
  method's `try`, so this alone does not cover it.
- **(b) Centralize in `orchestrator._execute_turn`.** Any post-commit exception routes through
  the compensation path like `ConversationPersistenceError`. But `orchestrator` cannot see
  whether a write committed — that knowledge lives in `TurnPersistence`. So (b) requires
  exposing a committed-state signal from `TurnPersistence` (e.g. a flag set when a write
  commits), and honoring the constraint that compensation not fire before any write committed
  (REQ-004).

Key finding feeding the decision: because a compensable exception can occur outside the write
call, a committed-state signal from `TurnPersistence` is needed under either approach; (b) is
the more robust place to route it, while (a) closes the in-write-call gap. Final selection is
a plan-to-implementation-procedure decision; both preserve the
`ConversationPersistenceError` `is_partial=False` contract and the `is_partial=True` signal
for a mid-turn committed exception. This does not block writing the plan.

**Preservation constraints.** Do not change the repository's transactional behavior
(`save_phase_grouped` single transaction, append-only compensation delete above the marker).
Compensation must run on a worker thread like the writes (single-connection invariant,
REQ-006). Do not widen compensation to fire on exceptions raised before any write committed
(REQ-004). Keep `BaseException`/`CancelledError` propagation escaping
`execute_all_tool_calls` and `orchestrator` (REQ-003, AC-5).

## Implementation steps
Each step cites the exact file path(s) via `Implementation Target Files` rows. Steps are small
enough to be independently revertable.

1. **Phase 1: Committed-state signal** (`scripts/agent/turn_persistence.py`)
   - [ ] Track whether at least one write committed for the turn (a flag set after a
     successful worker-thread write returns). (REQ-004)
2. **Phase 2: Compensation on non-`sqlite3.Error`** (`scripts/agent/turn_persistence.py`,
   `scripts/agent/orchestrator.py`)
   - [ ] Route a non-`sqlite3.Error` exception after a committed write through the same
     `_compensate` + memory-snapshot restore path, on a worker thread, and record
     `is_partial=True`. Choose (a) per-method broadening and/or (b) orchestrator centralization
     per the Design decision. (REQ-001, REQ-002, REQ-006)
   - [ ] Ensure compensation does not fire before any write committed. (REQ-004)
3. **Phase 3: Preserve propagation and existing contract** (`scripts/agent/orchestrator.py`)
   - [ ] Keep `ConversationPersistenceError` meaning `is_partial=False`; keep the exception
     escaping end-to-end. (REQ-002, REQ-003, REQ-005)
4. **Phase 4: Tests** (`tests/agent/test_turn_persistence.py`, `tests/agent/test_orchestrator.py`)
   - [ ] Add non-`sqlite3.Error` after partial-commit compensation tests and propagation tests;
     regression-confirm the `sqlite3.Error` path. (REQ-001, REQ-003, REQ-005)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/turn_persistence.py` | Unit | `uv run pytest tests/agent/test_turn_persistence.py`; `uv run ruff check scripts/agent/turn_persistence.py`; `uv run mypy --no-namespace-packages scripts/agent/turn_persistence.py` | Non-`sqlite3.Error` after commit is compensated; `sqlite3.Error` path unchanged |
| `scripts/agent/orchestrator.py` | Integration | `uv run pytest tests/agent/test_orchestrator.py`; `uv run ruff check scripts/agent/orchestrator.py`; `uv run mypy --no-namespace-packages scripts/agent/orchestrator.py` | Post-commit exception compensated end-to-end and still propagates |
| Full persistence/orchestrator trees | Regression | `uv run pytest tests/agent/` | Existing compensation/propagation tests pass |

## Risks
- **Risk**: Broadening the handler catches an exception that should propagate without
  compensation (before any write committed). → **Mitigation**: Gate compensation on the
  committed-state signal so it never fires before a write commits (REQ-004).
- **Risk**: Changing `orchestrator._execute_turn`'s `BaseException` handling weakens
  propagation (AC-5). → **Mitigation**: Only change the persistence side effect; re-raise the
  exception after compensation so it still escapes (REQ-003).
- **Risk**: `orchestrator.py` is high-churn (12 commits/30d) with extensive existing tests
  (21 commits/30d in `test_orchestrator.py`). → **Mitigation**: Rely on the existing test
  suite as regression coverage and add targeted tests for the new path.
- **Risk**: Compensation must run on a worker thread (single-connection invariant). →
  **Mitigation**: Offload compensation via `asyncio.to_thread` like the writes (REQ-006).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Committed-state signal (`scripts/agent/turn_persistence.py`) | Pending | — | — | REQ-004 |
| 2 | Compensation on non-`sqlite3.Error` (`scripts/agent/turn_persistence.py`, `scripts/agent/orchestrator.py`) | Pending | — | — | REQ-001, REQ-002, REQ-006 |
| 3 | Preserve propagation and existing contract (`scripts/agent/orchestrator.py`) | Pending | — | — | REQ-002, REQ-003, REQ-005 |
| 4 | Tests (`tests/agent/test_turn_persistence.py`, `tests/agent/test_orchestrator.py`) | Pending | — | — | REQ-001, REQ-003, REQ-005 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261115-081702_persis001_persistence-compensation-sqlite-only.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261115-194058
- **Related target files**: `scripts/agent/turn_persistence.py`, `scripts/agent/orchestrator.py`, `tests/agent/test_turn_persistence.py`, `tests/agent/test_orchestrator.py`

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem, Required Changes | `scripts/agent/turn_persistence.py`, `scripts/agent/orchestrator.py` | 2 | AC 1, AC 2, AC 3 | `test_turn_persistence.py`, `test_orchestrator.py` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent, Constraints | `scripts/agent/orchestrator.py` | 2, 3 | AC 4 | `test_orchestrator.py` | Confirmed by repository evidence |
| REQ-003 | Constraints (AC-5) | `scripts/agent/orchestrator.py` | 3 | AC 3 | `test_orchestrator.py` | Confirmed by repository evidence |
| REQ-004 | Constraints | `scripts/agent/turn_persistence.py` | 1, 2 | AC 5 | `test_turn_persistence.py` | Confirmed by repository evidence |
| REQ-005 | Acceptance Criteria | `scripts/agent/turn_persistence.py` | 2, 4 | AC 4 | regression test | Confirmed by repository evidence |
| REQ-006 | Constraints | `scripts/agent/turn_persistence.py` | 2 | AC (worker thread) | `test_turn_persistence.py` | Confirmed by repository evidence |

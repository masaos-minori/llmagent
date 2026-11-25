## Goal

Persist from the one snapshot the step captured, and bound the reads the persister performs, so a shutdown snapshot is atomic and cannot run past the deadline (REQ-007: bounded single-snapshot persistence; AC-3).

## Scope
**Release unit**: R4-sequence-and-snapshot (Phase 4)

- In scope: `capture_snapshot()`, `persist_session_memories()`, `persist_session_diagnostics()`, and the reads they perform.
- Out of scope: registering the step (row 7) and the step record and reporting (row 5).

## Assumptions

- `persist_session_diagnostics()` already accepts a snapshot (`scripts/agent/session_persister.py:211-214`) and captures one itself when none is given (`scripts/agent/session_persister.py:221`), so the parameter must stay optional: existing callers pass no snapshot (`tests/agent/workflow/test_session_diagnostics_wiring.py:113`, `tests/agent/test_repl_error_handling.py:73`).
- The gap this row closes is that a snapshot can be captured inside the persist call, and that the reads carry no deadline; it is not that two snapshot generations are taken by the REPL path (`scripts/agent/repl.py:94-102` already feeds one snapshot to both persist calls).
- Reads must keep working after the write gate closes (row 3): the snapshot step reads while writes are refused (REQ-006, REQ-008).

## Design decisions

- The step owns the snapshot: when a snapshot is supplied, the persister never captures another one, so the values the step records and the values written to the store come from one read (REQ-007).
- The optional parameter is kept rather than made required: making it required would break the callers listed above for no behavioral gain.
- Reads are bounded by the remaining deadline passed by the step, and a read that cannot finish is reported as a partial snapshot rather than retried past the deadline. The check is before each read group, never inside a query, so a partial result is well defined.
- The partial capture is labeled in two places: a `partial_sections` key in the persisted summary, and one console warning line. The coordinator's step record stays `completed` — the step ran and wrote what it could; `timed_out` remains the outcome when the coordinator's `wait_for` cuts the step off.
- `_workflow_counts()` opens a new write-mode `StateStore` (`scripts/agent/workflow/state_store.py:61-62`), which the closed write gate would refuse; it is admitted because row 5 runs the step inside `authorize("persist_snapshot")`. Skipping the group when the deadline is spent also avoids opening a connection that late.
- Compatibility impact: the two persist methods gain an optional keyword-only `deadline`, so every existing caller keeps compiling and behaving as today. The private read helpers `_workflow_counts()` and `_rag_summary()` gained a return element; they have no caller outside this module (verified).

## Alternatives considered

- capture the snapshot inside each persist call — rejected: two reads of a live session can disagree, which is the non-atomicity the Plan's Problem section names.

## Implementation
### Target file
`scripts/agent/session_persister.py`

### Procedure
1. Keep `capture_snapshot()` (`scripts/agent/session_persister.py:118-138`) unchanged as the single capture point. Do not mark the snapshot as "the step's snapshot": `SessionPersistenceSnapshot` is a frozen value object also consumed by `scripts/agent/services/session_transition.py:157-159`, and a marker field would change a shared type for no behavioral gain. The single-capture contract is enforced by the persist calls never re-capturing a supplied snapshot.
2. In `persist_session_diagnostics()` (`scripts/agent/session_persister.py:211-214`), keep using the supplied snapshot and the implicit capture at `scripts/agent/session_persister.py:221` only when none is given (already the case; verified, no change needed beyond the docstring).
3. Apply the same rule to `persist_session_memories()` (`scripts/agent/session_persister.py:317-326`) so both persist calls read from the same snapshot object.
4. Add a keyword-only `deadline` (a monotonic instant, `None` means no deadline) to `persist_session_diagnostics()` and `persist_session_memories()`, and pass it to the two synchronous read groups `_workflow_counts()` and `_rag_summary()`. Each group checks the deadline before it starts and returns a `skipped` flag when it is spent; the summary then carries `partial_sections` naming what was not read, plus one console warning line. `persist_session_memories()` skips the memory write outright when the deadline is spent and reports the skip.
5. Keep the constructor (`scripts/agent/session_persister.py:107-116`) unchanged so the existing wiring in `scripts/agent/repl.py:86-88` keeps working.
6. Row 5 was amended in the same batch to hand the step body its window (`register_snapshot_step(Callable[[float], Awaitable[None]])`), which is what supplies this row's `deadline`: the reads stop early instead of being cut off mid-write by the coordinator's `wait_for`.

### Method
- The snapshot is a value object produced once: the persist calls consume it and never re-read the session, so atomicity comes from data ownership rather than from locking.
- Deadline handling is a check before each read group, not a timeout inside a single query, so a partial snapshot is well defined.

### Details
- A partial capture names the sections it did not read in `partial_sections`; the sections it holds are persisted normally. The step's own outcome is the coordinator's record (row 5), and `timed_out` there means the step was cut off before it wrote anything (REQ-012).
- `deadline` is a monotonic instant, not a duration: both read groups are checked against the same instant, so a step that spends its window on the first group cannot start the second.

### Companion test files
- `tests/agent/test_session_persister.py`
  - Procedure: assert one captured snapshot is passed to both persist methods, and that a supplied snapshot is used instead of a fresh read.
  - Validation: `uv run pytest tests/agent/test_session_persister.py -q` (REQ-007; AC-3).

## Compatibility considerations

- The snapshot parameter stays optional, so every existing caller keeps compiling and behaving as today.
- Callers that pass no snapshot keep today's implicit capture, which is the path the tests listed above exercise.

## Security considerations

- Snapshot contents stay inside the diagnostic store; nothing new is written to the log (REQ-013).

## Rollback considerations

- Revert this row's commit with row 30: the single-snapshot expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/session_persister.py` | Unit | `uv run pytest tests/agent/test_session_persister.py -q` | one capture per shutdown step, bounded reads, partial-snapshot reporting pass |
| `scripts/agent/session_persister.py` | Unit | `uv run pytest tests/agent/workflow/test_session_diagnostics_wiring.py tests/agent/test_repl_error_handling.py -q` | callers that pass no snapshot keep working |

## Completion criteria

- A shutdown step produces exactly one snapshot and both persist calls consume that object.
- A read that cannot finish inside the deadline yields a reported partial snapshot rather than an unbounded wait.

## Out of Scope

- Step registration, step records, and the write gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-095800 | 20261125-100100 | Step 3b corrections applied before implementing: no marker field on `SessionPersistenceSnapshot` (shared with `scripts/agent/services/session_transition.py:157-159`), `deadline` is a keyword-only monotonic instant on both persist methods passed down to the two read groups, partial capture is labeled by `partial_sections` plus one warning line, row 5 amended to hand the step body its window |
| 2 | Add or update tests per Validation plan | Completed | 20261125-100100 | 20261125-100400 | companion row 30: `TestSingleSnapshotAndBoundedReads` (7 cases) — supplied snapshot never recaptured, both writes read the one snapshot, spent deadline labels both read groups, live deadline changes nothing, deadline checked before each group, memories skipped and reported past the deadline. 31 passed; the no-snapshot callers in `tests/agent/workflow/test_session_diagnostics_wiring.py` and `tests/agent/test_repl_error_handling.py` keep passing unchanged |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-104000 | 20261125-105200 | full R4+R5 batch gate ran: 14215 passed / 5 skipped (`-n logical -m "not integration and not production_paths_allowed and not repo_scan"`), diff-cover Pass, mypy Pass, lint-imports 6 kept, bandit Pass, check_docs_quality Pass, check_module_size Pass, reference-table/manifest drift Pass. `pre-commit run --all-files` still fails only on the two pre-existing hooks (workitem-structure on rows 45-54 and `issues/20261123-120131_02_unknowns.md`), identical to the R2 baseline.

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
- **Requirement ID**: REQ-007 (bounded single-snapshot persistence)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/session_persister.py`, `tests/agent/test_session_persister.py`

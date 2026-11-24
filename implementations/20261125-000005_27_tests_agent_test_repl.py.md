## Goal

Replace the two expectations this Plan deliberately changes in the REPL test file — the checkpoint-before-cancel ordering and the session-tag backup name — while keeping the path-containment and symlink expectations holding against the temporary-then-publish flow (REQ-001: one owner and sequence; REQ-006: bounded sequence; REQ-009: safe backup name and publication; AC-1, AC-3).

## Scope
**Release unit**: R4-sequence-and-snapshot (Phase 4) + R5-checkpoint-and-backup (Phase 5), executed last; moved from R1 by user decision 2026-11-25, consistent with this file's Design decision that it must land with rows 5, 6, 7 and 8

- In scope: the ordering test, the backup-name assertions, and the containment expectations in this file.
- Out of scope: the coordinator (row 5), the checkpoint manager (row 6), and the input-loop acceptance cases (row 22).

## Assumptions

- `test_checkpoint_completes_before_pending_task_cancelled` (`tests/agent/test_repl.py:1331-1372`) is the ordering lock: its docstring cites `REQ-RSC001B-1` and it asserts the checkpoint finishes before a pending task is cancelled. Owner decision OD-01 supersedes `REQ-RSC001B-1` (`plans/done/20260908-065641_plan.md:4,17,84`), so this test is the one that must change, not the code that satisfies it.
- The name expectations are the session-id assertion at `tests/agent/test_repl.py:1465` and the tag-shape assertions at `tests/agent/test_repl.py:1526-1530`, inside the path-rejection and writability block at `tests/agent/test_repl.py:1400-1530`.
- The containment and symlink expectations in the same block are not part of the change and must keep passing against the new publication flow.

## Design decisions

- Rewrite the ordering test rather than delete it: the sequence still has an order worth pinning, and the new name states it — settle writers, then snapshot, then checkpoint, then cancel-driven steps.
- Assert the new name shape as a shape, not as a fixed string: the name is database-scoped (basename plus timestamp) and contains no session identifier, so the test asserts the absence of the session tag as well as the presence of the basename.
- Keep the containment cases unchanged and add a case that a failed publication leaves no file at the final name, which is the property the temporary-then-publish flow exists to provide.
- Compatibility impact: this file is the regression gate for rows 5, 6, 7 and 8; it must land with them, not before.

## Alternatives considered

- leave the old ordering test and add a second one — rejected: two tests asserting opposite orders is a contradiction that fails at the next run.

## Implementation
### Target file
`tests/agent/test_repl.py`

### Procedure
1. Rename and rewrite `test_checkpoint_completes_before_pending_task_cancelled` (`tests/agent/test_repl.py:1331-1372`) to assert the settle-before-checkpoint order, and replace the `REQ-RSC001B-1` docstring citation with the superseding requirement `REQ-001` and `REQ-006` of this Plan.
2. Replace the session-tag name assertion at `tests/agent/test_repl.py:1465` with the database-scoped name, and update the tag-shape assertions at `tests/agent/test_repl.py:1526-1530` to assert the basename plus timestamp shape and the absence of a session identifier.
3. Keep the path-rejection and writability cases at `tests/agent/test_repl.py:1400-1530` unchanged, and add a case that an interrupted backup leaves no file at the final name.
4. Add a case that the persist step produces one step record and that the `finally` calls only `close_resources()` (row 7).

### Method

- Each changed assertion names the requirement it now enforces, so a future reader can tell a deliberate change from a regression.

### Details

- The new ordering assertion compares recorded step names, not wall-clock timing, so the test is not sensitive to scheduling.

## Compatibility considerations

- This file is asserted by rows 5, 6, 7 and 8; landing it before those rows makes it fail, landing it after leaves those rows unguarded.

## Security considerations

- The new name assertions check that no session identifier appears in a logged path (REQ-009, REQ-013).

## Rollback considerations

- Revert this row's commit together with rows 5, 6 and 7: the ordering and name expectations are the contract those rows implement.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_repl.py` | Unit | `uv run pytest tests/agent/test_repl.py -q` | settle-before-checkpoint order, database-scoped name, containment and no-partial-file cases pass |
| `tests/agent/test_repl.py` | Unit | `uv run pytest tests/agent/test_resource_shutdown_coordinator.py tests/agent/test_wal_checkpoint_manager.py -q` | the coordinator and checkpoint expectations agree with the new order |

## Completion criteria

- No test in this file asserts the superseded order or a session-tag name, and every containment and symlink expectation still passes.

## Out of Scope

- The coordinator and checkpoint implementations, and the input-loop acceptance cases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row is the test row |
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
- **Requirement ID**: REQ-001 (one owner and sequence), REQ-006 (bounded sequence), REQ-009 (safe backup name and publication)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `tests/agent/test_repl.py`, `scripts/agent/resource_shutdown_coordinator.py`, `scripts/agent/wal_checkpoint_manager.py`

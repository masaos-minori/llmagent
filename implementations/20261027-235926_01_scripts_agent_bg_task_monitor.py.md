## Goal

Clear the paused task type's entry in `_bg_pause_state` when that same task name
completes cleanly, so the opt-in background-failure pause gains a resume path
(REQ-1: clean completion resumes a paused task type). Failure counting, threshold
notification, the blocking check, and the opt-in constructor wiring stay behaviorally
unchanged (REQ-2).

## Scope

- One branch inside `BgTaskMonitor.on_task_done` (`scripts/agent/bg_task_monitor.py`).
- The cancelled branch and the failure ladder (`_count_failure`, `_report_first_failure`,
  `_report_threshold_failure`, `_notify_threshold_breach`) are not touched.
- No new public API, no config key, no change to `bg_pause_state` property or
  `check_pause_state()`.

## Assumptions

- Owner decision (Plan Assumptions, 2026-10-27): keep the pause mechanism, add
  success-based clear, do not wire `pause_on_critical_failure` or the threshold through
  config (Plan OUT-1).
- A cancelled task must NOT resume the pause: DR-002 semantics in the `on_task_done`
  docstring (L76-78) — cancellation is neither success nor failure.
- Cleared state must satisfy the consumer contract at `orchestrator.py` L159
  (`check_pause_state()` unpacks `(is_paused, paused_names)`); that file is a reference
  file and is not modified here.
- Cross-plan overlap check (`tools/check_plan_target_overlaps.py`): no finding names
  this Plan; no sequencing dependency against sibling plans.

## Design decisions

- Clear the pause entry in the same branch that already resets the failure streak on
  clean completion (`if exc is None:` at L90-91) — the resume is the same event as the
  counter reset, keeping the semantics symmetric with no new state or API surface.
- Use `self._bg_pause_state.pop(task_name, None)` directly: no public reset method is
  added (none exists today — repo grep confirms `_bg_pause_state` is written only at
  `_notify_threshold_breach` L168-169 and never cleared), and the existing
  `bg_pause_state` property/tests keep working untouched.

## Alternatives considered

- Clearing on cancellation too: rejected — DR-002 (cancelled is neither success nor
  failure) and Plan Assumptions.
- Adding a public `reset_bg_pause_state(task_name)` method: rejected — no caller exists
  today and the Plan fixes scope to the internal branch; clearing per-task-name inside
  `on_task_done` is sufficient.
- Clearing all task types on any success: rejected — pause and clear are both
  per-task-type (Plan Risk mitigation: same-type clean completion only).

## Implementation

### Target file

`scripts/agent/bg_task_monitor.py`

### Procedure

In `BgTaskMonitor.on_task_done`, extend the clean-completion branch so it also clears
this task name's pause entry alongside the existing `count = 0`.

### Method

Change only the `if exc is None:  # clean completion resets the streak` branch (L90-91):

```python
if exc is None:  # clean completion resets the streak and resumes a paused type
    count = 0
    self._bg_pause_state.pop(task_name, None)
```

No other branch, import, signature, or constant changes. `pop(task_name, None)` is a
no-op when no pause entry exists, so the common (never-paused) path stays side-effect
free.

### Details

- `task_name` is `task.get_name()` captured at L83; the same key used by
  `_notify_threshold_breach` when setting `_bg_pause_state[task_name] = True` (L168-169).
- The cancelled branch (`task.cancelled()` → `count = 0`, L86-87) must not clear the
  pause entry — keep it exactly as is.
- The failure ladder (L92-97) is unchanged.

## Compatibility considerations

- `orchestrator.py` L159 `check_pause_state()` gate and `_on_pause_blocked` are read-only
  consumers; clearing an entry makes them return `(False, [])` without any change there.
- Existing characterization tests stay green: `test_threshold_reached_with_pause_enabled_sets_pause_state`,
  `test_threshold_reached_with_pause_disabled_leaves_pause_state_empty`, and
  `TestHandleTurnPauseGuard` in `tests/agent/test_orchestrator.py` (reference, not modified).
- The `bg_pause_state` property (getter/setter) and `check_pause_state()` signatures are
  unchanged.

## Security considerations

N/A: in-memory per-task-type flag clearing on a clean task completion; no input, path,
credential, or persistence surface.

## Rollback considerations

N/A: revert the commit (single-branch, single-file change).

## Validation plan

| Check | Command | Expected |
|-------|---------|----------|
| targeted tests | `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py tests/agent/test_orchestrator.py -k "pause or threshold or failure"` | all green |
| full suite | `uv run pytest` | green |
| config-boundary grep | `grep -rn "pause_on_critical_failure" configs/ scripts/agent/services/` | no new config wiring appears (Plan OUT-1) |
| lint/type/security | `uv run ruff check . && uv run ruff format --check . && uv run mypy scripts/ && uv run bandit -c bandit.yaml -r scripts/ -q` | clean |

## Completion criteria

- After a threshold breach pauses a task type (opt-in), a clean completion of the same
  task name clears the entry so `check_pause_state()` returns `(False, [])` (REQ-1).
- Cancellation and other-task-name successes do not clear the entry (covered by seq 02
  tests).
- The existing pause characterization tests pass without edits (REQ-2).

## Out of Scope

- Config wiring of `pause_on_critical_failure` or `BG_FAILURE_THRESHOLD` (Plan OUT-1).
- Changes to `scripts/agent/orchestrator.py`, `repl_input_loop.py`, or scheduling /
  health-check internals (Plan OUT-2).
- New test cases (seq 02 document) and documentation updates (seq 03 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test cases are owned by the seq 02 procedure document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A here: docs update is the seq 03 procedure document |

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
- **Requirement ID**: `REQ-1` (clean completion clears the pause entry), `REQ-2` (counting/notification/blocking/opt-in unchanged)
- **Source issue**: `issues/20261026-225036_bgmonitor001_reset-background-failure-pause.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-085246_bgmonitor001_reset-background-failure-pause.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-235926
- **Related target files**: `scripts/agent/bg_task_monitor.py`

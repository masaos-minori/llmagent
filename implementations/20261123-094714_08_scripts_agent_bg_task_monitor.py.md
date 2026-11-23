## Goal

Register background tasks with type, instance id, session id, and generation, group failures by type, and log exception class names instead of raw reasons (REQ-005 monitor registration and redaction; AC-2).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 27 is covered as this document's companion. Registration callers are seq 09 and seq 10-11.

## Assumptions
- Current code verified: failure keys come from `task.get_name()` (`bg_task_monitor.py:81`), and raw `exc` text is interpolated with %s at `bg_task_monitor.py:115,130-133,139-142`.
- Tasks registered without a type keep working through the existing name-based keys (plan Design).

## Design decisions
- Add a `register()` (new) method taking task, task_type, session_id, and generation, storing the task metadata; failure counting and reporting group by task type instead of bare name (REQ-005).
- Logs and audit use `type(exc).__name__` only; raw exception text never appears (AC-2).

## Alternatives considered
- Dropping name-based tracking entirely: rejected — the plan keeps existing name keys valid for untyped registrations.

## Implementation
### Target file
`scripts/agent/bg_task_monitor.py`
### Procedure
1. Add the `register` API and per-task metadata (type, instance id, session id, generation).
2. Rework `_count_failure`, `_report_first_failure`, and `_report_threshold_failure` to key by task type when metadata exists and by name otherwise.
3. Replace exception-text interpolation with the exception class name in all three report paths and the `_on_error` notification payload text.
### Method
Metadata dict keyed by task; existing threshold logic unchanged.
### Details
N/A: none beyond the plan text.

### Companion test files
- `tests/agent/test_orchestrator_bg_failure_threshold.py`
  - Procedure: assert failures group by task type and that log records contain no raw exception reason, only the class name.
  - Validation: `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py -q`.

## Compatibility considerations
- Existing monitor call sites pass tasks by name only and remain valid; the constructor signature is unchanged.

## Security considerations
- Redaction is the security-relevant change: raw failure reasons (which may embed request or DB details) no longer reach logs or audit (AC-2).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_orchestrator_bg_failure_threshold.py -q`.

## Completion criteria
Every registered task carries type and session identity, failure thresholds count per type, and no log or audit line contains raw failure reasons (AC-2).

## Out of Scope
Task-creation capture (seq 09), title log redaction (seq 10-11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion row 27) | Pending | — | — | Tests written first per plan Phase 4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row |

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
- **Requirement ID**: `REQ-005` (typed monitor registration and log redaction)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/bg_task_monitor.py`, `tests/agent/test_orchestrator_bg_failure_threshold.py`

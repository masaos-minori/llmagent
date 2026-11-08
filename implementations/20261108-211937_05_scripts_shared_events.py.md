## Goal
Rename the `RetryEvent` TypedDict field `backoff_sec` to `retry_wait_sec` in `scripts/shared/events.py` — the same misleading name carried in the retry-event DTO (`REQ-003`, row added 2026-11-08).

## Scope
**Release unit**: wfaudit014-full

- Covers Plan `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md` row 5 only: `scripts/shared/events.py`.

## Assumptions
- Census 2026-11-08: `RetryEvent` has no emitter and no consumer in `scripts/` or `tests/` (no `RetryEvent(` construction found); the rename therefore breaks no call site.
- The REQ-003 grep gate covers all of `scripts/`, and `scripts/shared/events.py` L47 is a `backoff_sec` hit — leaving the DTO unrenamed would fail the plan's acceptance grep.

## Design decisions
- Rename the field line `backoff_sec: float` -> `retry_wait_sec: float` (type stays `float`: the DTO models an event payload, not the dataclass `int` policy field).
- `docs/40_shared`'s `RetryEvent` description names no individual fields (verified 2026-11-08), so no documentation edit is triggered by this row.

## Alternatives considered
- Delete `RetryEvent` as dead: rejected — the plan scopes this finding to renaming the misleading name; eventbus payload schemas are out of this unit's freeze.

## Implementation
### Target file
`scripts/shared/events.py`

### Procedure
Rename one TypedDict field.

### Method
In `class RetryEvent(TypedDict):`, the field line `backoff_sec: float` (HEAD L47, between `error_type: str` and `session_id: str`) -> `retry_wait_sec: float`. Field order and all other fields unchanged.

### Details
- `grep -rn backoff_sec scripts/shared/` returns nothing after the edit.

## Compatibility considerations
- Event payloads are constructed as plain dicts elsewhere if at all (none found); no persisted event schema validation names the field.

## Security considerations
- No change to data handling.

## Rollback considerations
- Revert the commit; no state involved.

## Validation plan
- Grep gate: `grep -rn "backoff_sec" scripts/ config/ tests/ docs/` (plan Validation plan) shows no `scripts/shared/events.py` hit after all rows land.
- `uv run pytest tests/agent/workflow/ -q` stays green (no test references the DTO field).

## Completion criteria
- `REQ-003` for this file: `backoff_sec` absent; `RetryEvent` names `retry_wait_sec`.

## Out of Scope
- Adding an emitter or consumer for `RetryEvent`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261107-203227_wfaudit014_retry-loop-dead-parameters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084015_wfaudit014_retry-loop-dead-parameters.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-211937
- **Related target files**: scripts/shared/events.py

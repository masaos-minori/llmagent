## Goal

- Rename the two `_populate_token_maps` references in `tests/eventbus/test_eventbus_dlq_pagination.py` to `build_and_publish_generation` (new) (REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; DLQ pagination behavior unchanged.

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: import at 15 and call at 34 — the file's only 2 removed-name references (grep-verified), matching the Plan row "`_populate_token_maps` calls (2)". No map mutation in this file.

## Design decisions

- Simple import/call rename; no behavior change.

## Alternatives considered

- None material (rename-only row).

## Implementation
### Target file
`tests/eventbus/test_eventbus_dlq_pagination.py`

### Procedure
1. Rename the `from eventbus.auth import _populate_token_maps` (line 15) and `_populate_token_maps(cfg)` (line 34) to `build_and_publish_generation` (new).
2. Confirm `grep -n "_populate_token_maps" tests/eventbus/test_eventbus_dlq_pagination.py` returns nothing.

### Method
- Pagination assertions (page sizes, ordering, total counts) stay unchanged (behavior locking).

### Details
- No other imports touched.

## Compatibility considerations

- File is not in the plan003 overlap set recorded in the Plan Assumptions — plan002-only edits.

## Security considerations

- N/A beyond unchanged behavior.

## Rollback considerations

- Revert of the single atomic commit restores the two names (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq_pagination.py` green after Method.
- `grep -n "_populate_token_maps" tests/eventbus/test_eventbus_dlq_pagination.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- File names neither removed name (AC-001).

## Out of Scope

- DLQ pagination semantics — unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename import (15) and call (34) — Plan Phase 1 | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `tests/eventbus/test_eventbus_dlq_pagination.py`

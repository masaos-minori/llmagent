## Goal

- Rename `_populate_token_maps` references and reword alias comments in `tests/eventbus/test_eventbus_crash_ack.py` (REQ-002); the file already avoids direct map mutation.

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; crash-ack behavior unchanged.

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: `_populate_token_maps` references at 60 (import), 81 (call), 82 and 91 (comments) — 4 total matching the Plan row "4 calls"; alias comments at 83 ("no direct _TOKEN_PRINCIPAL_MAP mutation needed.") and 93 ("No direct _TOKEN_PRINCIPAL_MAP mutation needed.") matching "Alias comments (lines 83, 93)". No actual mutation exists in this file (grep-verified).

## Design decisions

- Comments at 82-83 and 91-93 are reworded together: name the new function, replace the alias mention with generation wording ("the lifespan re-runs `build_and_publish_generation()`, which publishes a fresh baseline generation; no direct principal-map injection is needed").

## Alternatives considered

- Deleting the comments: rejected — they explain why this file needs no injection blocks; only the names are stale.

## Implementation
### Target file
`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure
1. Rename the import (60) and call (81) to `build_and_publish_generation` (new).
2. Reword comments at 82-83 and 91-93 per the Design decisions.
3. Confirm `grep -n "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" tests/eventbus/test_eventbus_crash_ack.py` returns nothing.

### Method
- Crash-ack recovery assertions stay unchanged (behavior locking).

### Details
- No helper imports are needed in this file (it publishes via lifespan only).

## Compatibility considerations

- Overlap with plan003 (recorded compatible in the Plan Assumptions): plan003 edits facade import lines and NACK call sites here; plan002 edits lines 60/81/82-83/91/93 only. Plan002 lands first; re-verify positions at plan003 generation time.

## Security considerations

- N/A beyond unchanged behavior (AC-006 unaffected).

## Rollback considerations

- Revert of the single atomic commit restores names/comments (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_crash_ack.py` green after Method.
- `grep -n "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" tests/eventbus/test_eventbus_crash_ack.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- File names neither removed name (AC-001).

## Out of Scope

- Crash-ack recovery semantics — unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename references (60, 81, 82, 91) and reword alias comments (83, 93) — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | populate renamed; comments reworded to generation wording |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Completed | 20261107-152722 | 20261107-152722 | full suite 11784 passed diff-cover 100pct |

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
- **Related target files**: `tests/eventbus/test_eventbus_crash_ack.py`
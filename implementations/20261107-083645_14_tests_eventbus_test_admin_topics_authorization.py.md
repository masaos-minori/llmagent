## Goal

- Convert `tests/eventbus/test_admin_topics_authorization.py` to the renamed publication function and generation-based reads, replacing the helper `principal_map()` and the map-identity assertion (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; admin rebuild/no-op/409 semantics unchanged.

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: `principal_map` import at 23 (with `post_topics_authorization` on the same line), generation-identity assertion at 269 (`assert principal_map() is state_before.principals`), principal read at 441 (`principal = principal_map()["consumer-tok"]`); `_populate_token_maps` references at 573 (comment), 589 (import), 609 (call), 630 (comment), 658 (import), 678 (call) — 6 total, matching the Plan row (grep-verified).

## Design decisions

- Identity assertion at 269 becomes `assert current_generation().principals is state_before.principals`: the no-op-rebuild test must keep proving the same generation object stays in force (REQ-004 / AC-004); the removed-name half of the old assertion (`principals is auth._TOKEN_PRINCIPAL_MAP`, an alias identity) is not the test's point and disappears with the alias — the generation-snapshot identity half survives unchanged (Plan Design "Test discipline").
- `principal_map()` calls (269, 441) become `current_principals()` (sibling document 04).
- Populate comments (573, 630) name `build_and_publish_generation()` in the same sentences.

## Alternatives considered

- Deleting line 269 outright: rejected — the assertion verifies "no-op body leaves the generation object untouched" (paired with `after is state_before` at 267 and the 409 tests around 271-276); deleting it would weaken AC-004. Only the alias-identity wording is removed.

## Implementation
### Target file
`tests/eventbus/test_admin_topics_authorization.py`

### Procedure
1. Line 23: replace `principal_map` with `current_principals` (new) in the `tests.eventbus.eventbus_helpers` import; update calls at 269 and 441.
2. Rename the `_populate_token_maps` comments (573, 630), imports (589, 658), and calls (609, 678) to `build_and_publish_generation` (new).
3. Confirm `grep -n "principal_map\|_populate_token_maps" tests/eventbus/test_admin_topics_authorization.py` (word-boundary) returns nothing except `_build_principal_map`-style names, of which this file has none.

### Method
- Admin endpoint status codes, 409 stale-generation behavior, and audit-log call-count assertions stay unchanged (behavior locking).

### Details
- No injection blocks exist in this file; the map is built through config publication only, so no `publish_derived_generation` (new) import is needed.

## Compatibility considerations

- File is not in the plan003 overlap set recorded in the Plan Assumptions — plan002-only edits.

## Security considerations

- `consumer-tok` at 441 stays a dict key in an assertion; no raw bearer token added (AC-006).

## Rollback considerations

- Revert of the single atomic commit restores the old helper import/calls (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_admin_topics_authorization.py` green after Method.
- `grep -rn "\bprincipal_map\b" tests/eventbus/test_admin_topics_authorization.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- Neither removed name appears; the no-op rebuild still proves generation-object identity via `current_generation()` (AC-001, AC-004).

## Out of Scope

- Admin route behavior (`admin_route.py` rebuild path) — reference-only, unchanged (Plan Reference Files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert helper import/calls (23, 269, 441) and populate references (573, 589, 609, 630, 658, 678) — Plan Phase 1 | Pending | — | — | |
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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `tests/eventbus/test_admin_topics_authorization.py`

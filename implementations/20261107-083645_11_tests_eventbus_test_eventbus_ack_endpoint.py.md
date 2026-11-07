## Goal

- Convert `tests/eventbus/test_eventbus_ack_endpoint.py` to `build_and_publish_generation()` and generation publication (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; ack-endpoint HTTP behavior unchanged.

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: `_populate_token_maps` references at 22 (import), 34 (call), 49 (import), 70 (call), 80 and 82 (comments naming the lifespan call) — 6 total, matching the Plan row "6 calls"; direct mutation region 83-89 (import 83, conditional override 85-89), matching "Direct map mutation (lines 83-89)".

## Design decisions

- Both import/call pairs (22/34, 49/70) rename to `build_and_publish_generation` (new) — the tests deliberately pre-populate before entering the client because the lifespan re-publishes the baseline (comments 80-82); that sequencing stays, only the name changes.
- The 83-89 conditional override becomes `publish_derived_generation({"consumer-token": Principal(...)})` from `current_principals()` values (sibling document 04); teardown handled by the conftest fixture (sibling document 05).

## Alternatives considered

- Moving the injection before client creation via config file: rejected — the tests specifically cover the lifespan-repopulation race; injection must happen after lifespan publication.

## Implementation
### Target file
`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure
1. Rename the imports (22, 49) and calls (34, 70) to `build_and_publish_generation` (new); update the comments at 80-82 to name the new function (they describe the lifespan re-population behavior — keep the explanation, change the name).
2. Replace the 83-89 mutation with `publish_derived_generation(...)` (roles and grants copied from `current_principals()["consumer-token"]`); delete the 83 `_TOKEN_PRINCIPAL_MAP` import.
3. Confirm `grep -n "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" tests/eventbus/test_eventbus_ack_endpoint.py` returns nothing.

### Method
- Ack endpoint status codes, delivery state, and duplicate-ack behavior assertions stay unchanged (behavior locking).

### Details
- `Principal` import stays from `eventbus.auth`; only the map name disappears.

## Compatibility considerations

- Overlap with plan003 (recorded compatible in the Plan Assumptions): plan003 edits facade import lines and NACK call sites here; plan002 edits auth regions 22/34/49/70/80-89 only. Plan002 lands first; re-verify positions at plan003 generation time.

## Security considerations

- Token-fingerprint copy at 89 (`token_fingerprint=_TOKEN_PRINCIPAL_MAP[...]`) becomes a `current_principals()` read — no raw token enters the new code (AC-006).

## Rollback considerations

- Revert of the single atomic commit restores the mutation region (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py` green after Method.
- `grep -n "_TOKEN_PRINCIPAL_MAP\|_populate_token_maps" tests/eventbus/test_eventbus_ack_endpoint.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- No removed-name reference remains; injection via publication only (AC-001, AC-003).

## Out of Scope

- Ack endpoint semantics — unchanged (behavior locking).
- Helper and fixture mechanism — sibling documents 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename populate references (22/34, 49/70, 80-82) and convert mutation (83-89) — Plan Phase 1 | Pending | — | — | |
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
- **Related target files**: `tests/eventbus/test_eventbus_ack_endpoint.py`

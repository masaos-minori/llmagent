## Goal

- Replace the four snapshot/mutate/restore blocks in `tests/eventbus/test_eventbus_consumer_authorization.py` with generation-based construction and publication, so this file no longer touches a global principal dictionary (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; restoration is delegated to the conftest generation fixture (sibling document 05).

## Assumptions

- Blocks verified 2026-11-07 at HEAD `1a13653e8`: `test_mapping_loaded_via_config_reaches_consumer_principal` (snapshot 290, populate 307, read 308, restore 311-312), `test_empty_mapping_via_config_denies_all` (320/336/337/340-341), `test_consumer_authorization_with_empty_topic_list_grants_nothing` (347/359/360/364-365), `test_missing_mapping_via_config_raises` (snapshot 373, populate 390, restore 394-395) — four `dict(eb_auth._TOKEN_PRINCIPAL_MAP)` snapshots and four `eb_auth._populate_token_maps(cfg)` calls total, plus docstring mentions at 286, 316, 369, matching the Plan row "Four snapshot/mutate/restore blocks via `eb_auth._TOKEN_PRINCIPAL_MAP` (lines 290-395)".

## Design decisions

- Config-driven blocks build the config object, call `build_and_publish_generation(cfg)` (sibling documents 01/02 rename the function) instead of mutating the live map, then read the effective principal via `current_principals()` (sibling document 04).
- The final `clear()/update(snapshot)` restores in all four blocks are deleted; the autouse conftest fixture republishes the test-start generation (sibling document 05).
- The raises-case block (367-395) asserts `current_generation()` is unchanged after the failed `build_and_publish_generation(cfg_missing)` — the same publish-only guarantee (AC-004) tested by the TTL file.

## Alternatives considered

- Keeping the block shape but copying the map into a local variable: rejected — the tests' purpose is the config->principal plumbing through the publication path; a local copy bypasses it and AC-003 forbids global-map contact.

## Implementation
### Target file
`tests/eventbus/test_eventbus_consumer_authorization.py`

### Procedure
1. Remove every `eb_auth._TOKEN_PRINCIPAL_MAP` reference (lines 290, 308, 311-312, 320, 337, 340-341, 347, 360, 364-365, 373, 394-395): snapshot lines become `before = eb_auth.current_generation()`, mutated-principal reads become `current_principals()["consumer-token"]`, restore `finally` blocks are dropped where the only cleanup was the restore (keep `finally` blocks that close clients).
2. Where a block injected a modified `consumer-token` Principal into the live map, call `publish_derived_generation({"consumer-token": Principal(...)})` (sibling document 04) instead.
3. Keep all HTTP expectations (401/403/200) and delivery-state assertions unchanged; only the state-construction mechanism changes (behavior locking).

### Method
- Duplicate-token and cross-pair guards in this file (tests at 246-282) do not touch the map and stay unchanged (grep-verified: `eb_auth._TOKEN_PRINCIPAL_MAP` appears only inside the four blocks 290-395).

### Details
- Import adjustment: drop `_TOKEN_PRINCIPAL_MAP` access via `eb_auth`, add `current_principals` (new) (and `publish_derived_generation` (new) where injection is needed) from `tests.eventbus.eventbus_helpers`.

## Compatibility considerations

- Overlap with plan003 on other files only; this file is not a plan003 target (Plan Assumptions list 003 overlaps for app.py, ack tests, checker).

## Security considerations

- Consumer ID and topic authorization stay enforced end-to-end via HTTP status assertions (AC-005); no token values are added to assertion messages (AC-006).

## Rollback considerations

- Revert of the single atomic commit restores the four blocks (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_consumer_authorization.py` green after Method.
- `grep -n "_TOKEN_PRINCIPAL_MAP" tests/eventbus/test_eventbus_consumer_authorization.py` -> no matches (AC-001, AC-003).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- No `_TOKEN_PRINCIPAL_MAP` reference remains in the file; all four blocks construct state via publication (AC-003).
- Authorization enforcement assertions pass unchanged (AC-005).

## Out of Scope

- The helper and fixture mechanism — sibling documents 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert the four snapshot/mutate/restore blocks (290-395) — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | snapshot/finally blocks removed (conftest generation restore); populate renamed; principal reads via current_principals(); mypy-clean import added |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063003_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-083645
- **Related target files**: `tests/eventbus/test_eventbus_consumer_authorization.py`
## Goal

- Convert the auth-state construction in `tests/eventbus/test_eventbus_ack_nack.py` to `build_and_publish_generation()` and generation publication (REQ-002, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; NACK semantics and delivery-state assertions unchanged (NACK/optional-consumer-id work belongs to plan003).

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: `_populate_token_maps` import 144 and call 165, lifespan comment at 182; mutation region 167-187: import 167, conditional override 169-173, later `base = _TOKEN_PRINCIPAL_MAP.get("consumer-token")` (185) and re-set 187 — matching the Plan row "Direct map mutation (lines 167-187) and `_populate_token_maps` calls (3)" (3 = import 144 + call 165 + call-adjacent references; file total 3 populate references plus comment at 182).

## Design decisions

- The conditional override (169-173) and the later get/re-set (185-187) become `publish_derived_generation({"consumer-token": Principal(...)})` calls (sibling document 04) — each publishes one complete generation; the conftest fixture republishes the test-start generation on teardown (sibling document 05).
- Lifespan comment at 182 renames the function mention only.

## Alternatives considered

- Reusing the mutation code with a copied dict: rejected — copying still mutates a live object mid-test and fails AC-003.

## Implementation
### Target file
`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure
1. Rename the `from eventbus.auth import _populate_token_maps` (144) and `_populate_token_maps(cfg)` (165) to `build_and_publish_generation` (new); update the 182 comment wording accordingly.
2. Replace the 167-173 conditional override with `publish_derived_generation({"consumer-token": Principal(roles=..., consumer_grants=..., token_fingerprint=...)})` built from `current_principals()` values; delete the 167 import of `_TOKEN_PRINCIPAL_MAP`.
3. Replace the 185-187 get/re-set pair with a second `publish_derived_generation(...)` call carrying the adjusted grants.
4. Confirm `grep -n "_TOKEN_PRINCIPAL_MAP" tests/eventbus/test_eventbus_ack_nack.py` returns nothing.

### Method
- Ack/NACK HTTP and broker-state assertions stay byte-identical (behavior locking); only principal construction changes.

### Details
- No import-layer change: the file keeps importing from `eventbus.auth` directly and from `tests.eventbus.eventbus_helpers`.

## Compatibility considerations

- Overlap with plan003 (recorded compatible in the Plan Assumptions): plan003 edits facade import lines and NACK call sites in this file; plan002 edits only the auth construction regions above. Plan002 lands first (memo order); re-verify positions when plan003 procedures are generated.

## Security considerations

- Consumer authorization for ack/nack paths stays enforced via unchanged 401/403 assertions (AC-005); no raw token in new text (AC-006).

## Rollback considerations

- Revert of the single atomic commit restores the mutation regions (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py` green after Method.
- `grep -n "_TOKEN_PRINCIPAL_MAP" tests/eventbus/test_eventbus_ack_nack.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- No `_TOKEN_PRINCIPAL_MAP` reference remains; construction via publication only (AC-001, AC-003).

## Out of Scope

- NACK behavior and optional consumer-id changes — plan003.
- Helper and fixture mechanism — sibling documents 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert populate calls (144, 165, 182) and mutation regions (167-187) — Plan Phase 1 | Pending | — | — | |
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
- **Related target files**: `tests/eventbus/test_eventbus_ack_nack.py`

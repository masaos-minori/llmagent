## Goal

- Replace direct `_TOKEN_PRINCIPAL_MAP` mutation in `tests/eventbus/test_eventbus_subscribe.py` with generation publication (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- Single atomic Phase 1 cutover file; HTTP authorization expectations unchanged.

## Assumptions

- Verified 2026-11-07 at HEAD `1a13653e8`: conditional override block at 131-137 (`from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal` at 131, `if "consumer-token" in ...` at 133, Principal rebuild with replaced `consumer_grants` at 134-137); second block at 207-218 (import at 207, set at 209-213, client 403 call at 212 region, `finally: _TOKEN_PRINCIPAL_MAP.pop("consumer-token", None)` at 218); alias comments at 596-597 ("Subscribe uses topic-based authorization (`_TOKEN_PRINCIPAL_MAP`)..." — verified via grep).

## Design decisions

- Injection becomes `publish_derived_generation({"consumer-token": Principal(...)})` (sibling document 04) after the client/lifespan baseline is live: the derived generation carries every current principal plus the override, published as one complete snapshot.
- The `finally: ...pop(...)` cleanup is deleted; the conftest fixture republishes the test-start generation on teardown (sibling document 05). The `try/finally` stays where it closes the client.
- Alias comments at 596-597 are reworded to generation wording ("topic-based authorization from the published generation's principals").

## Alternatives considered

- Monkeypatching `current_generation()`: rejected — publication is the production path the tests must exercise (AC-002); monkeypatching would bypass the very boundary AC-003 protects.

## Implementation
### Target file
`tests/eventbus/test_eventbus_subscribe.py`

### Procedure
1. Block 131-137: replace the read-modify-write on `_TOKEN_PRINCIPAL_MAP` with `publish_derived_generation({"consumer-token": Principal(roles=current_principals()["consumer-token"].roles, consumer_grants=frozenset({("consumer-A", "t")}), token_fingerprint=current_principals()["consumer-token"].token_fingerprint)})` (sibling document 04); drop the `from eventbus.auth import _TOKEN_PRINCIPAL_MAP ...` import.
2. Block 207-218: same replacement (grants `frozenset({("c1", "allowed-topic")})`, `token_fingerprint="test-fingerprint"`); delete the `finally`-pop of the map (keep client teardown).
3. Reword comments at 596-597 to remove the alias name.
4. Confirm `grep -n "_TOKEN_PRINCIPAL_MAP" tests/eventbus/test_eventbus_subscribe.py` returns nothing.

### Method
- The 403 expectations (disallowed topic at 212-214 region) stay identical — only construction changes (behavior locking).
- The "no consumer-token published yet" guard in block 1 (the `if "consumer-token" in ...` at 133) becomes unnecessary: `publish_derived_generation` (new) requires a published baseline (lifespan guarantees it) and raises otherwise (document 04 Method).

### Details
- `Principal`/`Role` imports move from the mutation blocks to the module import list as needed (no removed names involved).

## Compatibility considerations

- Overlap with plan003: plan003 edits facade import lines and NACK call sites in the ack test files; `test_eventbus_subscribe.py` is not listed in the 003 overlap set recorded in the Plan Assumptions — this file's edits are plan002-only.

## Security considerations

- Consumer identity and topic authorization stay enforced via unchanged HTTP status assertions (AC-005); no raw tokens in new assertion text (AC-006).

## Rollback considerations

- Revert of the single atomic commit restores both mutation blocks (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_subscribe.py` green after Method.
- `grep -n "_TOKEN_PRINCIPAL_MAP" tests/eventbus/test_eventbus_subscribe.py` -> no matches (AC-001, AC-003).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- No `_TOKEN_PRINCIPAL_MAP` reference or direct dict mutation remains (AC-001, AC-003).
- Subscribe authorization matrix (allowed/denied topic, consumer identity) unchanged (AC-005).

## Out of Scope

- Helper and fixture mechanism — sibling documents 04, 05.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Convert mutation blocks (131-137, 207-218) and alias comments (596-597) — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | fixture vestigial mutation removed (cfg grants identical); in-test mutation via publish_derived_generation, finally removed; comments reworded |
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
- **Related target files**: `tests/eventbus/test_eventbus_subscribe.py`
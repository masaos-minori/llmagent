## Goal
Update `tests/eventbus/test_eventbus_crash_ack.py`'s `principal_client` fixture to use `_TOKEN_PRINCIPAL_MAP` + `Principal` instead of the removed `_TOKEN_CONSUMER_MAP`.

## Scope
- **In-Scope**: Update `principal_client` fixture in `tests/eventbus/test_eventbus_crash_ack.py` to use `_TOKEN_PRINCIPAL_MAP` + `Principal` instead of `_TOKEN_CONSUMER_MAP`.
- **Out-of-Scope**: Do not modify `scripts/eventbus/auth.py`'s Principal/token-map implementation — the removal in `c85362a36` is treated as intentional. Do not investigate or fix the 14 unrelated failures in `tests/eventbus/test_eventbus_auth.py` (filed separately). Do not investigate or fix `test_partial_ack_replay` or the concurrent/DLQ test failures (fileed separately).

## Assumptions
- Replacing `_TOKEN_CONSUMER_MAP["consumer-token"] = {"consumer-A"}` with `_TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(...)` will restore the fixture's intended behavior (consumer-token principal owns only consumer-A).
- The existing `_populate_token_maps(cfg)` call in the fixture already populates `_TOKEN_PRINCIPAL_MAP` correctly; we just need to modify the resulting entry afterward.

## Design decisions
- After calling `_populate_token_maps(cfg)`, replace `_TOKEN_CONSUMER_MAP` mutation with:
```python
from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal
# ... after _populate_token_maps(cfg):
if "consumer-token" in _TOKEN_PRINCIPAL_MAP:
    _TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(
        roles=_TOKEN_PRINCIPAL_MAP["consumer-token"].roles,
        allowed_consumer_ids=frozenset({"consumer-A"}),
        allowed_topics=_TOKEN_PRINCIPAL_MAP["consumer-token"].allowed_topics,
        token_fingerprint=_TOKEN_PRINCIPAL_MAP["consumer-token"].token_fingerprint,
    )
```
This preserves all fields except `allowed_consumer_ids`, which is restricted to `{"consumer-A"}`.

## Alternatives considered
- Using a separate `_FALLBACK_DEFAULTS` dict for the "no config available" case vs. the "config loaded but incomplete" case — rejected because the Plan suggests this as a possible future enhancement, not an immediate fix.
- Adding try/except around the fallback path in `resolve_rag_config` itself — rejected because it doesn't address the root cause (self-contradiction between defaults and validation).

## Implementation
### Target file
`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure
Replace `_TOKEN_CONSUMER_MAP` import/mutation with `_TOKEN_PRINCIPAL_MAP` + `Principal` recreation.

### Method
Mechanical edit: modify the `principal_client` fixture.

### Details
1. Line 80: Change `from eventbus.auth import _TOKEN_CONSUMER_MAP` to `from eventbus.auth import _TOKEN_PRINCIPAL_MAP, Principal`
2. Line 82: Replace `_TOKEN_CONSUMER_MAP["consumer-token"] = {"consumer-A"}` with:
```python
if "consumer-token" in _TOKEN_PRINCIPAL_MAP:
    _TOKEN_PRINCIPAL_MAP["consumer-token"] = Principal(
        roles=_TOKEN_PRINCIPAL_MAP["consumer-token"].roles,
        allowed_consumer_ids=frozenset({"consumer-A"}),
        allowed_topics=_TOKEN_PRINCIPAL_MAP["consumer-token"].allowed_topics,
        token_fingerprint=_TOKEN_PRINCIPAL_MAP["consumer-token"].token_fingerprint,
    )
```

## Compatibility considerations
Modifying `_TOKEN_PRINCIPAL_MAP` after `_populate_token_maps` may have unintended side effects if the Principal object is shared across multiple lookups. Create a new `Principal` instance rather than mutating the existing one (as shown in the design section above).

## Security considerations
N/A: test-only change.

## Rollback considerations
If the fix causes unexpected side effects, revert the changes and instead choose the alternative direction (update the test to expect `ValueError` if the defaults direction was chosen, or revert the defaults change if the raise-based direction was chosen).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/eventbus/test_eventbus_crash_ack.py | Unit test execution | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck -v` | No ERROR outcomes |
| tests/eventbus/ | Integration regression | `uv run pytest tests/eventbus/ -q` | No new failures in eventbus test suite |

## Completion criteria
- [ ] REQ-EB-001-002: `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck -v` — no `ERROR` outcomes
- [ ] REQ-EB-001-005: Each previously-`ERROR`ing test now either passes, or fails with a test-body assertion failure that is filed as its own follow-up (not another `ImportError`)

## Out of scope
- Changing `RagConfigValidator`'s general validation rules beyond the specific `use_search`/`llm_url`/`embed_url` interaction
- Investigating or fixing any other file's test failures

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-EB-001-002; Verify correct approach (read auth.py) | Pending | — | — | |
| 2 | REQ-EB-001-002; Update crash_ack fixture | Pending | — | — | |
| 3 | REQ-EB-001-002; Run targeted test (crash_ack) | Pending | — | — | |
| 4 | REQ-EB-001-005; Run regression test | Pending | — | — | |

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
- **Requirement ID**: REQ-EB-001-002
- **Source issue**: issues/20260917-110241_eb01_eventbus-tests-reference-removed-_token_consumer_map-symbol.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260917-224815_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260918-002224
- **Related target files**: tests/eventbus/test_eventbus_crash_ack.py

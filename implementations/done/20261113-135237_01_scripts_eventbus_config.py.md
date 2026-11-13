## Goal

Make `EventBusConfig.__post_init__` the single validation point for the required `auth_token` and the loopback bind, and remove `topic_authorization` from the configuration layer so a config carrying it fails load with the existing unknown-key error.

## Scope
**Release unit**: single-authorization-format (shared with rows 02, 04, 05, 06, 07, 14, 17; the REQ-001 part of this document runs first as Plan Phase 1, before the unit lands)

## Assumptions
- `__post_init__` is the right single place: every construction path (load, `dataclasses.replace` in the admin route and TTL sweep) passes through it (Plan Assumptions).
- The load-time message for an empty referenced environment value becomes the `__post_init__` message; the existing test only changes its expected text.
- `_is_public_host` stays because `app.py`'s startup bind guard uses it.

## Design decisions
- Validation lives only in the dataclass; the load path keeps the unknown-key rejection (`config.py:346-351`) as the sole guard against removed formats, with no new parsing.

## Alternatives considered
- Keeping `_validate_cross_field` with the checks delegated to `__post_init__`: rejected; the Plan deletes the three functions outright (REQ-001).

## Implementation
### Target file
`scripts/eventbus/config.py`
### Procedure
Delete the three cross-check functions and the load-time empty check, reword the bind error, then remove the `topic_authorization` field and every handling of it.
### Method
Text deletion and one message reword within the module; no new function or import.
### Details
- Delete `_validate_cross_field` (lines 40-43), `_validate_token_combinations` (46-59; the procedure's original 46-61 range was re-verified 2026-11-13 — the function ends at 59), `_validate_deployment_mode` (62-70; original 63-71 — it starts at 62), and the `_validate_cross_field(cfg)` call in `load_config` (424). Keep `_is_public_host` (35).
- Delete the `load_config` empty check at 378-379 (`"eventbus config 'auth_token' must not be empty."`). Verified: no test asserts the deleted `_validate_token_combinations` message "At least one authentication token must be configured"; `test_load_config_requires_at_least_one_token` (test_eventbus_config.py:477) matches `auth_token` and stays green on the `__post_init__` message.
- Delete the `topic_authorization` plumbing in `authorization_baseline_hash` (verified 2026-11-13; required for AC-2 and because the field deletion makes the loop an AttributeError): the docstring phrase at line 77 ("consumer_authorization and topic_authorization") and the pair-expansion loop at 84-85. Keep the function itself and the consumer part (82-83).
- Reword the bind error in `__post_init__` (145-148): keep the prefix `Event Bus bound to non-loopback address {host}` and state that only loopback addresses are allowed; drop the misleading `set auth_token` advice (REQ-001).
- Keep the `auth_token is required but not configured` check in `__post_init__` (150) as the single required-token message (REQ-001).
- Remove `topic_authorization`: the dataclass field (121), its shape validation block in `__post_init__` (222-237), the entry in the allowed-key list (266), the load-time set conversion code (386-390), and the constructor argument (409). Rewrite the normalization comment at 381-384 so it names only `consumer_authorization` (the comment text at 382 currently names `topic_authorization` and would fail the AC-2 search; keep the `(REQ-002)` label in it — config.py labels are outside this row's scope and stay for the rmcompat007 Plan). Keep `consumer_authorization = data.get(...)` at 385 and the constructor use at 408. After this, a config carrying the key fails load with the unknown-key error (REQ-002).
- Keep `consumer_authorization` and its list-only shape validation (205-219) unchanged.

### Companion test files
- `tests/eventbus/test_eventbus_config.py`
  - Procedure (claims re-verified 2026-11-13): move the expectation at line 619 (`match="must not be empty"`, inside `test_load_config_shared_token_env_reference_empty_hits_non_empty_check` at 604) to the `__post_init__` message `auth_token is required but not configured`; delete the `topic_authorization` fixture lines and assertions in `test_load_config_surfaces_authorization_mappings` (fixture 698, assertion 702) and `test_load_config_normalizes_mapping_types` (fixture 717, assertions 720-722) — rewrite both tests for `consumer_authorization` only (the tests at 686 and 705 must not be deleted whole, only their topic-side parts); add one test per remaining message (empty token, bind); keep the existing bind tests (181-195, `match="non-loopback"`) and keep the startup test's `Event Bus bound to non-loopback address` match in `test_eventbus_startup.py` — the reworded message keeps that prefix; add a load test asserting a TOML with `topic_authorization` fails with the unknown-key error (`test_load_config_rejects_unknown_key` at 207 shows the pattern).
  - Validation: `uv run pytest tests/eventbus/test_eventbus_config.py tests/eventbus/test_eventbus_startup.py`

## Compatibility considerations
- `dataclasses.replace` callers (admin route, TTL sweep) stop passing `topic_authorization` in rows 04 and 05; the whole unit lands together (Plan Release units).
- The deployed `config/eventbus.toml` must carry no active `topic_authorization` key before deploy (UNK-03).

## Security considerations
- Fail-closed: removing the key from the allowed list makes a config that still carries it refuse to start rather than be silently accepted.

## Rollback considerations
- Pure deletion plus one message reword; revert the file to restore the previous behavior. Audit log queries are unaffected.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_config.py tests/eventbus/test_eventbus_startup.py`
- AC-1/AC-2 acceptance searches from the Plan (`rg` for the deleted functions and `topic_authorization` in this file).
- `uv run ruff check` and `mypy --no-namespace-packages scripts/eventbus/config.py`; no new finding.

## Completion criteria
- No `topic_authorization` remains in the file; the three deleted functions and the load empty check are gone; each remaining failure message has a test (AC-1, AC-2, AC-8).

## Out of Scope
- The client missing `expected_generation` (UNK-06) and any client contract change.
- `REQ-` label comments outside this file (left for the rmcompat007 Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-13 | 2026-11-13 | REQ-001 part (Phase 1) + REQ-002 part both landed; targeted tests green |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-13 | 2026-11-13 | both REQ parts landed; targeted tests green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-13 | 2026-11-13 | unit-2 targeted+full suites green; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-13 | 2026-11-13 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| WI-01 | 3 | docs-fix | Resolved | agent | 2026-11-13 | adr_02_04_006 lines 84/349 reworded to `EventBusConfig.__post_init__`; `tools/check_compat_shims.py` green |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/eventbus/config.py`, `tests/eventbus/test_eventbus_config.py`

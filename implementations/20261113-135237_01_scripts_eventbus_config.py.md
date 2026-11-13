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
- Delete `_validate_cross_field` (lines 40-43), `_validate_token_combinations` (46-61), `_validate_deployment_mode` (63-71), and the `_validate_cross_field(cfg)` call in `load_config` (424). Keep `_is_public_host` (35).
- Delete the `load_config` empty check at 378-379 (`"eventbus config 'auth_token' must not be empty."`).
- Reword the bind error in `__post_init__` (145-148): keep the prefix `Event Bus bound to non-loopback address {host}` and state that only loopback addresses are allowed; drop the misleading `set auth_token` advice (REQ-001).
- Keep the `auth_token is required but not configured` check in `__post_init__` (150) as the single required-token message (REQ-001).
- Remove `topic_authorization`: the dataclass field (121), its shape validation block in `__post_init__` (222-237), the entry in the allowed-key list (266), the load-time set conversion (382-390), and the constructor argument (409). After this, a config carrying the key fails load with the unknown-key error (REQ-002).
- Keep `consumer_authorization` and its list-only shape validation (205-219) unchanged.

### Companion test files
- `tests/eventbus/test_eventbus_config.py`
  - Procedure: move the `test_eventbus_config.py` line 619 expectation from the load message to the `__post_init__` message; delete the `topic_authorization` load tests (698-722); add one test per remaining message (empty token, bind) keeping the `non-loopback` match used by `test_eventbus_startup.py`; add a load test asserting a TOML with `topic_authorization` fails with the unknown-key error.
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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20261110-170832_rmcompat004_eventbus-config-auth-audit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120726_rmcompat004_eventbus-config-auth-audit.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-135237
- **Related target files**: `scripts/eventbus/config.py`, `tests/eventbus/test_eventbus_config.py`

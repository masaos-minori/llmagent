# Implementation Procedure: `tests/eventbus/eventbus_helpers.py` (EBAUTHGEN001 Phase 1)

**Plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` (REQ-001, REQ-005)

## Goal
Add the shared test fixtures the generation/TTL tests need: an injectable clock, a
generation-state reset fixture, and a generation-aware admin-request helper; adapt the
existing principal accessor to the generation object.

## Scope
- `eventbus_test_tokens` `:78-94`, `eventbus_auth_headers` `:97-107`,
  `eventbus_test_config` `:110-137`, `make_eventbus_client` `:140-178`,
  `eventbus_two_lifecycle_clients` `:181-213`, `principal_map` `:216-225`
  (reads `auth._TOKEN_PRINCIPAL_MAP` `:225`).

## Assumptions
- Plan-level assumptions apply unchanged; see the Source plan Assumptions section.

## Design decisions
- `injectable_clock()` (new): returns `(clock, advance)` — `clock()` reports a
  controllable unix epoch; `advance(seconds)` moves it; used by doc 09 expiry tests and
  passed as the sweep's `clock` argument (doc 04).
- `reset_generation_state` (new): pytest fixture (function-scoped) snapshotting
  `eventbus.auth.current_generation()` before the test and re-publishing it after, via
  `publish_generation`. This is the mitigation for doc 01's Needs-Confirmation note —
  `tests/eventbus/conftest.py` must NOT be edited (Reference Files only).
- `post_topics_authorization(client, body, *, expected_generation=None, ttl_seconds=None)`
  (new): generation-aware request helper that defaults `expected_generation` to
  `current_generation().generation` and posts to the admin topics-authorization endpoint
  (path /admin/topics/authorization, unbacktick'd to avoid stale-detector path false
  positives).
- `principal_map()` `:216-225`: keep the function name and return type; internally switch
  to `auth.current_generation().principals` (doc 01 removes the bare map). Existing
  callers in `test_admin_topics_authorization.py` (`:176`, `:204`, `:215`) stay green.

## Alternatives considered
- No file-level alternatives beyond those evaluated in the Source plan; this procedure executes the selected option.

## Implementation
1. Append the three new helpers after `principal_map` (`:225`).
2. Rewrite only the body of `principal_map` (`:216-225`).
3. Register `reset_generation_state` so doc 09 discovers it (import it in the new test
   file as a fixture; do not move fixture registration into conftest.py).

## Compatibility considerations
**Dependencies**:
- Upstream: doc 01 (generation accessor names)
**Blocks**: docs 08, 09 (both consume the new helpers)

## Security considerations
- Existing authentication/authorization boundaries are unchanged except where this procedure states otherwise; secret values must never appear in logs, audit records, or error messages (plan Risk).

## Rollback considerations
- Revert or remove the added test rows; no production change to unwind.

## Validation plan
- No standalone gate; exercised by docs 08/09. Existing helper consumers
  (`make_eventbus_client` users across `tests/eventbus/`) must stay green.

## Completion criteria
- Deterministic expiry tests are possible without wall-clock sleeps; no test relies on
  `auth._TOKEN_PRINCIPAL_MAP` directly after this row lands.

## Out of Scope
- Everything outside the target file and the anchors recorded above; cross-plan boundaries and sequencing are recorded in the Source plan.

## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-verify cited anchors before editing | Pending | — | — | |
| 2 | Apply the Implementation procedure | Pending | — | — | |
| 3 | Run the Validation plan gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `20261030-141000_01_scripts_eventbus_auth.py.md` | 1 (dependency) | Procedure | Pending | — | — |

## Marker record
- `(new)` markers applied: `injectable_clock`, `reset_generation_state`,
  `post_topics_authorization` (Contract section).

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: `issues/20261029-104509_ebauthgen001_eventbus-authz-generation-ttl.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261030-013620_ebauthgen001_eventbus-authz-generation-ttl.md` — Implementation Target Files row 11
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-141000
- **Related target files**: `tests/eventbus/eventbus_helpers.py`

## Goal

Extend `tests/eventbus/test_admin_topics_authorization.py` to cover the admin-layer
acceptance criteria: one-generation publish (no empty-map window), the `persistent` status
field, empty/no-op handling, and audit emission; and build principals through the production
path (`_populate_token_maps()` / `load_config()`) instead of mutating globals directly.

## Scope

- Modify only `tests/eventbus/test_admin_topics_authorization.py`.

## Assumptions

- The admin handler (seq 01) returns `{"status": "ok", "persistent": <bool>,
  "changed": <bool>}` and emits `log_privileged_action` only on effective change.
- Principals are constructed via `_populate_token_maps(config)` (seq 02) or `load_config()`.

## Design decisions

- Add focused tests per acceptance criterion rather than rewriting the existing suite:
  one-generation publish, persistence field, empty/no-op, audit emission, production-path
  principals.

## Alternatives considered

- Rewriting the whole file: unnecessary; additive tests preserve existing coverage.

## Implementation

### Target file

`tests/eventbus/test_admin_topics_authorization.py`

### Procedure

1. Add a test that an effective update returns `persistent` (bool) and `changed: true`, and
   that a subsequent concurrent ACK/NACK never observes a mixed/empty map (one generation;
   REQ-001).
2. Add a test for the persistence contract: the response states `persistent: true/false`
   and restart restores the documented state (REQ-002; UNK-01).
3. Add a test that an empty body `{}` (and a body equal to current value) returns
   `changed: false` WITHOUT repopulating the map or emitting an audit record (REQ-004).
4. Add a test that an effective change emits exactly one redacted `log_privileged_action`
   and a no-op emits none (REQ-003, REQ-008).
5. Refactor any principal setup to build via `_populate_token_maps()` / `load_config()`
   instead of assigning `_TOKEN_PRINCIPAL_MAP` directly (REQ-006).

### Method

Add test functions; convert existing direct-map setup to the production path.

### Details

- Keep assertions referencing the response fields added in seq 01; do not assert on the old
  bare `{"status": "ok"}` shape.

## Compatibility considerations

- The new response fields are asserted; existing assertions reading `status` remain valid.

## Security considerations

- Audit-emission test confirms no token value leaks (INV-05, REQ-008).

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_admin_topics_authorization.py` — all new assertions pass.
- `uv run pytest tests/eventbus/` — full suite passes.

## Completion criteria

- One-generation publish, persistence field, empty/no-op rejection, and audit emission are
  each asserted; principals are built via the production path.

## Out of Scope

- Other test files (seq 07-10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row IS the test update |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation if in scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261023-154326_eventbus006_runtime-authorization-update-consistency.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-122243_eventbus006_runtime-authorization-update-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-090956
- **Related target files**: `tests/eventbus/test_admin_topics_authorization.py`

## Goal

Delete the two synthetic all-roles tests `test_admin_token_grants_all_roles` and
`test_shared_token_grants_all_roles_for_backward_compat` from
`tests/eventbus/test_eventbus_auth.py` so the suite no longer encodes a token-role
model that `scripts/eventbus/auth.py`, ADR-013 and the config docs all contradict
(REQ-001).

## Scope

- In-scope: delete exactly the two test methods above from
  `tests/eventbus/test_eventbus_auth.py`.
- Out-of-scope: any change to `scripts/eventbus/auth.py`, ADR-013, config docs, or
  other tests. The surviving map-shape pin
  (`test_distinct_tokens_get_exactly_their_documented_role`) and the route-level 403
  tests (`test_shared_and_admin_tokens_have_no_consumer_bypass`,
  `test_control_plane_token_cannot_use_consumer_routes`) remain untouched.

## Assumptions

- The two tests are pure tautologies over the injection mechanism; deleting them loses
  no coverage because the documented role shape is pinned by
  `test_distinct_tokens_get_exactly_their_documented_role` (line 1618) and the route
  403 tests verify in this cycle.
- No CI job or test-selection list references the two test names by name
  (`grep` over `.github`/`pyproject.toml`/`tox.ini` found none).

## Design decisions

- Deletion-only. No replacement test is introduced: the shape is already pinned
  elsewhere, and keeping a hand-injected `frozenset(Role)` all-roles test would
  re-introduce the contradiction this Plan removes.

## Alternatives considered

- N/A: replacing the tests would require asserting a principal shape the production map
  can never produce, which is exactly the model the docs forbid.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py` (exists; not a new file).

### Procedure

1. Delete the two test methods `test_admin_token_grants_all_roles` and
   `test_shared_token_grants_all_roles_for_backward_compat` (including their
   `@pytest.mark.asyncio` decorators) from `tests/eventbus/test_eventbus_auth.py`.
2. Run `uv run ruff format` on the file to restore canonical spacing.
3. Run the suite and confirm the expected collection delta.

### Method

Delete the contiguous block spanning both methods. At the current frozen inventory the
block is lines 873-928:

- Line 873: `    @pytest.mark.asyncio` (decorator of `test_admin_token_grants_all_roles`)
- Lines 874-899: body of `test_admin_token_grants_all_roles`
- Line 900: blank
- Line 901: `    @pytest.mark.asyncio` (decorator of
  `test_shared_token_grants_all_roles_for_backward_compat`)
- Lines 902-928: body of `test_shared_token_grants_all_roles_for_backward_compat`

Delete lines 873-928 inclusive (verify against the live file before deleting; line
numbers may have shifted if the file changed since the Plan froze). Both methods are
adjacent, so a single contiguous removal replaces both. If the surrounding blank lines
are left non-canonical, `ruff format` normalizes them.

### Details

Each deleted method injects `Principal(roles=frozenset(Role), consumer_grants=frozenset(), token_fingerprint="test-fingerprint")`
directly into `_TOKEN_PRINCIPAL_MAP` and asserts the injected roles round-trip. Neither
reflects `_populate_token_maps`, which grants the shared `auth_token` and `admin_token`
only `_CONTROL_PLANE_ROLES = {OPERATOR, MONITORING, ADMIN}` (no Publisher, no Consumer)
per `scripts/eventbus/auth.py`; ADR-013 (Decision Details #1, INV-07) states the same.
The next method in the file, `test_per_role_token_has_no_consumer_restriction`
(`frozenset({Role.CONSUMER})`, a single role), is deliberately kept.

## Compatibility considerations

- N/A: test-file change only; no runtime path, public contract, or persisted state is
  affected.

## Security considerations

- N/A: no authentication or authorization logic is touched. The fail-closed consumer
  authorization regression class (`TestFailClosedConsumerAuthorization`) is preserved.

## Rollback considerations

- N/A: revert the implementing commit (single logical deletion).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_auth.py` | Suite run, collection-count comparison | `uv run pytest tests/eventbus/test_eventbus_auth.py` | 409 passed, 1 skipped (baseline 411 passed, 1 skipped, minus the 2 removed) |
| `tests/eventbus/test_eventbus_auth.py` | Full EventBus suite | `uv run pytest tests/eventbus` | 409 passed, 1 skipped |
| `tests/eventbus/test_eventbus_auth.py` | Lint | `uv run ruff check tests/eventbus/test_eventbus_auth.py` | clean |

## Completion criteria

- Neither `test_admin_token_grants_all_roles` nor
  `test_shared_token_grants_all_roles_for_backward_compat` exists in the file.
- `uv run pytest tests/eventbus/test_eventbus_auth.py` collects exactly 2 fewer tests
  than the pre-change baseline and passes.
- `test_distinct_tokens_get_exactly_their_documented_role`,
  `test_shared_and_admin_tokens_have_no_consumer_bypass` and
  `test_control_plane_token_cannot_use_consumer_routes` remain present and green.
- `ruff check` on the file is clean.

## Out of Scope

- Any modification to `scripts/eventbus/auth.py` or other production code.
- ADR-013 or config-doc edits (verified consistent with the code; no drift).
- The identifier-comment cleanup in this file filed under
  `issues/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md` (sequenced after
  this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the two synthetic all-roles tests (REQ-001) | Completed | — | 20261029-103558 |  |
| 2 | Run the file and full EventBus suite; confirm collection delta (REQ-001, REQ-002) | Completed | — | 20261029-103558 |  |
| 3 | ruff on the changed file (REQ-001) | Completed | — | 20261029-103558 |  |

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
- **Source issue**: `issues/20261028-122206_ebgen001_authz-generation-role-tests.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-231549_ebgen001_authz-generation-role-tests.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-072757
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`
## Goal

- Switch `tests/eventbus/conftest.py::_reset_auth_state` from snapshot/restore of `_TOKEN_PRINCIPAL_MAP` to snapshot/republish of `auth._CURRENT_GENERATION`, so the autouse fixture enforces the generation lifecycle for every EventBus test (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- One fixture rewrite (lines 55-68); the db_conn fixture above it (lines 40-53) is untouched. Part of the Plan's single atomic Phase 1 cutover; it is the restoration mechanism that replaces every per-test `clear()/update()/pop()` block (sibling documents 01, 07-14).

## Assumptions

- Fixture verified 2026-11-07 at HEAD `1a13653e8` (lines 55-68): snapshots `getattr(auth, "_TOKEN_PRINCIPAL_MAP", {})` and contains the odd double `monkeypatch.setattr` (restoring the same live object twice).
- UNK-01: lifespan side effects of `make_eventbus_client` publish new generations; because the fixture snapshots the generation object (identity, not content) at test start and republishes it on teardown, any generation published during the test — lifespan baseline included — is rolled back (Plan Unknowns resolution path).

## Design decisions

- Restore by identity republish: `monkeypatch.setattr(auth, "_CURRENT_GENERATION", original_generation)` after yield — republishing the exact previous `AuthzGeneration` object keeps generation numbering and principal identity intact for follow-on assertions (Plan Design "Test discipline").
- The `original_map = getattr(auth, "_TOKEN_PRINCIPAL_MAP", {})` snapshot and both alias `monkeypatch.setattr` calls are deleted; `original_generation = auth.current_generation()` (may legitimately be `None`) is the new snapshot.

## Alternatives considered

- Restoring by rebuilding a generation from the old principals dict: rejected — creates a new generation number and breaks identity assertions the suite relies on (e.g. `current_generation() is granted` in `test_authz_generation_ttl.py`); identity republish is exact.

## Implementation
### Target file
`tests/eventbus/conftest.py`

### Procedure
1. In `_reset_auth_state` (lines 55-68): replace the docstring's alias wording with generation wording ("`_CURRENT_GENERATION` is published at runtime by the app lifespan or by test helpers via `publish_generation()`; preserving it prevents test-to-test generation leakage").
2. Replace `original_map = getattr(auth, "_TOKEN_PRINCIPAL_MAP", {})` with `original_generation = auth.current_generation()`.
3. Replace the `monkeypatch.setattr(auth, "_TOKEN_PRINCIPAL_MAP", ...)` teardown line with a direct restore: `try: yield finally: auth._CURRENT_GENERATION = original_generation` (second revision during implementation — a before-`yield` `monkeypatch.setattr` was tried first, but tests that call `monkeypatch.undo()` mid-test (`test_eventbus_requeue_edge_cases.py`, `test_eventbus_concurrent.py`, `test_eventbus_dlq_outbox.py`) share the same function-scoped `monkeypatch` fixture instance and would undo this autouse fixture's patch too, rewinding the generation the test's own lifespan just published — observed as 401 failures in 4 deploy/eventbus tests. Direct module-attribute assignment in a post-`yield` finally block is immune to `monkeypatch.undo()`).
4. Drop the `monkeypatch: pytest.MonkeyPatch` fixture parameter (no longer needed); keep the autouse decorator.

### Method
- Verified current body at HEAD `70391b306`: decorator line 55, def line 56, `from eventbus import auth` line 64, snapshot line 66, `yield` line 67, single teardown setattr at line 68 (the Plan-era note of "two setattrs" does not match the current file — only one exists; the fixture's docstring 57-62 also references `_TOKEN_PRINCIPAL_MAP` and is rewritten by this procedure).

### Details
- Fixture ordering is unchanged; the db_conn fixture (lines 40-53) and any other conftest content stay as-is.

## Compatibility considerations

- Tests that intentionally assert a generation published during the test (ttl, admin_topics no-op cases) still observe it inside the test; only teardown rolls back. Cross-file leakage detection relies on running the whole `tests/eventbus/` suite in order (Plan Validation row 2).

## Security considerations

- N/A: fixture mechanics only; tokens never logged (unchanged).

## Rollback considerations

- Revert of the single atomic commit restores the old fixture (Plan Design "Atomicity").

## Validation plan

- `uv run pytest tests/eventbus/ -q` — green, no fixture-order dependence (AC-003, Plan Validation row 2).
- `grep -n "_TOKEN_PRINCIPAL_MAP" tests/eventbus/conftest.py` -> no matches (AC-001).
- Completion gates per `rules/toolchain.md` run in the Plan Phase 3 pass.

## Completion criteria

- The fixture snapshots/restores `_CURRENT_GENERATION` only; no EventBus test leaks a published generation into the next (AC-003).

## Out of Scope

- The helper functions tests use to publish — sibling document 04.
- Per-test mutation-block conversions — sibling documents 01 (companion), 07-14.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `_reset_auth_state` (lines 55-68) to generation snapshot/republish — Plan Phase 1 | Completed | 20261107-152722 | 20261107-152722 | generation-restore fixture landed (setattr registered before yield) |
| 2 | Run the validation sequence (`rules/toolchain.md`) in the Plan Phase 3 pass | Completed | 20261107-152722 | 20261107-152722 | whole-suite order run verifies restoration full suite 11784 passed diff-cover 100pct |

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
- **Related target files**: `tests/eventbus/conftest.py`
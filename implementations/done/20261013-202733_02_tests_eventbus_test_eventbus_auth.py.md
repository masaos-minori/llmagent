## Goal

Add and update the EventBus CONSUMER-authorization unit tests in
`tests/eventbus/test_eventbus_auth.py` that verify the EVENTBUS-008 deny-all resolution:
an empty-mapping CONSUMER token denies every `consumer_id`, a non-empty mapping still
restricts to its allowlist, the superuser path is unchanged, and a missing key still
raises. Also correct the `TestFailClosedConsumerAuthorization` docstring that documents the
old empty-`{}`→unrestricted behavior.

## Scope

Single file: `tests/eventbus/test_eventbus_auth.py`. Changes:

- Update the `TestFailClosedConsumerAuthorization` class docstring (lines 862-864).
- Add a deny-all test (empty mappings) and a non-empty allowlist regression test inside
  `TestFailClosedConsumerAuthorization`.
- Confirm (do not duplicate) the missing-key-still-raises and superuser-unchanged coverage
  that already exists.

## Assumptions

- Tests live in the same repo venv (`uv run pytest`); `eventbus.auth` is importable as
  `from eventbus.auth import ...`.
- The `prod_client` fixture (line 1243, `consumer_authorization={}`) gates on ROLE only and
  passes no `consumer_id`, so deny-all does not affect it.
- `UNK-01` is resolved to deny-all at runtime (`frozenset()`); tests assert that sentinel.

## Design decisions

- Put the new deny-all / non-empty tests in the existing `TestFailClosedConsumerAuthorization`
  class so they share its setup/teardown and stay co-located with the docstring being fixed.
- Assert the deny-all outcome at two levels: the resolved `Principal` state
  (`allowed_consumer_ids == frozenset()`) for REQ-001, and an end-to-end rejection through
  `require_consumer_identity()` for REQ-002, reusing the existing request-mock pattern.
- Prefer confirming existing coverage for REQ-004/REQ-005 over adding duplicates.

## Alternatives considered

- Adding a brand-new test class for the new cases: rejected; `TestFailClosedConsumerAuthorization`
  is the semantically correct home and keeps the docstring fix adjacent to its tests.
- Deriving REQ-004/REQ-005 from brand-new tests: rejected; existing tests already assert
  `allowed_consumer_ids is None` for superuser tokens and `ValueError` for a missing key.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

1. **Correct the docstring (REQ-001).** In `TestFailClosedConsumerAuthorization` (lines
   862-864), replace the sentence documenting empty-`{}`→unrestricted ("An empty mapping {}
   is accepted and leaves the consumer token unrestricted; only None is rejected — never
   weaken this guarantee.") with deny-all semantics: an empty mapping resolves to
   `frozenset()` (deny-all), and only `None` (missing key) raises at startup.
2. **Add a deny-all test (REQ-001, REQ-002, T-1).** Inside the class, add
   `test_empty_mappings_deny_all_consumers` (new): build an `EventBusConfig` with `consumer_token`
   set and both `consumer_authorization={}` and `topic_authorization={}`, call
   `_populate_token_maps(cfg)`, and assert the CONSUMER principal has
   `allowed_consumer_ids == frozenset()` and `allowed_topics == frozenset()`. Then assert
   `require_consumer_identity(...)` rejects a sample `consumer_id` with HTTP 403, reusing the
   request-mock / audit-record pattern from
   `test_consumer_identity_rejection_produces_structured_audit_record`.
3. **Add a non-empty allowlist regression test (REQ-003, T-2).** Add
   `test_non_empty_mapping_restricts_to_allowlist` (new): build a config with a non-empty
   `consumer_authorization`/`topic_authorization`, assert the CONSUMER principal is restricted
   to the union allowlist, and that a `consumer_id` outside the allowlist is rejected while one
   inside is allowed.
4. **Confirm the missing-key-still-raises test (REQ-005, T-4).** The existing
   `test_consumer_token_without_consumer_authorization_raises` (line 867) already asserts
   `pytest.raises(ValueError, match="consumer_authorization is missing")`. Verify it still
   passes after the auth.py change; do not duplicate it.
5. **Confirm the superuser-unchanged test (REQ-004, T-3).** Existing tests
   `test_admin_token_grants_all_roles` (line 769) and
   `test_shared_token_grants_all_roles_for_backward_compat` (line 799) already assert
   `allowed_consumer_ids is None` for superuser tokens. Verify they still pass; do not
   duplicate them.

### Method

- New tests are `@staticmethod` (matching the class's existing `test_consumer_token_...`
  style) or instance methods if they need the class fixtures; keep consistent with the class.
- For the `require_consumer_identity` rejection assertion, construct a minimal request object
  exposing `request.state.request_id` and `request.url.path` (see the existing audit-record
  tests), and assert the raised `HTTPException` has `status_code == 403`.
- Mirror the snapshot/restore of `_TOKEN_PRINCIPAL_MAP` used by the existing missing-key test
  (lines 871-888) to avoid cross-test contamination.

### Details

- REQ-001 assertion is the resolved state: `principal.allowed_consumer_ids == frozenset()`
  (empty, not `None`). An empty `frozenset()` is falsy, so assert equality explicitly — do
  not assert truthiness.
- REQ-002 end-to-end path exercises `resolve_principal` → `require_consumer_identity`; reuse
  the helper already present in the class/module rather than building a new one.
- The non-empty regression (REQ-003) must use a mapping whose union is non-empty and assert
  both an in-allowlist `consumer_id` is accepted and an out-of-allowlist one is rejected.

## Compatibility considerations

- The `prod_client` fixture (line 1243) sets `consumer_authorization={}`; under deny-all the
  CONSUMER principal becomes `frozenset()`, but every ROLE-gated route test passes no
  `consumer_id`, so these tests are unaffected. Run the full suite to confirm.
- The fixture's inline comment at lines 1241-1242 describes `{}` as "unrestricted", which is
  now inaccurate. It is intentionally left unchanged to stay within the frozen scope; treat
  it as a known stale comment to clean up in a follow-up, not part of this change.

## Security considerations

- Tests pin the fail-closed sentinel: assert `== frozenset()` (deny-all), never that the
  value is "falsy/unrestricted". A test that only checks falsiness would accept `None` and
  hide the fail-open regression.
- Ensure the deny-all rejection test actually drives `require_consumer_identity` (not just the
  resolved state) so a logic slip in the rejection path is caught.

## Rollback considerations

- Single-file revert (`git checkout tests/eventbus/test_eventbus_auth.py`) restores prior
  tests. Reverting the auth.py change is covered in the auth.py document.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_auth.py` | Unit: new deny-all + non-empty regression green; existing superuser/missing-key tests still pass | `uv run pytest tests/eventbus/test_eventbus_auth.py` | All pass; no regression in ROLE-gated `prod_client` tests |
| `tests/eventbus/test_eventbus_auth.py` | Full suite sanity | `uv run pytest` | No new failures |

## Completion criteria

- `TestFailClosedConsumerAuthorization` docstring reflects deny-all (empty → `frozenset()`),
  not empty→unrestricted.
- A deny-all test asserts `allowed_consumer_ids == frozenset()` and that every `consumer_id`
  is rejected via `require_consumer_identity`.
- A non-empty regression test asserts allowlist restriction (in-allowlist allowed,
  out-of-allowlist rejected).
- Missing-key (`None`) still raises; superuser tokens remain `allowed_consumer_ids=None`.
- Full EventBus suite passes.

## Out of scope

- Any change to `scripts/eventbus/auth.py` logic — handled in the auth.py document.
- Modifying the `prod_client` fixture body or other test classes beyond the docstring fix.
- Other roles' authorization tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 2026-10-14 | 2026-10-14 | Drives config.py empty-mapping deny-all fix; covers superuser auth_token/admin_token residual deviation |
| 2 | Add or update tests per Validation plan | Done | 2026-10-14 | 2026-10-14 | test_empty_mappings_deny_all_consumers added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 2026-10-14 | 2026-10-14 | 40 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 2026-10-14 | 2026-10-14 | ADR-013/ADR-006 EVENTBUS-008 resolution documented (commit 6dabbf63a) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20261013-161114_eballow01_require-non-empty-consumer-authorization-for-eventbus-consumer-token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-185233_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-202733
- **Related target files**: tests/eventbus/test_eventbus_auth.py

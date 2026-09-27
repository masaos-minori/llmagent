## Goal

Fix `tests/eventbus/test_eventbus_auth.py`'s 5 failures across two independent clusters: (a) remove the unsupported `_principal` keyword argument from `_make_test_app`'s local `dlq_list`/`replay` route wrappers (REQ-001); (b) give the 3 `require_consumer_identity`-unit-testing tests a `request` stand-in with real string `.state.request_id`/`.url.path` values instead of a bare `MagicMock()` (REQ-002).

## Scope

In scope: `_make_test_app`'s `dlq_list`/`replay` wrappers and the 3 named tests' `request` stand-in, all in this file. Out of scope: `scripts/eventbus/dlq_route.py`'s `dlq_list()`, `scripts/eventbus/replay_route.py`'s `replay()`, `scripts/eventbus/auth.py`'s `require_consumer_identity`/`log_auth_failure`, and `scripts/eventbus/audit.py`'s `orjson.dumps` call — all confirmed already correct for real production call patterns.

## Assumptions

- The real `scripts/eventbus/app.py` route wrappers for `/dlq` and `/replay` are the authoritative call pattern this file's local wrappers should mirror (no `_principal` forwarding for these two routes specifically).

## Design decisions

- REQ-001: remove `_principal=_principal` from both wrapper calls, matching the real `app.py` wrapper's exact call pattern (`dlq_list_route(request, limit=limit, offset=offset)` / equivalent for `replay`).
- REQ-002: set explicit string values for `.state.request_id`/`.url.path` on each test's `request` stand-in immediately before calling `require_consumer_identity`, preserving the `MagicMock()`-based approach (minimal diff) rather than switching to a different fake-request mechanism.

## Alternatives considered

- REQ-002: introducing a shared `_fake_request()` helper used by all 3 tests instead of inline per-test attribute assignment: considered reasonable but not required by the Plan's evidence — this document uses the simpler per-test inline assignment to keep the diff minimal; a shared helper can be introduced later if a 4th such test appears.

## Implementation

### Target file

`tests/eventbus/test_eventbus_auth.py`

### Procedure

1. **REQ-001**: re-confirm `_make_test_app`'s `dlq_list`/`replay` wrapper bodies via Read (lines ~119-154) — confirm `_principal=_principal` is still passed to `eb_app.dlq_list_route(...)`/`eb_app.replay_route(...)`. Remove that keyword argument from both calls, matching the real `app.py` wrapper's call pattern (no `_principal` forwarding for these two routes).
2. **REQ-002**: for each of `test_non_empty_topic_restriction_is_enforced_and_returned`, `test_topic_authorization_rejection_produces_structured_audit_record`, `test_consumer_identity_rejection_produces_structured_audit_record`, replace the bare `MagicMock()` passed as `request` to `require_consumer_identity(...)` with a `MagicMock()` whose `.state.request_id` and `.url.path` are explicitly set to string literals (e.g. `request_mock = MagicMock(); request_mock.state.request_id = "test-request-id"; request_mock.url.path = "/test-route"`) before the call.

### Method

Step 1: direct keyword-argument removal at 2 call sites. Step 2: per-test `request` stand-in enhancement (add 2 explicit attribute assignments before each `require_consumer_identity(...)` call) — no change to the tests' actual assertions on `HTTPException`/audit-record structure.

### Details

- REQ-001 before: `result: dict[str, Any] = await eb_app.dlq_list_route(request, limit=limit, offset=offset, _principal=_principal)`; after: `result: dict[str, Any] = await eb_app.dlq_list_route(request, limit=limit, offset=offset)`. Apply the analogous change to the `replay` wrapper's call to `eb_app.replay_route(...)`.
- REQ-002: confirm via Read the exact current `MagicMock()` construction in each of the 3 tests before adding the 2 attribute assignments — some tests may construct `request` once and reuse it across multiple `require_consumer_identity` calls within the same test body (per this session's earlier investigation of `test_non_empty_topic_restriction_is_enforced_and_returned`, which calls it twice with different `topics` arguments) — set the attributes once on the shared `request` object, not per-call.
- `log_auth_failure`'s downstream `orjson.dumps` call (`scripts/eventbus/audit.py`) requires `request_id`/`route` to be JSON-serializable strings — confirm the assigned values satisfy this (plain string literals do).

## Compatibility considerations

- No production code changes; both fixes are test-infrastructure corrections restoring compatibility with already-correct production call patterns/data types.

## Security considerations

N/A: test-only fixes, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the prior `_principal` keyword arguments and bare `MagicMock()` request objects.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_auth.py` | Integration/Unit | `uv run pytest tests/eventbus/test_eventbus_auth.py -q` | All tests pass, including the 5 previously-failing ones |

## Completion criteria

- `uv run pytest tests/eventbus/test_eventbus_auth.py -q` passes with no failures.
- The 3 REQ-002 tests genuinely exercise `require_consumer_identity`'s `HTTPException`/audit-record-structure assertions (confirmed by the test passing for the right reason, not by weakening any assertion).

## Out of scope

- `scripts/eventbus/dlq_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/auth.py`, `scripts/eventbus/audit.py` (all confirmed already correct).
- Other eventbus test files tracked under separate Plans/issues.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 5 tests is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001, REQ-002: fix `dlq_list`/`replay` wrapper duplicates and the 3 tests' `request` stand-in
- **Source issue**: issues/20260927-075244_eb004_eventbus-auth-audit-test-failures-magicmock-serialization-and-status-codes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-083315_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092434
- **Related target files**: tests/eventbus/test_eventbus_auth.py

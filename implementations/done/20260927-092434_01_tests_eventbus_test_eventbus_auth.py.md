## Goal

Fix `tests/eventbus/test_eventbus_auth.py`'s 5 failures across three independent clusters: (a) remove the unsupported `_principal` keyword argument from `_make_test_app`'s local `dlq_list`/`replay` route wrappers (REQ-001); (b) give the `test_non_empty_topic_restriction_is_enforced_and_returned` unit test a `request` stand-in with real string `.state.request_id`/`.url.path` values instead of a bare `MagicMock()` (REQ-002); (c) wire `/subscribe`'s `require_consumer_identity` dependency to receive the real `consumer_id`/`topic` query args so the caller's identity/topic allowlists are actually enforced (REQ-003), and configure the consumer-token allowlist in `_make_test_app` so the two rejection tests exercise a non-empty allowlist.

## Scope

In scope: `_make_test_app`'s `dlq_list`/`replay` wrappers and the `test_non_empty_topic_restriction_is_enforced_and_returned` `request` stand-in (this file); the `/subscribe` route wrapper in `scripts/eventbus/app.py` so `require_consumer_identity` receives the real `consumer_id`/`topic`; and the consumer-token allowlist configured inside `_make_test_app`. Out of scope: `scripts/eventbus/dlq_route.py`'s `dlq_list()`, `scripts/eventbus/replay_route.py`'s `replay()`, `scripts/eventbus/auth.py`'s `require_consumer_identity`/`log_auth_failure` body, and `scripts/eventbus/audit.py`'s `orjson.dumps` call — all confirmed already correct; the failure was that `app.py`'s `/subscribe` dependency passed empty defaults so the (already-correct) allowlist checks never fired.

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

## Execution deviations

The original plan scoped this as test-infrastructure only. Adversarial verification
(Step 3) showed failures 4 and 5 (`test_consumer_identity_rejection_produces_structured_audit_record`,
`test_topic_authorization_rejection_produces_structured_audit_record`) hang the SSE
stream because `app.py`'s `/subscribe` declared `_identity = Depends(require_consumer_identity)`
with no arguments, so `require_consumer_identity` received `consumer_id=""`/`topics=None`
and never rejected. A test-only fix cannot make those two assertions pass: they assert a
403 plus a structured audit record emitted by `require_consumer_identity`, which requires
the real `consumer_id`/`topic`. Per the user's explicit directive ("4,5も全て通す本番修正まで行う"),
REQ-003 added a production fix: a `resolve_subscribe_identity` dependency in both
`scripts/eventbus/app.py` and this file's `_make_test_app` that forwards the actual
`consumer_id`/`topic` query args (and resolves `principal` via `Depends(resolve_principal)`
so the direct call does not raise). The consumer-token allowlist is set inside `_make_test_app`
(`allowed_consumer_ids=frozenset({"consumer_a","consumer_b"})`, `allowed_topics=frozenset({"test"})`)
mirroring the per-fixture overrides used by the other eventbus test modules. This expands the
Target file / Scope to include `scripts/eventbus/app.py`. No other behavior changed; the full
eventbus suite shows exactly these 5 fixes with zero new failures (remaining failures are
pre-existing and unrelated).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260927-171739 | Removed _principal kwarg from dlq_list/replay wrappers (REQ-001) |
| 2 | Add or update tests per Validation plan | Completed | — | 20260927-171739 | N/A: fixing the existing 5 tests is itself the fix Gave test_non_empty_topic_restriction_is_enforced_and_returned a shared string-valued request stand-in (REQ-002) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260927-171739 | ruff clean; pytest: 5 target failures fixed, zero new failures (other failures pre-existing). mypy has pre-existing tool_constants collision (unrelated) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260927-171739 | N/A: no docs/00_index.md task-scope mapping for this test file N/A: no docs/00_index.md task-scope mapping for this test file |

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
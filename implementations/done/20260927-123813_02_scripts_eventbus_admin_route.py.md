## Goal

Create `scripts/eventbus/admin_route.py`: the handler for `POST /admin/topics/authorization`, validating the request body and applying the authorization update (REQ-001, REQ-003).

## Scope

In scope: request parsing/validation and delegating to the authorization-update logic. Out of scope: the exact internal wiring mechanism the update calls into — **this row is partially blocked by row 3's open question** (see Details); the parts of this row independent of that question (request shape, validation) can proceed now.

## Assumptions

- The exact function this handler calls to apply the update depends on row 3 (`scripts/eventbus/auth.py`)'s Blocked resolution — this document specifies the handler's own request/response contract, which does not change regardless of that resolution.

## Design decisions

- Follow the one-module-per-route convention (`publish_route.py`, `subscribe_route.py`, `dlq_route.py`) — this handler lives in its own file, imported by `app.py` (row 1).
- Validate the request body using the same type constraints `EventBusConfig.__post_init__()` already enforces for `consumer_authorization`/`topic_authorization` (string keys, list/set values of strings), rather than writing a second, independently-worded validation.

## Alternatives considered

- Inlining the handler directly in `app.py`: rejected — breaks the existing one-module-per-route convention.

## Implementation

### Target file

`scripts/eventbus/admin_route.py`

### Procedure

1. Define an async handler function accepting the request body (a dict shaped like `{"consumer_authorization": {...}, "topic_authorization": {...}}`, both optional).
2. Validate the body's type shape using the same rules as `EventBusConfig.__post_init__()`'s existing `consumer_authorization`/`topic_authorization` checks (confirmed via Read of `scripts/eventbus/config.py`) — string keys, list/set values of strings; reject with a 4xx `HTTPException` on violation, before mutating any state.
3. Construct the validated new values in local variables first; only after validation passes, assign them to `app.state.config.consumer_authorization`/`topic_authorization` (per REQ-003's requirement not to corrupt in-memory state on a partial/invalid update).
4. Call the (row-3-dependent) authorization-refresh function — **the exact function name and signature depend on row 3's Blocked resolution; do not implement this call until that row is unblocked and this document is updated to reference the actual function.**
5. Return a success response confirming the update was applied.

### Method

New route-handler module, following the existing one-module-per-route convention; request validation reuses existing `EventBusConfig` validation logic rather than duplicating it.

### Details

- **Blocked dependency**: this row's step 4 cannot be finalized until `scripts/eventbus/auth.py` (row 3, currently Blocked — see that document's Blocker Log) resolves whether `consumer_authorization`/`topic_authorization` are enforced per-token (via `Principal`) or per-request (via `require_consumer_identity()`). If per-token: this handler calls the extended `_populate_token_maps()`. If per-request: this handler may not need to call anything beyond updating `app.state.config` itself, since `require_consumer_identity()` could read `app.state.config.consumer_authorization`/`topic_authorization` directly at request time without a separate refresh step. **Do not implement step 4 speculatively — wait for row 3's resolution.**
- `scripts/eventbus/config.py::EventBusConfig.__post_init__()`'s existing type-validation for these two fields is the exact logic to reuse for step 2.

## Compatibility considerations

New module, no existing callers until row 1 wires it in.

## Security considerations

Step 3's "validate into local variables first" ordering (not REQ-003's literal wording, but its intent) prevents a partially-invalid request from corrupting `app.state.config` mid-validation.

## Rollback considerations

New, uncalled-until-wired file — revert via `git revert` or deletion; row 1's import would need to be reverted alongside it.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/admin_route.py` | Unit + Integration | `uv run pytest tests/eventbus/test_admin_topics_authorization.py -q` | Auth gating, validation, and update-takes-effect tests all pass |
| `scripts/eventbus/admin_route.py` | Static | `uv run ruff check scripts/eventbus/admin_route.py && uv run mypy scripts/eventbus/admin_route.py && uv run bandit -r scripts/eventbus/admin_route.py -c pyproject.toml` | All pass |

## Completion criteria

- A valid request updates authorization and a subsequent subscribe/publish request reflects it (AC-1) — **not achievable until row 3 unblocks**.
- An invalid request body is rejected with a 4xx response without corrupting state (AC-3) — achievable independent of row 3.

## Out of scope

- The exact authorization-refresh mechanism (row 3's concern).
- Route registration and ADMIN gating (row 1's concern).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement request parsing and validation (Procedure steps 1-3) | Completed | 20260927-144037 | 20260927-144037 | Not blocked — can proceed independently of row 3 CORRECTION (found during row 5's integration testing): EventBusConfig is a frozen dataclass — the original implementation's direct attribute mutation (config.consumer_authorization = ...) raised FrozenInstanceError. Fixed to use dataclasses.replace() to build a new config instance and swap it into request.app.state.config, then call _populate_token_maps() on the new instance. Re-validated: ruff/pyright/lint-imports/bandit clean, 5/5 integration tests pass (row 5). |
| 2 | Implement the authorization-update call (Procedure step 4) | Completed | 20260927-144037 | 20260927-144037 | Depends on row 3's Blocker Log resolution |
| 3 | Add or update tests per Validation plan | Completed | 20260927-144037 | 20260927-144037 | Depends on step 2 Covered by tests/eventbus/test_admin_topics_authorization.py (row 5) |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-144037 | 20260927-144037 | Depends on step 2 ruff/pyright/bandit clean. Row 3 unblocked (union-apply, per-token model confirmed) — implemented update_topics_authorization() calling _populate_token_maps() after mutating app.state.config |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-144037 | 20260927-144037 | N/A: no `docs/00_index.md` task-scope row maps this new file N/A: no docs/00_index.md task-scope row maps this new file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Depends on `scripts/eventbus/auth.py`'s (row 3) Blocked resolution of the per-token vs. per-request enforcement question | Yes — row 3 resolved (union-apply, per-token) | 20260927-144037 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/done/20260927-115652_eventbus007_implement-agent-eventbus-topic-management-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121125_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123813
- **Related target files**: scripts/eventbus/admin_route.py
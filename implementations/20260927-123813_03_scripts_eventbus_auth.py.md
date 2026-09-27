## Goal

Extend `scripts/eventbus/auth.py::_populate_token_maps()` to wire `config.consumer_authorization`/`topic_authorization` into each per-role token's `Principal.allowed_consumer_ids`/`allowed_topics`, and make it safely re-invocable so the new admin endpoint (row 2 of this Plan) can apply a runtime authorization update (REQ-001).

## Scope

In scope: extending `_populate_token_maps()` (or adding a helper it calls) to consult `consumer_authorization`/`topic_authorization`; confirming the shared `auth_token`/`admin_token` remain unrestricted. Out of scope: `_CONSUMER_ID_ALLOWLIST` (dead variable, not touched by this change); any change to the `Principal` dataclass itself or the enforcement code at lines 238-293 (already correct, just never triggered).

## Assumptions

- Extending the existing per-role-token loop (lines 119-136) is sufficient — no larger restructuring of the Principal model is needed, since the enforcement code already correctly consults `allowed_consumer_ids`/`allowed_topics`.

## Design decisions

- Wire `consumer_authorization` (`consumer_id -> [topics]`) by setting the matching per-role token's `Principal.allowed_topics` when a `consumer_id` maps to it, and `topic_authorization` (`topic -> [consumer_ids]`) as the inverse — confirm the exact precedence/merge rule between the two maps during implementation if both apply to the same token (not resolved by this Plan; a reasonable default is: the union of topics either map grants, unless the owner's future ruling on EVENTBUS-007-adjacent config semantics says otherwise).
- Do not touch `_CONSUMER_ID_ALLOWLIST` — confirmed dead (zero writes anywhere); the real enforcement path is `Principal.allowed_consumer_ids`/`allowed_topics`, not this variable.

## Alternatives considered

- Populating `_CONSUMER_ID_ALLOWLIST` instead of `Principal.allowed_consumer_ids`/`allowed_topics`: rejected — confirmed via Read that `_CONSUMER_ID_ALLOWLIST` has no readers anywhere in `scripts/eventbus/`; populating it would have no runtime effect.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. Re-confirm `_populate_token_maps()` (lines 92-147, as of this Plan's investigation) still does not read `consumer_authorization`/`topic_authorization`, immediately before editing.
2. In the per-role-token loop (currently lines 119-136), after resolving `token`/`role`, look up `config.consumer_authorization`/`topic_authorization` for entries mapping to this token's associated `consumer_id`(s) (the token-to-consumer-id association itself must be confirmed or established during implementation — `consumer_authorization` is keyed by `consumer_id`, not by token, so a token→consumer_id link is needed; check whether one already exists elsewhere in this file before inventing one).
3. Set the resulting `Principal.allowed_consumer_ids`/`allowed_topics` from the looked-up values, leaving `None` (unrestricted) when no matching entry exists — preserving current behavior for tokens with no configured restriction.
4. Explicitly confirm the shared `auth_token` and `admin_token` branches (lines 110-116, 140-147) remain untouched — they must stay unrestricted (`None`) regardless of `consumer_authorization`/`topic_authorization` content, per their existing "grants every role" superuser semantics.
5. Ensure `_populate_token_maps()` remains safely callable a second time at runtime (it already does — confirmed via Read: it starts with `_TOKEN_PRINCIPAL_MAP.clear()`), so the new admin endpoint (row 2) can call it again after updating `app.state.config`.

### Method

Extend an existing function in place, adding new lookups into two existing config fields; no new function signature or public interface change.

### Details

- **Critical open question surfaced during this Plan's own investigation, not yet resolved**: `consumer_authorization` is keyed by `consumer_id` (`dict[str, list[str]]`), but `_populate_token_maps()`'s per-role-token loop operates over *tokens*, not `consumer_id`s — there is no confirmed existing mapping from a specific token to a specific `consumer_id` in the current code (`Principal` has no `consumer_id` field). Before writing this row's code, confirm during implementation whether such a mapping exists elsewhere (e.g. is established at request time via `require_consumer_identity()`'s `consumer_id` parameter, not at token-population time) — if no static token↔consumer_id mapping exists, `consumer_authorization`'s per-consumer semantics may need to be enforced at request time (in `require_consumer_identity()`, which already receives `consumer_id` as a parameter) rather than baked into the token-level `Principal` at startup. This may mean this row's actual change is smaller than originally scoped (e.g. only wiring `topic_authorization`'s topic-level restriction into `Principal.allowed_topics`, with `consumer_authorization`'s per-consumer-id restriction enforced separately in `require_consumer_identity()`) — resolve this before implementing, and correct this document's Procedure if the resolution changes it.

## Compatibility considerations

Existing tokens with no configured `consumer_authorization`/`topic_authorization` entry keep their current unrestricted behavior — this is additive, not a behavior change for existing deployments with these config fields unset (the common case, since they are optional/`None`-defaulted).

## Security considerations

Confirm `auth_token`/`admin_token` remain unrestricted after this change (Procedure step 4) — accidentally restricting the superuser tokens would be a functional regression, not just a security concern, since it could lock out legitimate administrative access.

## Rollback considerations

`git revert` the commit. Since `_populate_token_maps()` is called once at startup regardless, reverting restores the prior always-unrestricted behavior with no data migration concern (no persisted state, only in-memory).

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/auth.py` | Unit | `uv run pytest tests/eventbus/test_admin_topics_authorization.py -q` (covers this file's behavior indirectly via the endpoint) | Auth-restriction tests pass |
| `scripts/eventbus/auth.py` | Static | `uv run ruff check scripts/eventbus/auth.py && uv run mypy scripts/eventbus/auth.py && uv run bandit -r scripts/eventbus/auth.py -c pyproject.toml` | All pass |
| Full suite | Regression | `uv run pytest -q` | No new failures — critically, confirm no existing Event Bus test that assumes `auth_token`/`admin_token` are unrestricted starts failing |

## Completion criteria

- A per-role token with a configured `consumer_authorization`/`topic_authorization` entry is correctly restricted after this change.
- `auth_token`/`admin_token` remain unrestricted (AC-1, security consideration above).
- The open question in Details is resolved one way or the other, and this document (or a corrected version of it) reflects the actual resolution before code is written.

## Out of scope

- `_CONSUMER_ID_ALLOWLIST` (confirmed dead).
- The `Principal` dataclass definition and `require_consumer_identity()`/`resolve_principal()`'s existing enforcement logic (already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Resolve the token↔consumer_id mapping open question (Details) before implementing | Blocked | — | — | See Blocker Log — `consumer_authorization`/`topic_authorization` are keyed by `consumer_id`/`topic`, not by token; no existing mechanism associates a specific token with specific `consumer_id`(s), so REQ-001's "set Principal.allowed_consumer_ids/allowed_topics per token" approach may not be the correct enforcement point |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | — | — | Depends on step 1 |
| 3 | Add or update tests per Validation plan | Blocked | — | — | Depends on step 1 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Blocked | — | — | Depends on step 1 |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Blocked | — | — | Depends on step 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `consumer_authorization: dict[consumer_id, list[topics]]` and `topic_authorization: dict[topic, set[consumer_ids]]` have no confirmed association to a specific auth token in current source — `Principal` (the per-token authorization object `_populate_token_maps()` builds) has no `consumer_id` field, so it is unclear whether REQ-001's per-token restriction is the correct enforcement point, or whether `consumer_authorization`/`topic_authorization` should instead be enforced at request time in `require_consumer_identity()` (which already receives `consumer_id` as a request parameter) independent of which token authenticated the caller. Requires an owner/architect decision on the intended enforcement model before this row can be implemented. | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260927-115652_eventbus007_implement-agent-eventbus-topic-management-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121125_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123813
- **Related target files**: scripts/eventbus/auth.py

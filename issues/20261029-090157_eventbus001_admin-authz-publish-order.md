# Build and publish the principal map before the configuration in the admin authorization update

## Priority
Low

## Summary
Make `update_topics_authorization()` build the replacement principal map first and publish the replacement configuration only after that build succeeds, so a failed principal-map build can never leave a new configuration active next to the previous principal generation. Add a test for that failure path.

## Background
Source: `memo-issue.md` item 01 (runtime authorization updates), re-verified against current source on 2026-10-29. Most of that item is already resolved or planned:
- `_populate_token_maps()` in `scripts/eventbus/auth.py` already builds the new map in a local dict and publishes it with one assignment through `publish_principals()` (`Explicit in code`). The in-place `clear()` window described by the archived `issues/done/20261023-154326_eventbus006_runtime-authorization-update-consistency.md` is gone.
- The admin route already validates the body before mutating state, rejects an empty body, reports `persistent: false`, and skips both the swap and the audit record on a no-op (`Verified by test` in `tests/eventbus/test_admin_topics_authorization.py`).
- The two synthetic all-roles tests in `tests/eventbus/test_eventbus_auth.py` are removed by `plans/20261028-231549_ebgen001_authz-generation-role-tests.md`.

One ordering defect remains (`Explicit in code`): `update_topics_authorization()` assigns `request.app.state.config` first and calls `_populate_token_maps(config)` afterwards. If `_populate_token_maps()` raises, the new configuration stays published while the old principal map stays active. The archived issue listed "publish the config and the map together, so a failed rebuild leaves the previous generation intact" as a Required Change, and only the map half was implemented.

## Problem
The configuration publish and the principal-map publish are two separate steps in a fixed, unsafe order. A failure between them leaves a mixed generation, and the existing failure-path test (`test_invalid_body_rejected_without_corrupting_state`) covers only body validation, not a failing principal-map build.

## Reason for Change
Authorization state is security-sensitive, and a failed update should leave the previous generation fully active. Severity is Low because no input reachable through the admin route was found that makes `_populate_token_maps()` fail: the update replaces only the two authorization mappings, and token-field checks depend on unchanged token fields. This is a defensive ordering fix, not a reproduced defect. It is not time-sensitive.

## Implementation Intent
Order the steps as validate, build the replacement `EventBusConfig` without publishing it, build the replacement principal map from that config, then publish both. If any build step raises, nothing is published. Keep `_populate_token_maps()` as the single place that derives principals from a config, and keep the runtime-only persistence contract. Prefer the smallest change that achieves the ordering, for example a build function that returns the map and a separate publish step, over introducing a new generation object.

## Target Files or Areas
- `scripts/eventbus/admin_route.py` (`update_topics_authorization`)
- `scripts/eventbus/auth.py` (`_populate_token_maps`, `publish_principals`) only if the build and publish steps must be separated
- `tests/eventbus/test_admin_topics_authorization.py`

## Required Changes
- Reorder `update_topics_authorization()` so the configuration is published only after the replacement principal map has been built successfully.
- If needed, split `_populate_token_maps()` into a build step that returns the map and the existing publish step, keeping the current behavior for startup callers.
- Add a regression test in which the principal-map build raises during an effective admin update, asserting that both `app.state.config` and the active principal map are unchanged and that the route does not report success.

## Constraints
- The admin route keeps its current request and response contract (`status`, `persistent`, `changed`).
- Duplicate-token and missing-`consumer_authorization` checks keep failing closed without exposing token values.
- The update stays runtime-only; no file write is introduced.

## Acceptance Criteria
- When the principal-map build raises, `app.state.config` still holds the previous configuration and the active principal map is the previous generation.
- A successful effective update publishes the new configuration and the new principal map, and a no-op update publishes neither.
- Existing tests in `tests/eventbus/test_admin_topics_authorization.py` and `tests/eventbus/test_eventbus_auth.py` pass unchanged.

## Testing Expectations
- New failure-path regression test as described in Required Changes, using a patched build step.
- `uv run pytest tests/eventbus` passes.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, and `uv run bandit -r scripts/eventbus -c pyproject.toml -ll` pass for the changed files.

## Documentation Impact
No documentation change is expected. If the build and publish steps are separated, check that the EventBus authorization description in `docs/24_eventbus/` does not state the old order; correct it only if it does.

## Out of Scope
- Serializing concurrent admin updates, a generation-counter object, and any change to the token-to-role matrix (see Unresolved Questions for the concurrency reasoning).
- Audit record content (`request_id`, actor, scope summary), which belongs to `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`.
- Removing the all-roles tests, which belongs to `plans/20261028-231549_ebgen001_authz-generation-role-tests.md`.

## Dependencies
- Coordinate with `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`: both change `update_topics_authorization()` in `scripts/eventbus/admin_route.py` and add tests to `tests/eventbus/test_admin_topics_authorization.py`. Land the audit plan first or rebase carefully; the regions differ (publish order versus audit call arguments).
- Related, no ordering required: `plans/20261028-231549_ebgen001_authz-generation-role-tests.md` (tests in a different file).

## Unresolved Questions
- `Needs confirmation`: after `await request.json()`, the handler contains no further `await`, so other coroutines cannot interleave between the two publish steps. Whether any thread-based reader (for example a worker run through `run_with_db_lock`) reads the authorization configuration or the principal map is not confirmed. If none does, the only effect of this issue is the failed-build case, which is why the priority is Low.
- `Needs confirmation`: whether any input can make `_populate_token_maps()` raise during an admin update. If the owner prefers not to change production code for an unreachable path, close this issue as not needed after confirming.

## AI Implementation Instruction
- Change only the publish order in `update_topics_authorization()` and the minimum needed in `scripts/eventbus/auth.py`; do not refactor unrelated authorization code.
- Preserve public behavior and the response shape; do not add persistence, locks, or a generation object unless the owner asks.
- Do not log or return token values.
- If the Unresolved Questions show the failure path is unreachable and the owner declines the change, stop and report instead of implementing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-090157
- **Related target files**: `scripts/eventbus/admin_route.py`, `scripts/eventbus/auth.py`, `tests/eventbus/test_admin_topics_authorization.py`

# EventBus per-role token feature is incomplete: misplaced validation and un-updated test fixtures

## Priority
High

## Summary
The per-role token feature added to `scripts/eventbus/config.py` is only partially
wired up: its validation code is misplaced inside an unrelated loop, and the callers
that construct `EventBusConfig`/TOML fixtures across `tests/eventbus/` were not
updated to satisfy its new requirements, so most of the auth-related test suite fails
at setup with `ValueError`.

## Background
N/A: covered by Summary

## Problem
Three related defects, all stemming from the same incomplete rollout:

1. In `scripts/eventbus/config.py`'s `load_config()`, the `auth_token`-non-empty check
   and the per-role-token-required check are indented one level too deep — inside the
   `for key, expected_type in _CONFIG_KEY_TYPES.items():` type-validation loop instead
   of after it. This does not change the validation *outcome* (the same checks still
   run, just redundantly per iteration) but is a clear structural mistake that should
   not ship as-is.
2. `EventBusConfig`'s own `__post_init__` only requires `auth_token` to be non-empty;
   it has no equivalent check that at least one per-role token
   (`consumer_token`/`operator_token`/`admin_token`) is set. That requirement exists
   only in `load_config()`'s TOML-parsing path, so directly constructing
   `EventBusConfig(...)` (as most test fixtures do) never sees it — an asymmetry
   between the two construction paths.
3. Several existing test fixtures predate the per-role token requirement and were
   never updated: `tests/eventbus/test_eventbus_auth.py`'s `_make_test_app()` helper
   defaults `token` to `None` (not `EventBusConfig.auth_token`'s expected `str`), has
   no `publisher_token` parameter at all despite a caller's comment saying "using
   per-role tokens only", and several call sites pass `token=None` explicitly.
   `tests/eventbus/test_eventbus_config.py::test_load_config_succeeds_without_stray_keys`
   and `tests/eventbus/test_eventbus_subscribe.py`'s fixtures likewise construct
   configs with no per-role token set.

## Reason for Change
Confirmed by repository evidence: running `tests/eventbus/test_eventbus_auth.py` and
`tests/eventbus/test_eventbus_subscribe.py` produces `ValueError: auth_token is
required but not configured` or `ValueError: At least one per-role token must be
configured` at test *setup* (13 errors in `test_eventbus_auth.py` alone, plus 2 in
`test_eventbus_subscribe.py` and 2 in `test_eventbus_config.py`), meaning the entire
per-role-token authorization path currently has no passing test coverage.

## Implementation Intent
Fix the config.py indentation so the two validation checks run once, after the
type-validation loop, not once per known config key. Decide and apply one consistent
rule for whether `EventBusConfig`'s direct-construction path should also enforce the
per-role-token requirement (recommended: yes, to avoid the exact asymmetry that let
this go untested). Then update every affected test fixture in `tests/eventbus/` to
supply values that satisfy the current requirements, and finish `_make_test_app()`'s
per-role-token support (add the missing `publisher_token` parameter) so the "per-role
tokens only" test cases it currently only comments about actually work.

## Target Files or Areas
- `scripts/eventbus/config.py` (`load_config()` validation block; possibly
  `EventBusConfig.__post_init__`)
- `tests/eventbus/test_eventbus_auth.py` (`_make_test_app()` and its call sites)
- `tests/eventbus/test_eventbus_config.py`
- `tests/eventbus/test_eventbus_subscribe.py`

## Required Changes
- Move the `auth_token`-non-empty and per-role-token-required checks out of the
  `_CONFIG_KEY_TYPES` loop in `load_config()` so each runs exactly once.
- Decide whether `EventBusConfig.__post_init__` should also enforce "at least one
  per-role token configured", and apply that decision consistently.
- Add a `publisher_token` parameter to `_make_test_app()` in
  `tests/eventbus/test_eventbus_auth.py`, and update every call site that currently
  passes `token=None` (or omits per-role tokens) to supply values satisfying the
  current requirements.
- Update `tests/eventbus/test_eventbus_config.py`'s and `tests/eventbus/
  test_eventbus_subscribe.py`'s config-construction fixtures the same way.

## Constraints
Do not weaken the underlying security intent (requiring at least one credential to be
configured) to make tests pass — fix the fixtures to supply valid tokens instead.

## Acceptance Criteria
- `load_config()`'s validation checks execute exactly once per call, not once per
  known config key.
- Every currently-`ERROR`ing test in `tests/eventbus/test_eventbus_auth.py`, `tests/
  eventbus/test_eventbus_subscribe.py`, and `tests/eventbus/test_eventbus_config.py`
  passes.
- `TestPublishAuth`'s per-role-token test cases in `test_eventbus_auth.py` actually
  exercise a `publisher_token`-authenticated request, not `None`.

## Testing Expectations
Run `tests/eventbus/test_eventbus_auth.py`, `tests/eventbus/test_eventbus_config.py`,
and `tests/eventbus/test_eventbus_subscribe.py` in full; confirm no new failures
elsewhere in `tests/eventbus/`.

## Documentation Impact
N/A: internal config-validation and test-fixture fix; no operational config schema
change is implied (the per-role token fields already exist in `EventBusConfig`).

## Out of Scope
- The `/events/{event_id}/ack` routing 403 issue (tracked separately).
- The `_dlq_loop` shutdown/segfault issue (tracked separately).
- The `/nack` endpoint's `consumer_id` dependency-injection issue (tracked separately).

## Dependencies
N/A: none

## Unresolved Questions
- Whether `EventBusConfig.__post_init__` should enforce the per-role-token-required
  rule directly (making both construction paths consistent) is a design decision, not
  a discovered fact — recorded here as `Needs confirmation` rather than assumed.

## AI Implementation Instruction
Fix `scripts/eventbus/config.py`'s indentation first and confirm it does not change
existing passing-test behavior. Then decide the `__post_init__` question above
explicitly (state the decision and reasoning) before touching test fixtures. Update
only the files listed in Target Files or Areas — do not touch `scripts/eventbus/
auth.py`'s route-role mapping, `scripts/eventbus/app.py`'s `_dlq_loop`, or the `/nack`
endpoint's consumer_id handling; each has its own tracked issue.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-093422
- **Related target files**: scripts/eventbus/config.py, tests/eventbus/test_eventbus_auth.py, tests/eventbus/test_eventbus_config.py, tests/eventbus/test_eventbus_subscribe.py

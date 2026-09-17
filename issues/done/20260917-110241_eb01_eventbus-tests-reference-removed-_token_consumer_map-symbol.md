# eventbus tests reference removed `_TOKEN_CONSUMER_MAP` symbol

## Priority
High

## Summary
Four eventbus test files construct a `principal_client` fixture that imports
`_TOKEN_CONSUMER_MAP` from `eventbus.auth`, but that symbol no longer exists —
it fails with `ImportError: cannot import name '_TOKEN_CONSUMER_MAP' from
'eventbus.auth'`. Update the fixtures to use the current Principal-based API
so the affected tests can run again.

## Background
Commit `c85362a36` ("refactor(eventbus): replace split token maps with
Principal dataclass") removed the module-level `_TOKEN_CONSUMER_MAP` dict from
`scripts/eventbus/auth.py` as part of migrating consumer-ID ownership onto the
`Principal` dataclass. The four eventbus test files below were not updated to
match and still import the removed symbol directly.

## Problem
`principal_client` fixture setup in each affected file does:
```
from eventbus.auth import _TOKEN_CONSUMER_MAP
_TOKEN_CONSUMER_MAP["consumer-token"] = {"consumer-A"}
```
This raises `ImportError` at fixture-setup time, so every test depending on
`principal_client` in these files errors out before running (13 tests total).

## Reason for Change
These are pre-existing (as of this issue) test errors uncovered while
syncing to `origin/master` via the `git-commit-and-sync` skill; a full
`uv run pytest tests/` run showed all 13 as `ERROR` at setup. They currently
mask whatever coverage `principal_client`-based tests were meant to provide
for consumer-identity/ownership authorization, so they should be restored to
running order.

## Implementation Intent
Update each fixture to grant `consumer-A` ownership of `"consumer-token"`
through whatever mechanism `Principal`/`_populate_token_maps` (or equivalent
current API in `scripts/eventbus/auth.py`) now exposes for per-token
`allowed_consumer_ids`, instead of mutating a module-level dict that no
longer exists. Follow the same pattern already used successfully elsewhere
in the codebase for constructing a `Principal` with a restricted
`allowed_consumer_ids` set (see `scripts/eventbus/auth.py`'s `Principal`
dataclass and `_populate_token_maps`/`_TOKEN_PRINCIPAL_MAP` for the current
shape). Do not reintroduce the old split-token-map structure.

## Target Files or Areas
- `tests/eventbus/test_eventbus_ack_nack.py` (`principal_client` fixture)
- `tests/eventbus/test_eventbus_crash_ack.py` (`principal_client` fixture)
- `tests/eventbus/test_eventbus_subscribe.py` (`principal_client` fixture)
- `tests/eventbus/test_eventbus_ack_endpoint.py` (`principal_client` fixture)
- `scripts/eventbus/auth.py` (read-only reference for the current Principal API — not expected to change)

## Required Changes
- In each of the four test files, replace the `from eventbus.auth import
  _TOKEN_CONSUMER_MAP` / `_TOKEN_CONSUMER_MAP["consumer-token"] = {"consumer-A"}`
  lines with the current API's equivalent way of restricting the
  `consumer-token` principal's `allowed_consumer_ids` to `{"consumer-A"}`.
- Re-run each affected test to confirm the fixture no longer raises
  `ImportError` and the test's actual assertions pass or fail on their own
  merits (a passing fixture does not guarantee the test body itself is
  correct against the current API — see Acceptance Criteria).

## Constraints
N/A: none beyond preserving the existing fixture's intent (consumer-token
principal owns only consumer-A)

## Acceptance Criteria
- [ ] `uv run pytest tests/eventbus/test_eventbus_ack_nack.py::TestNackEvent -v` — no `ERROR` outcomes
- [ ] `uv run pytest tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck -v` — no `ERROR` outcomes
- [ ] `uv run pytest tests/eventbus/test_eventbus_subscribe.py::TestSubscribePrincipalValidation -v` — no `ERROR` outcomes
- [ ] `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint -v` — no `ERROR` outcomes
- [ ] Each previously-`ERROR`ing test now either passes, or fails with a
  test-body assertion failure that is filed as its own follow-up (not another
  `ImportError`)

## Testing Expectations
Run the four targeted test files listed above, plus
`uv run pytest tests/eventbus/ -q` to confirm no new failures were introduced
elsewhere in the eventbus suite. `uv run mypy scripts/` and
`uv run mypy tests/` are not expected to be affected but should stay green.

## Documentation Impact
N/A: this is a test-fixture-only fix; no `docs/` content describes
`_TOKEN_CONSUMER_MAP` or references it as public API.

## Out of Scope
- Do not modify `scripts/eventbus/auth.py`'s Principal/token-map
  implementation — the removal in `c85362a36` is treated as intentional.
- Do not investigate or fix the 14 unrelated failures in
  `tests/eventbus/test_eventbus_auth.py` (filed separately).
- Do not investigate or fix `test_partial_ack_replay` or the concurrent/DLQ
  test failures (filed separately).

## Dependencies
N/A: none

## Unresolved Questions
- What is the exact current mechanism for restricting a token's
  `allowed_consumer_ids` after `_populate_token_maps(cfg)` has already run —
  is there a supported way to do this outside of constructing the
  `EventBusConfig`/token map from scratch with the restriction baked in?
  Needs confirmation against the current `scripts/eventbus/auth.py` API
  before implementation.

## AI Implementation Instruction
Read `scripts/eventbus/auth.py` in full before touching any test file to
confirm the current supported way to scope a token's `allowed_consumer_ids`.
Change only the four fixtures' setup lines identified above — do not touch
test bodies, assertions, or unrelated fixtures in the same files. If a test's
assertions still fail once the fixture no longer errors, stop and report it
rather than adjusting the assertion to match incidental current behavior.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260917-110241
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py, tests/eventbus/test_eventbus_crash_ack.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_ack_endpoint.py, scripts/eventbus/auth.py

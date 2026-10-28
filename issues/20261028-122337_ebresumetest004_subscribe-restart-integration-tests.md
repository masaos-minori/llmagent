# Add restart and resume integration coverage through the real subscribe endpoint

## Priority
Medium

## Summary
Add integration tests that resume a consumer through `/subscribe` after a full application restart (shutdown, then startup on the same SQLite file), and rename or retire the tests that claim endpoint coverage while executing SQL directly or skipping.

## Background
Source: `memo-issue.md` item 05, re-verified against current source on 2026-10-28. The memo's file paths are stale; the files are under `tests/eventbus/`.

- `tests/eventbus/test_eventbus_restart_resume.py` runs every test inside one `TestClient` lifecycle (the `client` fixture holds one `with TestClient(eb_app.app)` and one database connection). No test closes the first lifecycle and reopens the database in a second one. `Explicit in code`.
- The restart class `TestOutOfOrderAckNoSkipOnReconnect` and `test_get_resume_position_no_offset` open the database and call `ack_event_for_consumer`, `get_consumer_offset` and `get_resume_position` directly, so they do not cross `/subscribe`. `Explicit in code`.
- `test_reconnect_after_ordered_acks_replays_next_event_first` and `test_reconnect_after_out_of_order_ack_replays_lowest_unacked_first` do use `/subscribe` through `_reconnect_ids()`, which sets `sse_idle_timeout` to 0.5 s so the stream ends deterministically; both stay within one lifecycle. `Explicit in code`.
- `test_resume_from_sqlite_offset` is skipped with a reason that cites the issue `ebsse01` by its old path under `issues/`; that issue is archived as `issues/done/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md`. Whether the skip is still needed is `Needs confirmation`.
- `tests/eventbus/test_eventbus_replay_subscribe.py::test_subscribe_yields_matching_event` runs a SQL query and `_row_to_dict()` directly; its docstring says so, but its name claims subscribe behavior. `Explicit in code`.
- `tests/eventbus/test_eventbus_startup.py` reopens a canonical database only to check the schema gate, not subscribe or resume behavior. `Explicit in code`.

## Problem
At-least-once resume after a process restart is not verified end to end: no test proves that a second lifecycle (new connection, new broker, cleared shutdown state) resumes the same consumer from the persisted position through the public endpoint.

## Reason for Change
Resume correctness depends on the offset, delivery and replay path across a restart, which is the scenario production restarts exercise. Single-lifecycle tests can pass while a stale connection, broker or shutdown flag breaks the second start. No incident is cited; severity is Medium (testability of a core delivery guarantee).

## Implementation Intent
Use the production lifespan for both lifecycles and drive `/subscribe` with the existing finite harness (`sse_idle_timeout`), so assertions come from real SSE output. Keep the direct-query tests as clearly named unit tests. Reuse the fixture and helper patterns already in the file.

## Target Files or Areas
- `tests/eventbus/test_eventbus_restart_resume.py`
- `tests/eventbus/test_eventbus_replay_subscribe.py`
- `tests/eventbus/conftest.py` or `tests/eventbus/eventbus_helpers.py` for a shared two-lifecycle fixture
- `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py` (read-only reference unless a defect is found)

## Required Changes
- Add a fixture or helper that starts the app lifespan, yields a client, shuts it down, and starts a second lifespan on the same database path.
- Add integration tests: the same consumer resumes after restart; a different consumer starts from the beginning; an out-of-order ACK does not skip the lowest unacknowledged event; an ordered ACK fast-forwards; topic filtering and consumer authorization hold through the endpoint; a duplicate active consumer id is rejected; a client disconnect removes the subscriber.
- Assert that no broker, connection, shutdown flag or queue state leaks across lifecycles.
- Rename `test_subscribe_yields_matching_event` (and any direct-SQL test) so the name says it tests the query and row conversion.
- Remove or replace the skipped `test_resume_from_sqlite_offset` once the new tests cover it, or document why the skip must stay.

## Constraints
- Use explicit synchronization or the idle timeout; no sleeps.
- Tests must not write production paths (`tests/conftest.py` isolation applies).
- Do not change production behavior unless a test exposes a defect; report it instead.

## Acceptance Criteria
- At least one test crosses two complete production lifecycles on the same database file and asserts resume position from real `/subscribe` output.
- The second lifecycle uses a new connection and broker.
- Direct-query tests are named as unit tests; no skipped test remains without a documented current reason.
- The new tests terminate deterministically.

## Testing Expectations
- The new integration tests, run alone and with `uv run pytest tests/eventbus`.
- Run the new tests twice in one session to confirm no state leaks (flag, principal map, metrics registry).
- ruff on the changed files; mypy on `tests/eventbus` (it is in the mypy `files` scope).

## Documentation Impact
Not required.

## Out of Scope
- Changes to resume or replay behavior.
- A general SSE client library for tests.
- Authorization model changes (covered by other work).

## Dependencies
- Coordinate with the archived `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md`: its pending procedure `implementations/20261028-115236_04_tests_eventbus_test_eventbus_shutdown.py.md` adds a second-lifecycle test and clears `app.state.db` after shutdown; a second lifecycle in this issue depends on that behavior being settled. Implement after it, or rebase.
- Related and already archived: `issues/done/20260911-135626_ebsse01_subscribe-generator-never-detects-client-disconnect.md` (the reason cited by the skipped test).

## Unresolved Questions
- Is the skip on `test_resume_from_sqlite_offset` still required now that `ebsse01` is archived and `_reconnect_ids()` ends the stream by idle timeout? `Needs confirmation`.
- Does a second `with TestClient(eb_app.app)` on the same database leak the module-level `_shutting_down` flag or metrics registry today? `Needs confirmation`.

## AI Implementation Instruction
Write tests only; do not edit production code. Reuse `_reconnect_ids()` and the fixtures in the file. If a second lifecycle exposes a production defect, stop and report it with the failing test instead of patching around it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261028-122337
- **Related target files**: `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_replay_subscribe.py`, `tests/eventbus/conftest.py`, `tests/eventbus/eventbus_helpers.py`, `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`

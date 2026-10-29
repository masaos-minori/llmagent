# Run EventBus test fixtures through the production lifespan and shutdown path

## Priority
Medium

## Summary
Make the EventBus test fixtures that build application state by hand use the production lifespan for startup and the shared `_shutdown_lifespan()` sequence for teardown, starting with the health fixture, which currently initializes state twice. Record the correct helper names so the related plan is re-verified before it is implemented.

## Background
Source: `memo-issue.md` item 06 (test lifecycle), re-verified against current source on 2026-10-29. The same concern was filed as the archived `issues/done/20261028-122523_ebtestdrift007_test-lifecycle-terminology.md` and converted into `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`. That plan narrowed the lifecycle part to the restart-resume schema copy and a `make_test_client` helper, and its premises do not hold in the repository:
- The plan states that `test_eventbus_health.py` does not bypass the lifespan fixture. It does: its `client` fixture calls `_init_state()` and then enters `with TestClient(eb_app.app)`, so state is initialized by hand and again by the production lifespan (`Explicit in code`).
- The plan names `make_event_bus_ctx`, `open_consumer_db` and `subscribe_client` as existing helpers. A search of the repository outside `plans/`, `issues/` and `implementations/` finds none of them, and `git log -S` finds them only in the commit that added the plan (`Explicit in code`). The real shared helper is `make_eventbus_client()` in `tests/eventbus/eventbus_helpers.py`. The earlier ebdlqunique007 plan was superseded for the same reason (`plans/done/20261028-094441_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md`).

Current behavior (`Explicit in code`):
- `lifespan()` in `scripts/eventbus/app.py` clears the shutdown flag, loads the config, opens the database, populates the token maps, creates the broker and starts the DLQ sweep task. `_shutdown_lifespan()` sets the shutdown flag, stops the sweep, shuts the broker down, and closes the connection under the database lock. Its docstring says the tests exercise the same sequence; only `tests/eventbus/test_eventbus_shutdown.py` calls it.
- In `test_eventbus_health.py`, `_init_state()` opens a database connection and a broker on a throwaway event loop, then the lifespan opens and assigns a second pair. The first connection and broker are not closed. After the `with` block, the lifespan has already set `app.state.db` to `None`, so the fixture's own `_do_cleanup()` has nothing left to close.
- `make_eventbus_client()` and its `_init_state()` / `_do_cleanup()` in `tests/eventbus/eventbus_helpers.py` build the state by hand, create `TestClient(eb_app.app)` without entering it (so the lifespan does not run), and tear down with a hand-written sequence that omits the shutdown flag and the database-lock handshake. It is used by several test files, among them `test_eventbus_publish.py`, `test_eventbus_crash_ack.py`, `test_eventbus_slow_consumer.py` and `test_admin_topics_authorization.py`.

## Problem
Tests built on these fixtures run against a lifecycle the production service never creates: no DLQ sweep task, no shutdown-flag reset, a different teardown order, and, in the health fixture, an orphaned first connection and broker. A lifecycle regression in `lifespan()` or `_shutdown_lifespan()` is not seen by those tests, and the health fixture's cleanup is dead code.

## Reason for Change
The lifecycle fixes in `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` made the shutdown sequence the single supported teardown, and the fixtures should exercise it. The related plan will fail its own verification because of the missing helpers, so the premise needs correcting before an implementation procedure is generated from it. No incident is cited; not time-sensitive.

## Implementation Intent
Use the production lifecycle as the contract and keep fixture code thin:
- Health fixture: remove the manual state initialization and the hand-written cleanup, enter `TestClient` as a context manager, and let the lifespan start and stop the application.
- Shared helper: provide one lifecycle-based fixture (start through the lifespan, stop through the context exit, which runs `_shutdown_lifespan()`) and migrate `make_eventbus_client()` callers to it in small steps, or keep `make_eventbus_client()` only where a test genuinely needs to mutate `app.state` before startup, documenting that reason.
- Reuse the two-lifecycle fixture that `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md` adds, instead of creating a competing one.

## Target Files or Areas
- `tests/eventbus/test_eventbus_health.py` (`client` fixture, `_init_state`, `_do_cleanup`)
- `tests/eventbus/eventbus_helpers.py` (`make_eventbus_client`, `_init_state`, `_do_cleanup`)
- Callers of `make_eventbus_client()` under `tests/eventbus/`, migrated incrementally
- `tests/eventbus/conftest.py` (autouse resets must stay valid; read, change only if a reset becomes redundant)

## Required Changes
- Rewrite the health fixture to rely on the lifespan only, with no manual `app.state` initialization and no custom cleanup.
- Introduce a lifecycle-based fixture or helper in `tests/eventbus/eventbus_helpers.py` and migrate `make_eventbus_client()` callers whose tests do not need pre-startup state mutation.
- For callers that keep `make_eventbus_client()`, make its teardown use `_shutdown_lifespan()` instead of a separate sequence, or record why that is not possible.
- Add a test that two sequential lifecycles in one process work, that a closed connection is never reused, and that shutdown state is cleared on the next startup.
- Measure the blast radius before migrating (see Constraints) and record it in the change description.

## Constraints
- No production code changes; `lifespan()` and `_shutdown_lifespan()` are the reference behavior.
- Existing test assertions keep their meaning; only fixture construction and teardown change.
- Before changing a widely used helper, count references: `rg -l 'make_eventbus_client' tests/` and `rg -c 'make_eventbus_client' tests/` (see `rules/toolchain.md` Impact-radius check). Migrate in separate commits per test file group if the count is large.
- Tests that patch `load_config`, `get_schema_path` or `app.state` before startup must keep working; the health fixture already patches `load_config` and `get_schema_path`.

## Acceptance Criteria
- `test_eventbus_health.py` has no `_init_state` or `_do_cleanup`, and its fixture opens exactly one connection and one broker per test.
- Fixtures migrated by this issue start through the lifespan and stop through the context exit, with no hand-written teardown sequence.
- A test shows two sequential lifecycles succeed, the second one opens a new connection, and the shutdown flag does not leak.
- `uv run pytest tests/eventbus` passes with no assertion changes in migrated tests.
- `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md` has been re-verified against the real helper names, or its owner has recorded the correction.

## Testing Expectations
- New lifecycle test as described above; full `uv run pytest tests/eventbus` after each migration step.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus` passes (`tests/eventbus` must be clean).
- `uv run ruff check tests/eventbus` and `uv run ruff format --check tests/eventbus` pass.

## Documentation Impact
No `docs/` change is required by the migration itself. If `docs/24_eventbus/eventbus_08_reference_api.md` lists test fixture names, it must match the real helper names; this is also tracked by the related plan.

## Out of Scope
- Removing the private schema copy and the `make_test_client` helper (`plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`).
- The two-lifecycle `/subscribe` restart scenarios (`plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`).
- Requirement-identifier cleanup (`issues/20261029-090453_eventbus004_test-requirement-id-cleanup.md`).
- Any change to `scripts/eventbus/`.

## Dependencies
- Coordinate with `plans/20261028-234121_ebresumetest004_subscribe-restart-integration-tests.md`: it adds the two-lifecycle fixture to `tests/eventbus/eventbus_helpers.py` first; this issue should reuse it and land after it.
- Coordinate with `plans/20261028-234655_ebtestdrift007_test-lifecycle-terminology.md`: it edits `tests/eventbus/eventbus_helpers.py` and restart-resume fixtures and references helpers that do not exist. Its premises must be re-verified before an implementation procedure is generated from it.
- Related, archived: `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (settled shutdown sequence).

## Unresolved Questions
- `Needs confirmation`: whether any test relies on `make_eventbus_client()` not running the lifespan, for example to avoid starting the DLQ sweep task. This decides how many callers can migrate; check each caller before migrating.
- `Needs confirmation`: how `make_eventbus_client()` populates the token map. Confirm it matches what `lifespan()` does through `_populate_token_maps()`, so the migrated tests do not change authorization behavior.
- `Needs confirmation`: whether the ebtestdrift007 plan's owner wants this issue merged into that plan after the plan is corrected.

## AI Implementation Instruction
- Change only test fixtures and helpers under `tests/eventbus/`; do not touch `scripts/`.
- Migrate callers in small steps and run `uv run pytest tests/eventbus` after each; stop and report if a test needs pre-startup state that the lifespan would overwrite.
- Do not invent helper names; use `make_eventbus_client` and the helpers that exist in `tests/eventbus/eventbus_helpers.py`.
- Do not rename identifiers or edit comments beyond what a fixture change requires.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-090402
- **Related target files**: `tests/eventbus/test_eventbus_health.py`, `tests/eventbus/eventbus_helpers.py`, `tests/eventbus/conftest.py`

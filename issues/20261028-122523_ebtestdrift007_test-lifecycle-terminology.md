# Clean up EventBus test lifecycle fixtures, the stale schema fallback and terminology

## Priority
Low

## Summary
Remove the remaining drift in EventBus tests: fixtures that initialize application state by hand instead of running the production lifespan, an inline fallback schema that no longer matches `schema.sql`, a misspelled DLQ acronym in test names, and requirement identifiers in comments that no longer point at a visible definition.

## Background
Source: `memo-issue.md` item 06 (test and terminology part), re-verified against current source on 2026-10-28. The audit-record and `published_at` parts of that item are filed separately (`issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`, `issues/20261028-122454_ebpubat006_published-at-ownership.md`).

- `tests/eventbus/test_eventbus_health.py` defines `_init_state(cfg)`, which assigns `app.state.config`, `app.state.db`, the envelope schema and a new broker by hand; `tests/eventbus/test_admin_topics_authorization.py` assigns `app.state.db` the same way and closes it in its own teardown. Whether `TestClient`'s lifespan then runs on top of that state is `Needs confirmation`. `Explicit in code`.
- `tests/eventbus/test_eventbus_restart_resume.py::_create_tables` falls back, when `schema.sql` is not found, to an inline `CREATE TABLE` whose `events` table has `acked` and `consumer_delivery_failure_count` columns that the canonical `scripts/eventbus/schema.sql` no longer defines (per-consumer state moved to `consumer_delivery`). `Explicit in code`.
- `tests/eventbus/test_eventbus_requeue_edge_cases.py` names tests `test_requeue_non_dmq_event` and `test_requeue_valid_dmq_event`; the term is DLQ. `Explicit in code`.
- Requirement identifiers such as `REQ-004`, `UNK-01`, `AC-3` and `H-03` appear in comments and docstrings across `tests/eventbus` (the highest counts are in `test_eventbus_config.py`, `test_eventbus_auth.py` and `test_eventbus_dlq.py`); whether each resolves to a visible, current definition is `Needs confirmation` (`H-03` is the deferred health integrity placeholder; its plan decision is recorded in the archived `plans/done/20261028-094217_ebmetrics006_correct-db-timing-health.md`).

## Problem
Tests can pass against a state the production lifespan would never create, a fallback schema can mask a missing `schema.sql`, and stale identifiers and a misspelled acronym make the tests harder to read and search.

## Reason for Change
Maintenance and readability only; no behavior is wrong today. The fallback schema is the one item with a correctness angle (it hides a missing canonical file). Nothing is time-sensitive, so the priority is Low.

## Implementation Intent
Use the production lifespan in fixtures, fail clearly when `schema.sql` is missing, rename the misspelled tests without changing behavior, and keep only requirement identifiers that resolve to a canonical, current definition. Describe current behavior in comments, not history.

## Target Files or Areas
- `tests/eventbus/test_eventbus_health.py`
- `tests/eventbus/test_admin_topics_authorization.py`
- `tests/eventbus/test_eventbus_restart_resume.py`
- `tests/eventbus/test_eventbus_requeue_edge_cases.py`
- `tests/eventbus/conftest.py` (a shared lifecycle fixture, if added)
- other `tests/eventbus` files that carry stale identifiers

## Required Changes
- Replace hand-built app state with fixtures that run the production lifespan startup and shutdown once per lifecycle; reset global shutdown flags, principal maps and the metrics registry between tests.
- Delete the inline fallback schema and fail with a clear message when `schema.sql` is unavailable.
- Rename the two `dmq` tests to `dlq`.
- For each retained `REQ-*`, `UNK-*`, `AC-*` or `H-03` identifier, map it to a canonical specification (ADR invariant or doc section) or remove it; delete superseded history comments in the touched files.

## Constraints
- Renames and comment edits must not change test behavior.
- Do not touch production code.
- Keep each touched file's tests passing; do not skip or loosen a test to remove a fixture.

## Acceptance Criteria
- Health and admin tests use the production lifespan fixture; two sequential `TestClient` lifecycles work in one process.
- No fallback schema exists in `tests/eventbus`.
- No `dmq` remains in `tests/eventbus`.
- Every remaining requirement identifier in the touched files resolves to a visible definition.

## Testing Expectations
- `uv run pytest tests/eventbus` before and after with the same pass count (renames do not change collection counts except names).
- Run the touched files twice in one session to confirm no state leaks.
- ruff on changed files; mypy on `tests/eventbus`.

## Documentation Impact
Not required (identifier mapping may add a pointer in an ADR Implementation Notes section only if one is missing).

## Out of Scope
- Privileged audit records and the `published_at` contract (separate issues).
- New test coverage (restart/resume is filed separately).
- Production code and schema changes.

## Dependencies
- Overlaps in target files with pending procedures of archived Plans: `implementations/20261028-120038_07_tests_eventbus_test_eventbus_health.py.md` (ebmetrics006, health tests), `implementations/20261028-114911_11_tests_eventbus_test_admin_topics_authorization.py.md` (ebauth001) and `implementations/20261028-120147_03_tests_eventbus_test_eventbus_requeue_edge_cases.py.md` (ebdlqunique007, the file with the `dmq` names). Implement after them or rebase.
- Related: `issues/20261028-122337_ebresumetest004_subscribe-restart-integration-tests.md` edits `tests/eventbus/test_eventbus_restart_resume.py` and may add the shared two-lifecycle fixture; implement this issue's fixture work after it, or fold into the same fixture.

## Unresolved Questions
- Does the lifespan run on top of the hand-built state today? `Needs confirmation`.
- Where should a retained requirement identifier be defined (ADR invariant or doc)? `Needs confirmation` per identifier.

## AI Implementation Instruction
Keep changes to fixtures, names and comments; do not change assertions or production code. If removing a hand-built state makes a test fail, stop and report the failing test rather than editing its expectation.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261028-122523
- **Related target files**: `tests/eventbus/test_eventbus_health.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_restart_resume.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/conftest.py`

# Decide whether to remove or redefine the event-level failure counters

## Priority
High

## Summary
Decide whether the event-level counters `delivery_failure_count` and `cycle_failure_count` are removed or kept as documented diagnostics, and align the NACK response, the DLQ listing, redelivery, the schema, the constants, and the documentation with that decision.

## Background
`memo-issue.md` item H-03 observed that the per-consumer counter `consumer_delivery_failure_count` is the only counter that gates DLQ promotion, while the event-level counters are still stored, returned, and copied. Confirmed against current source:
- `scripts/eventbus/delivery_repo.py` documents both event-level counters as "legacy values" that NACK does not modify under the per-consumer model; `nack_event()` nevertheless returns them in `NackResult`, using the sentinels `-1` (event not found) and `-2` (idempotent repeat NACK, in the `cycle_failure_count` slot).
- `scripts/eventbus/ack_route.py` returns `delivery_failure_count` in the `POST /nack` response, which is the unchanged event-level value.
- `scripts/eventbus/dlq.py` lists `delivery_failure_count` in `GET /dlq` items and in inline promotion logging.
- `scripts/eventbus/dlq_repo.py` copies `delivery_failure_count` and resets `cycle_failure_count` to `0` on redelivery.
- `scripts/eventbus/schema.sql` defines both columns and `scripts/eventbus/_constants.py` exposes their names.
- Documentation (`eventbus_04`, `eventbus_05`, `eventbus_12`) describes them as legacy or events-level values.
- No module outside `scripts/eventbus/` and no test outside `tests/eventbus/` (plus one schema test) references them. External API consumers are unknown.

## Problem
The API and the database keep fields that no longer carry the failure count callers would expect: the NACK response reports an event-level value that NACK never changes, and the result type overloads integers as status sentinels. A caller can read the wrong counter or misread a sentinel.

## Reason for Change
The authoritative counter is per-consumer, so keeping a differently named, unmodified field in the response invites misuse and keeps redelivery copy/reset logic alive for no behavioral reason.

## Implementation Intent
Choose one contract and apply it everywhere.
- Option A: remove both counters from the NACK response, `NackResult`, the DLQ listing, redelivery, the schema (through a controlled change), the constants, tests, and documentation, with a client notice if any external client reads them.
- Option B: keep them and define their meaning, updater, and behavior across redelivery cycles, remove the "legacy" wording only after that contract is approved, and still replace the overloaded sentinels with an explicit status.
Prefer the option that leaves one authoritative counter in the public responses, unless an external consumer needs the event-level fields.

## Target Files or Areas
- `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `scripts/eventbus/event_repo.py`
- `scripts/eventbus/schema.sql`, `scripts/eventbus/_constants.py`
- `tests/eventbus/` tests for NACK, DLQ, requeue, pagination, restart resume, concurrency, and authorization; `tests/db/test_create_schema.py`
- `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, `eventbus_05_dlq_offsets_and_delivery_semantics.md`, `eventbus_07_configuration-and-operations.md`, `eventbus_12_ack_nack_endpoints.md`

## Required Changes
- Record the Remove or Retain decision for each counter and the compatibility impact.
- Apply the decision across the response schemas, result type, redelivery, schema, constants, tests, and documentation.
- Replace the `-1` / `-2` sentinels by explicit status values where the decision keeps the result type, and keep idempotent NACK unambiguous.
- If removing, provide the removal version and client migration guidance.

## Constraints
- DLQ promotion must keep using `consumer_delivery_failure_count`; promotion behavior must not change.
- A schema column removal needs a migration path for the existing database or an explicit recreate decision (the supported baseline is the current schema).
- ADR text is not edited without the owner's decision.

## Acceptance Criteria
- Every internal reference to both counters is accounted for (removed, or retained with a stated design rationale).
- The NACK response, DLQ listing, redelivery, schema, constants, tests, and documentation agree.
- Idempotent NACK and not-found results are unambiguous and tested.
- The full suite, `ruff`, `mypy --no-namespace-packages`, `lint-imports`, and the documentation checkers pass.

## Testing Expectations
- Update and extend the NACK, DLQ promotion, requeue, and pagination tests; run `tests/eventbus` and the full suite once.
- `uv run python tools/check_db_separation.py` and the generated-reference check.

## Documentation Impact
Yes. The ACK/NACK endpoint, DLQ endpoint, and delivery-semantics documents must describe the final counters and status values only, without a history of the change.

## Out of Scope
- Offset handling, DLQ lineage redesign, and unrelated schema work.

## Dependencies
- The EventBus schema-migration removal plan (`plans/done/20261022-093935_plan.md`, procedures under `implementations/`) edits `scripts/eventbus/schema.py` and `scripts/db/` files; apply in order and re-read the files first.
- Sibling-issue check: no open issue under `issues/` and no active plan under `plans/` touches these files.

## Unresolved Questions
- Does any consumer outside this repository read `delivery_failure_count` or `cycle_failure_count` from `POST /nack` or `GET /dlq`? Unknown.
- Should the public API compatibility policy for the EventBus be written down first? None exists in the repository.

## AI Implementation Instruction
Do not change the DLQ promotion rule. Obtain the owner's Remove or Retain decision first; stop and report if it is missing. Change only the files listed and keep the response change visible in the documentation.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261022-124142
- **Related target files**: scripts/eventbus/delivery_repo.py, scripts/eventbus/ack_route.py, scripts/eventbus/dlq.py, scripts/eventbus/dlq_repo.py, scripts/eventbus/event_repo.py, scripts/eventbus/schema.sql, scripts/eventbus/_constants.py, docs/24_eventbus/eventbus_04_dlq_endpoint.md, docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md, docs/24_eventbus/eventbus_07_configuration-and-operations.md, docs/24_eventbus/eventbus_12_ack_nack_endpoints.md

# Define the durability contract for EventBus publish, NACK and DLQ promotion

## Priority
Medium

## Summary
Document and, where needed, implement one explicit durability model for publish (SQLite, JSONL, live broker notification) and for NACK/DLQ promotion (SQLite state and DLQ file), including how partial completion is detected and repaired.

## Background
Source: `memo-issue.md` Issue 03, re-verified in part against current source on 2026-10-27. The memo rated it High; because several of its failure states self-heal or are only metered, Medium is assigned (Phase 7 tie-breaking).

- `publish()` in `scripts/eventbus/publish_route.py` commits the event to SQLite under the DB lock, then appends to `events.jsonl` and notifies the in-memory broker. A JSONL `OSError` increments `eventbus_jsonl_append_failure_total` and is logged; a broker exception increments `eventbus_broker_notify_failure_total`. In both cases the response still reports success with `event_id` and `seq`. `Explicit in code`.
- DLQ promotion in `scripts/eventbus/dlq.py` writes the record with `_atomic_write` and then runs `UPDATE events SET dlq_at ... WHERE dlq_at IS NULL` and `db.commit()`. A write failure increments `eventbus_dlq_file_write_failure_total` and leaves the row live; a failure of the UPDATE/commit after the file exists is not covered by a documented recovery. `Explicit in code` for the order; recovery behavior is `Needs confirmation`.
- The NACK route in `scripts/eventbus/ack_route.py` performs NACK recording and `is_promotable`/`promote_single` inside one `run_with_db_lock` call, but `nack_event()` in `scripts/eventbus/delivery_repo.py` commits before promotion starts. `Explicit in code` for the commit; whether a failed promotion is retried by the background sweep is `Needs confirmation`.
- Prior work: `issues/done/20260907-125042_eb_m02_duplicate_publish_jsonl_reconciliation.md` handled duplicate-publish JSONL behavior only.

## Problem
Each of these sequences can leave partially completed state: committed NACK with failed promotion, a DLQ file without `dlq_at`, a committed event missing from JSONL, or a committed event never delivered to connected subscribers. The authoritative record, recovery path and client-visible guarantee are not defined together in one place.

## Reason for Change
Operators and ADR-006 readers cannot tell which store is authoritative or what a successful publish guarantees. No incident is cited; the risk is an undefined contract plus metrics-only signalling.

## Implementation Intent
First decide and record, per operation, which store is authoritative (SQLite versus JSONL versus DLQ file) and what publish success guarantees. Then change code only where the decision requires it: for example, repository-level NACK-plus-promotion as one transition, or a reconciliation step for a DLQ file without `dlq_at`. Prefer idempotent repair (the existing `dlq_at IS NULL` guard and atomic rename already help) over new mechanisms.

## Target Files or Areas
- `scripts/eventbus/publish_route.py`, `scripts/eventbus/event_repo.py`
- `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`
- `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py` (DLQ sweep)
- `tests/eventbus/`
- ADR-006 (`docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`) and EventBus operations docs under `docs/24_eventbus/`

## Required Changes
- Record the authority model: SQLite versus DLQ file for dead letters; SQLite versus JSONL for published events; whether loss of live notification after a successful publish is acceptable.
- Decide whether NACK recording, promotability check and promotion form one transaction, and implement it if yes.
- Define and implement (or document as accepted) recovery for: DLQ file written but `dlq_at` not committed; NACK committed but promotion failed; JSONL append failed after commit.
- Define the interaction of inline promotion and the background sweep so promotion is neither duplicated nor lost.
- Surface partial post-commit failures through the existing metrics with documented operator action.

## Constraints
- Preserve the current publish response contract unless the decision explicitly changes it.
- Do not change ADR Decisions or Invariants without owner approval; ADR edits must pass `tools/check_adr_preservation.py`.
- Keep the DLQ file format stable.

## Acceptance Criteria
- Each failure point listed in Required Changes has a documented resulting state and a test that demonstrates it.
- SQLite and DLQ artifacts cannot silently disagree without a repair path.
- The publish guarantee is stated once and matches the code and tests.

## Testing Expectations
- Fault-injection tests for: NACK update failure, DLQ file write failure, DB failure after DLQ file creation, JSONL failure after commit, broker failure after commit, concurrent inline promotion and sweep.
- Idempotency test for a duplicate publish after partial completion.
- `uv run pytest tests/eventbus -q`, mypy, ruff.

## Documentation Impact
Yes. Record in ADR-006 and the operations docs: the authority per store, the publish guarantee, failure behavior and operator actions for the post-commit failure metrics. Current behavior only.

## Out of Scope
- Introducing an outbox or message queue unless the decision requires it.
- Changing retry limits or DLQ file location.
- Consumer-side delivery semantics (offsets, resume position).

## Dependencies
N/A: none open. Overlaps in target files with `plans/20261027-120858_ebcompat002_decide-eventbus-db-facade.md` (import migration only); coordinate ordering if both are implemented.

## Unresolved Questions
- Is loss of immediate live notification after a successful publish acceptable? `Needs confirmation` (owner decision).
- Is JSONL required for audit or recovery, or best-effort only? `Needs confirmation`.
- Does the background sweep re-promote an event whose NACK committed but whose inline promotion failed? `Needs confirmation`: read `dlq.py` sweep and `is_promotable`.
- Whether `nack_event()` commit and promotion are in separate transactions in all paths: `Needs confirmation`.

## AI Implementation Instruction
Start with the decision record and tests; change code only where the decision requires it. Do not add infrastructure (outbox, queue) without an explicit owner decision. Stop and report the open questions above before implementing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-155846
- **Related target files**: `scripts/eventbus/publish_route.py`, `scripts/eventbus/event_repo.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/delivery_repo.py`, `scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, `tests/eventbus/`, `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md`, `docs/24_eventbus/`

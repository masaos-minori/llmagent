# Make duplicate publish handling content-safe and reconcile JSONL semantics

## Priority
Medium

## Summary
`scripts/eventbus/db.py`'s `insert_event()` uses `INSERT OR IGNORE` (line 180) with no
comparison of the existing row's topic/producer/payload/timestamp against the new request when
`event_id` already exists — confirmed by direct read, any duplicate `event_id` is treated as an
idempotent retry regardless of content. `scripts/eventbus/publish_route.py`'s `publish()`
appends to `events.jsonl` (lines 50-59) unconditionally, before checking whether `inserted` is
`True` — confirmed by direct read, the JSONL append happens outside the `if inserted:` block
(which only gates the broker-notify call at line 61), so a duplicate that SQLite ignores still
produces a new JSONL line.

## Background
Confirmed by direct read of `scripts/eventbus/db.py` lines 170-188 (`insert_event`) and
`scripts/eventbus/publish_route.py` lines 19-77 (`publish`): the JSONL write block (lines 50-59)
runs unconditionally after `_insert()` returns, and the `if inserted:` guard (line 61) applies
only to the subsequent broker-publish call. There is no test in
`tests/eventbus/test_eventbus_publish.py`/`test_eventbus_publish_contract.py` (file names
confirmed present under `tests/eventbus/`) that asserts JSONL line count matches SQLite row
count after a duplicate `event_id` is published with different content — this needs
confirmation by reading those files' actual assertions before considering it resolved.

## Problem
- A publisher that reuses an `event_id` with a different topic/payload/producer/timestamp
  receives the same HTTP 200 success response as the original publish (the response only
  echoes `event_id`/`seq`, per line 77) — SQLite retains the original content, but the caller
  cannot tell that its new content was silently discarded.
- Every publish attempt — including SQLite-ignored duplicates — appends a line to
  `events.jsonl`, so SQLite can contain one row for an `event_id` while `events.jsonl` contains
  multiple (potentially conflicting) records for the same ID, with no defined reconciliation
  rule for which JSONL line reflects the current SQLite state.

## Reason for Change
Provide strict idempotency. An identical retry should return the original sequence without a
new delivery, while a conflicting reuse of an event ID should be rejected. The role of JSONL
must be explicit so it can be reconciled with SQLite and not be mistaken for a second
inconsistent source of truth.

## Implementation Intent
Load and compare the existing event when an event ID already exists, using canonical equality
fields and canonical JSON comparison or content hashing (not raw string comparison, to avoid
false conflicts from reordered JSON keys — `scripts/eventbus/json_utils.py`'s `dumps()` already
sorts keys via `OPT_SORT_KEYS`, which should make this comparison straightforward to implement
consistently). Return idempotent success only for identical content; return HTTP 409 for
conflicting content without modifying stored data. Declare `events.jsonl`'s role explicitly
(replica, recovery artifact, or request audit) and change the append behavior in
`publish_route.py` to match that declared role.

## Target Files or Areas
- `scripts/eventbus/db.py`
- `scripts/eventbus/publish_route.py`
- `scripts/eventbus/json_utils.py`

## Required Changes
- Load and compare the existing event when an event ID already exists.
- Define canonical equality fields and canonical JSON comparison or content hashing.
- Return idempotent success only for identical content.
- Return HTTP 409 for conflicting content without modifying stored data.
- Declare `events.jsonl` to be either a replica, recovery artifact, or request audit.
- If it is a replica, append only newly inserted events (move the JSONL write inside the
  `if inserted:` block). If it is an audit, record an explicit inserted-or-duplicate outcome
  using a distinct record contract (do not conflate the two under the current single-shape
  line format).
- Add reconciliation and failure-injection tests.

## Constraints
- Keep unrelated behavior unchanged.
- Do not weaken fail-closed behavior, validation, or auditability.
- Do not mark this issue complete with documentation-only changes when runtime behavior is
  defective.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Identical retries (same `event_id` with matching canonical content) return the existing
      sequence and do not cause redelivery.
- [ ] Conflicting retries (same `event_id`, different content) return HTTP 409 and do not
      modify the stored row.
- [ ] Reordered JSON object keys in the payload do not create a false conflict.
- [ ] SQLite and JSONL can be reconciled deterministically according to the declared role of
      `events.jsonl`.
- [ ] A JSONL append failure does not misrepresent the SQLite commit outcome (existing
      try/except around the JSONL write at lines 50-59 already logs and continues on `OSError` —
      confirm this remains true after the change).

## Testing Expectations
Add tests for identical-content retry (200, same seq, no new JSONL line if replica-role is
chosen), conflicting-content retry (409, unchanged stored row), and reordered-key equality. Run
the complete EventBus test suite and the repository's linting, type checking, and documentation
consistency checks.

## Documentation Impact
Document `events.jsonl`'s declared role (replica/recovery-artifact/audit) and the idempotency
contract (identical-vs-conflicting duplicate handling) in the canonical EventBus persistence
specification.

## Out of Scope
- Transactional ACK/offset redesign, DLQ requeue redesign, and authentication (each tracked
  separately in this batch).
- Changing `insert_event()`'s `seq` allocation scheme (`AUTOINCREMENT` via `schema.sql`) beyond
  what's needed to support content comparison.

## Dependencies
N/A: none

## Unresolved Questions
Whether `events.jsonl`'s role should be replica, recovery artifact, or audit — this must be an
explicit decision recorded in the canonical specification before choosing the append/dedup
behavior; do not assume replica-role by default without confirming no other consumer depends on
the current append-every-attempt behavior.

## AI Implementation Instruction
Confirm no other code or operator tooling currently depends on `events.jsonl` containing one
line per publish *attempt* (including ignored duplicates) before changing the append condition
— check for readers of `events.jsonl` under `scripts/` before assuming replica-role is safe to
adopt.

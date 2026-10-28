## Goal
Correct the DLQ endpoint doc so the 409 for an already-redelivered event is described
as enforced by the database index, with the pre-insert check as a classification
path (REQ-006).

## Scope
- Edit `docs/24_eventbus/eventbus_04_dlq_endpoint.md` only: the requeue description
  sentence (line 43) and the `### Concurrency guarantee` paragraph (lines 54-56).
- Reference only: `scripts/eventbus/dlq_repo.py` (seq 02), `scripts/eventbus/schema.sql`
  (seq 01), `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` (link target,
  edited by seq 07).

## Assumptions
- Line 43 today reads: "The original row's `dlq_at` is intentionally left set so only
  one redelivery succeeds per original event (concurrency guard)." and the
  `### Concurrency guarantee` paragraph attributes enforcement to "the
  `redelivered_from` existence check in `redeliver_event()`" (verified this cycle,
  lines 43 and 54-56).
- The HTTP mapping (200/404/409) and response bodies documented around lines 45-52
  stay byte-identical; only the enforcement attribution changes.

## Design decisions
- Keep both places but re-attribute: the guarantee is a database constraint
  (`idx_events_redelivered_from` (new), a partial unique index on `events.redelivered_from`);
  the pre-insert `SELECT` stays documented as the fast path that classifies the
  sequential case without a failed insert; both paths return the same 409 result
  vocabulary, so no request/response contract text changes.
- Link the schema guarantee to the schema doc (`eventbus_06_persistence_schema_and_replay.md`)
  instead of duplicating the DDL text here.

## Alternatives considered
- Deleting the Concurrency guarantee paragraph: rejected — the observable guarantee
  (exactly one successful redelivery) is API-level behavior callers depend on; only
  its attribution is wrong.
- Naming the sqlite3 error text in this doc: rejected — error-message matching is an
  implementation detail owned by seq 02 and the schema doc.

## Implementation
### Target file
`docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Procedure
1. Line 43: replace "...so only one redelivery succeeds per original event
   (concurrency guard)." with "...so only one redelivery succeeds per original event;
   the database enforces this with the partial unique index `idx_events_redelivered_from` (new)
   on `events(redelivered_from)` (see [Persistence, Schema, and
   Replay](eventbus_06_persistence_schema_and_replay.md))."
2. `### Concurrency guarantee` (lines 54-56): replace the paragraph with:
   "Concurrent requeue attempts on the same event produce exactly one successful
   redelivery. The partial unique index `idx_events_redelivered_from` (new) enforces at
   most one descendant row per `redelivered_from` source, so a racing second request
   fails the insert and is reported as HTTP 409; the `redelivered_from` existence
   check in `redeliver_event()` classifies the already-redelivered case before the
   insert for sequential requests."
3. No other section changes.

### Method
Two prose edits; preserve heading levels and the Error Responses list verbatim.
English, per `skills/DESIGN.md`.

### Details
- The 409 wording in `### Error Responses` ("...or it was already requeued.") already
  covers both paths and needs no edit.

## Compatibility considerations
- Docs-only change; API contract text unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the two sentences.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain eventbus`.
- `uv run python tools/check_docs_structure.py`; `uv run python tools/check_docs_quality.py`.
- `uv run python tools/stale_detector.py docs/24_eventbus/eventbus_04_dlq_endpoint.md`.

## Completion criteria
- Neither line 43 nor the Concurrency guarantee paragraph calls the pre-insert check
  the concurrency guard; both name the index as the enforcement layer.
- 200/404/409 contract text byte-identical.
- Docs checkers report no errors for this file.

## Out of Scope
ADR-006 (seq 06), schema doc (seq 07), `dlq_repo.py` docstring wording (seq 02
carries the code-side reword), response contract changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Checker-gated, no new tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | This document's change IS the doc |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006 (DLQ endpoint doc states database enforcement)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: docs/24_eventbus/eventbus_04_dlq_endpoint.md

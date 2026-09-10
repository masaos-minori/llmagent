# Create the canonical EventBus delivery and recovery specification

## Priority
Low

## Summary
`docs/06_eventbus_*.md` already covers persistence/schema/replay
(`06_eventbus_03_persistence_schema_and_replay.md`) and DLQ/offset/delivery semantics
(`06_eventbus_04_dlq_offsets_and_delivery_semantics.md`), including a "SQLite/JSONL
Consistency Check and Recovery Procedure" section — confirmed by direct read of both files'
headings. However, that recovery section is explicitly scoped as detection-only
("Recommended Additional Actions (Documentation Only for this Phase)"), and a repository-wide
search for "recovery runbook"/"WAL"/"controlled restart" across all `docs/06_eventbus_*.md`
files returns no match — confirmed by `grep`, no executable operator recovery runbook covering
WAL files, integrity checking, sequence validation, consumer progress, or DLQ state currently
exists for EventBus.

## Background
Confirmed by direct read: `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`'s
headings (`Dead Letter Queue`, `Consumer Offset`, `Delivery Guarantees`, `Consumer ID Collision
Risk`, `Reliability Limits`) already cover much of what memo4.md's "state-transition and
delivery-semantics section" requests, and `docs/06_eventbus_03_persistence_schema_and_replay.md`
already documents the SQLite/JSONL consistency *check*. What is confirmed missing is: (1) an
executable recovery runbook (the existing consistency-check section is explicitly documentation-
only for its current phase, with no restart/rollback procedure), and (2) a single canonical
cross-reference tying schema, API contract, and runtime behavior together with links to
verification evidence, as opposed to the current per-chapter split.

## Problem
Publish, subscribe, replay, ACK, NACK, DLQ promotion, requeue, persistence, and recovery rules
are distributed across multiple implementation files and multiple documentation chapters, with
the actual operator-executable recovery procedure not yet written (only its detection
groundwork is). Without one canonical contract that links each invariant to verification
evidence, a code change can resolve a local defect while creating a new contradiction in a
sibling chapter — a risk borne out by this batch's other issues, each of which found gaps
between what the current EventBus documentation implies and what `scripts/eventbus/` actually
does (e.g. this batch's EB-H01/H03 issues both touch delivery/offset/DLQ semantics documented
across the two chapters above).

## Reason for Change
Provide one current-specification source that explains the complete delivery lifecycle,
transaction boundaries, failure handling, redelivery behavior, and operational recovery. The
document must describe the implemented system only and link each invariant to verification
evidence.

## Implementation Intent
Rather than starting from scratch, consolidate and extend the existing
`06_eventbus_03_persistence_schema_and_replay.md`/`06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
chapters (and the others listed below) into one canonical cross-reference, and complete the
currently-documentation-only SQLite/JSONL consistency section into an actually executable
recovery runbook covering WAL files, integrity checking, sequence validation, consumer
progress, and DLQ state. This issue should be sequenced after this batch's higher-priority
implementation issues (EB-H01 through EB-M06) land, since the specification should describe the
implemented system, not a target state that may still change under those issues.

## Target Files or Areas
- `docs/06_eventbus_01_system-overview.md`
- `docs/06_eventbus_02_operations.md`
- `docs/06_eventbus_03_persistence_schema_and_replay.md`
- `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `docs/06_eventbus_05_configuration-and-operations.md`
- `docs/06_eventbus_06_reference-api.md`
- `docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- `docs/adr/ADR-008-sqlite-4db-separation.md`

## Required Changes
- Create one canonical state-transition and delivery-semantics section (extending the existing
  `06_eventbus_04` chapter rather than duplicating it elsewhere).
- Document consumer identity, ordering, ACK and NACK rules, offset semantics, replay,
  backpressure, DLQ promotion, requeue, and retention — reflecting whatever this batch's
  EB-H01/H02/H03/M03 issues actually implement, not the pre-implementation behavior.
- Document transaction boundaries and behavior after partial infrastructure failures.
- Complete the existing "SQLite/JSONL Consistency Check and Recovery Procedure" section
  (`06_eventbus_03`) from detection-only into an executable EventBus database recovery runbook
  covering WAL files, integrity checking, sequence validation, consumer progress, DLQ state,
  and controlled restart.
- Remove or correct contradictory and obsolete descriptions in related documents.
- Link each invariant to an automated test or an explicitly identified missing test.

## Constraints
- Keep unrelated behavior unchanged — this is a documentation issue; it should describe
  implemented behavior, not drive new runtime changes.
- Do not weaken fail-closed behavior, validation, or auditability.
- Do not mark this issue complete with documentation-only changes when the runtime behavior it
  describes is still defective — sequence this issue after the batch's implementation issues,
  per Implementation Intent.
- Do not invent configuration values, migration history, or approval evidence.

## Acceptance Criteria
- [ ] Each operation has documented preconditions, postconditions, and error responses.
- [ ] The specification identifies the canonical source for schema, API contract, and runtime
      behavior.
- [ ] The recovery runbook is executable by an operator and includes verification and rollback
      steps (not only detection, unlike the current `06_eventbus_03` section).
- [ ] Documentation checks report no unresolved contradiction introduced or left by this work.

## Testing Expectations
`uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, and
`uv run python tools/check_docs_consistency.py --domain eventbus` (if an eventbus domain
option exists — confirm the exact `--domain` value against `tools/check_docs_consistency.py`'s
actual supported list at implementation time). No code-level test changes expected, since this
is documentation-only.

## Documentation Impact
This issue's entire scope is the documents listed in Target Files or Areas — it is itself the
documentation-consolidation work, not a change requiring separate documentation follow-up.

## Out of Scope
- Any code change under `scripts/eventbus/` — this issue is documentation-only; the runtime
  behavior gaps it would otherwise need to reconcile are this batch's separate implementation
  issues (EB-H01 through EB-M06).
- Writing the full database-specific logical-verification implementation for the recovery
  runbook — document the procedure; implementing new verification code (if any is found
  missing) is out of scope here.

## Dependencies
Depends on this batch's EB-H01 (transactional ACK/offset), EB-H02 (backpressure), EB-H03 (DLQ
requeue redesign), and EB-M03 (state transitions) — the canonical specification should describe
their landed behavior, not be written against the pre-implementation state and then need
immediate revision.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm at implementation time which of this batch's other EventBus issues have actually landed
before writing the canonical specification — do not document behavior from this batch's issue
descriptions as if already implemented. Extend the existing `06_eventbus_03`/`06_eventbus_04`
chapters rather than creating parallel new documents; per `rules/coding.md`'s "Current behavior"
classification, treat any remaining doc/code mismatch found during this work as its own
Implementation-fix-required or Documentation-fix-required item, not as silently patched prose.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260907-125042
- **Related target files**: see Target Files or Areas above

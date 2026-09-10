## Goal
Replace "If different clients use the same `consumer_id`, the last write wins... This
is an intentional design choice" with the finalized one-connection-per-`consumer_id`
policy (REQ-007; Documentation Impact).

## Scope
In scope: "## Consumer ID Collision Risk" section only. Out of scope: "Dead Letter
Queue (DLQ)", "Consumer Offset" (that section is the sibling Plan's row 13 concern —
this row does not duplicate that edit), "Delivery Guarantees", "Reliability Limits" —
unrelated to this Requirement.

## Assumptions
- This section's current text describes a raw-string-collision-detection mechanism
  (`.map`-file-based, in `offsets.py`) conflated with a general "last write wins"
  framing — this Plan's row 01 (`broker.py`) adds a connection-level rejection
  (HTTP 409) that is a distinct, additional mechanism, not a replacement for the
  existing file-based collision detection (which remains, per the sibling Plan's Out-
  of-Scope retaining `offsets.py` unmodified).

## Design decisions
Replace the "last write wins... intentional design choice" framing with a description
that a second concurrent connection using the same non-empty `consumer_id` is now
rejected (HTTP 409) at the connection level, closing the race this section previously
described as accepted. Retain (do not remove) any remaining accurate description of
the underlying `.map`-file-based raw-string-collision detection, since that mechanism
is unrelated to and unremoved by this Plan (confirmed via `scripts/eventbus/offsets.py`,
a Reference File this Plan explicitly does not modify) — this row corrects the
document's characterization of "same `consumer_id`, concurrent use" as an accepted gap,
not any correction to the collision-detection mechanism itself.

## Alternatives considered
Renaming this section (e.g. to "Consumer ID Concurrency Policy") was considered and
rejected: the heading itself still accurately describes the topic (collision risk),
and this Plan closes the *concurrent-connection* collision specifically — renaming
would be a scope-creeping structural change not required by REQ-007.

## Implementation
### Target file
`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure
Replace the "## Consumer ID Collision Risk" section's body text describing
last-write-wins as intentional, with text stating the finalized rejection policy.

### Method
Prose edit within the existing section; no heading change.

### Details
Example replacement (adapt wording to match surrounding document style):
- Before: "If different clients use the same `consumer_id`, the last write wins and
  the offset is overwritten. This is an intentional design choice but can lead to
  offset inconsistencies due to collisions."
- After: state that a second concurrent connection attempting to use the same
  non-empty `consumer_id` as an already-active connection is rejected with HTTP 409 —
  only one active connection per non-empty `consumer_id` is permitted at a time,
  closing the previously-accepted last-write-wins race; the separate,
  filename-sanitization-based raw-string-collision detection (unrelated mechanism)
  remains in place for the legacy offset-file path.

## Compatibility considerations
This document must remain consistent with row 08 (operations doc) and the sibling
Plan's ADR-006/DB-architecture updates — none should describe last-write-wins as
current, accepted behavior once this Plan lands.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert this file's diff; no other document's correctness depends on this file's exact
wording beyond the cross-reference consistency noted above.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `uv run python tools/check_docs_structure.py docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `uv run python tools/check_docs_consistency.py --domain overview`

## Completion criteria
"Consumer ID Collision Risk" describes the one-connection-per-non-empty-`consumer_id`
rejection policy as current, canonical behavior — no remaining text describes
last-write-wins as an accepted, intentional design choice for concurrent connections.

## Out of scope
"Consumer Offset" section (sibling Plan's row 13); "Dead Letter Queue (DLQ)",
"Delivery Guarantees", "Reliability Limits" sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace "Consumer ID Collision Risk" body text with the rejection policy | Completed | — | — | |
| 2 | Run `check_docs_quality.py`/`check_docs_structure.py`/`check_docs_consistency.py` | Completed | — | — | |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092931
- **Related target files**: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

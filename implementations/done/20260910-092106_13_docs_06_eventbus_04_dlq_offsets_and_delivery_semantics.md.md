## Goal
Update the "Consumer Offset" section to describe per-consumer SQLite-backed offsets
instead of `{offsets_dir}/{sanitized_consumer_id}` files (REQ-006; AC-8).

## Scope
In scope: "## Consumer Offset" and its "### Explicit Ack-only Offset" subsection only.
Out of scope: "Dead Letter Queue (DLQ)", "Delivery Guarantees", "Consumer ID Collision
Risk", "Reliability Limits" — untouched, since `delivery_failure_count`/`dlq_at` and
collision-detection-by-filename remain unchanged per this Plan's Out-of-Scope.

## Assumptions
- "Consumer ID Collision Risk" describes the `.map`-file-based raw-string-collision
  detection in `offsets.py`, a distinct mechanism from the offset *value*'s storage —
  confirm this section does not need updating since collision detection itself is
  unchanged (still file-based, retained per Plan Out-of-Scope) even though the offset
  value's live-service store moves to SQLite.

## Design decisions
Replace "Offset files are stored in `{offsets_dir}/{sanitized_consumer_id}`. The
`consumer_id` is sanitized." with a description that the live-service offset store is
a per-consumer SQLite table, seeded once at startup from any legacy `offsets_dir`
files (additive, idempotent migration) — describing the policy and mechanism, not
literal current file paths or config values (per `skills/DESIGN.md` No concrete
configuration values).

## Alternatives considered
Removing all mention of `offsets_dir`/legacy files from this document was considered
and rejected: the legacy files and their migration remain operationally relevant
during the retention period (per Plan Out-of-Scope, `offsets.py`'s functions are not
deleted) — the document should describe both the new live-service store and the
legacy migration's existence, not erase the legacy mechanism's documentation
prematurely.

## Implementation
### Target file
`docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Rewrite the opening statement of "## Consumer Offset" to describe the SQLite-backed
   per-consumer offset table as the live-service source of truth.
2. Add a note that a one-time, idempotent startup migration seeds this table from any
   pre-existing legacy `offsets_dir` files, which remain in place (not deleted) during
   the retention period.
3. Review "### Explicit Ack-only Offset" for any statement assuming file-based storage
   specifically, and generalize it to the new store if needed.

### Method
Prose edit within the existing section/subsection; no new top-level heading.

### Details
Example replacement (adapt wording/language to match surrounding document style):
- Before: "Offset files are stored in `{offsets_dir}/{sanitized_consumer_id}`. The
  `consumer_id` is sanitized."
- After: state that each consumer's last-committed offset is stored in a per-consumer
  SQLite table, advanced atomically alongside that consumer's delivery-state record in
  one transaction; a legacy, file-based store existed previously and is migrated into
  this table once, idempotently, at service startup, with the legacy files retained
  (not deleted) during the retention period.

## Compatibility considerations
This document must remain consistent with row 12 (ADR-006) and row 14 (DB
architecture doc) — all three must describe the same per-consumer model without
contradiction.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert this file's diff; no other document's correctness depends on this file's exact
wording beyond the cross-reference consistency noted above.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- `uv run python tools/check_docs_structure.py docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`
- Manual cross-reference against rows 12/14 for consistency.

## Completion criteria
"Consumer Offset" describes the per-consumer SQLite-backed store as canonical, with
the legacy file-based mechanism described as a retained, migrated-from source, not the
live-service store (AC-8).

## Out of scope
"Dead Letter Queue (DLQ)", "Delivery Guarantees", "Consumer ID Collision Risk",
"Reliability Limits" sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite "Consumer Offset" opening statement for the SQLite-backed store | Pending | — | — | |
| 2 | Add note on the idempotent legacy-file migration | Pending | — | — | |
| 3 | Review "Explicit Ack-only Offset" subsection for file-based assumptions | Pending | — | — | |
| 4 | Run `check_docs_quality.py`/`check_docs_structure.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md

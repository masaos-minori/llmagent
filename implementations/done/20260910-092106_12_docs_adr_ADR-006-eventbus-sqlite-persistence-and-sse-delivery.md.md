## Goal
Update ADR-006's "Decision Details" and "Consequences" sections to describe the new
per-consumer delivery/offset model and the transactional ACK+offset write, replacing
the file-based-offset description (REQ-006; AC-8).

## Scope
In scope: "Decision Details" (around the Monotonicity Invariant bullet, line ~74) and
"Consequences" sections only. Out of scope: "Status", "Summary", "Context",
"Rationale", "Alternatives Considered" — this Plan implements decisions already
recorded there (per-consumer ACK tracking and atomic monotonicity are consistent with,
not contradicting, the existing Accepted decision); no re-litigation of Alternatives
is needed.

## Assumptions
- ADR-006's `Status` remains `Accepted` — this Plan implements the existing decision
  more precisely (per-consumer instead of a global flag, atomic instead of
  read-then-compare), it does not reverse any Accepted decision.
- Per `skills/DESIGN.md` Docs content policy — remove/retain and No source-code line
  numbers, this update must describe the mechanism (per-consumer table, atomic SQL
  statement) without citing file:line locations or literal current config values.

## Design decisions
Update the Monotonicity Invariant bullet (currently: "`new_offset <= current_offset`を
拒否するか警告して無視するか → 拒否する（Monotonicity Invariant）") to state that
rejection is enforced by a single atomic SQL statement against a per-consumer offset
table, not a read-then-compare file check. Update "Consequences" to note the ACK state
and offset are now tracked per consumer (not as a single global event flag), and that
the ACK write and offset advancement commit or roll back together in one transaction.

## Alternatives considered
Rewriting "Alternatives Considered" to add a new alternative (e.g. "global ACK flag
with per-consumer offset only") was considered and rejected: this Plan's design does
not reconsider any previously-rejected alternative — it implements the already-Accepted
decision with the specific persistence mechanism this Plan adds. No new alternative
needs recording.

## Implementation
### Target file
`docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. In "Decision Details", update the Monotonicity Invariant bullet to describe atomic,
   single-statement enforcement against a per-consumer offset store, replacing any
   wording that implies a file-based, read-then-compare check.
2. In "Consequences" (Positive/Negative/Operational as applicable), add a note that ACK
   state and offset tracking are per-consumer, and that the ACK+offset write path is
   transactional (commit-or-rollback together).

### Method
Prose edit within existing sections; no new `##`/`###` heading added.

### Details
Example replacement for the Monotonicity Invariant bullet (adapt wording to match
surrounding document style/language):
- Before: "`new_offset <= current_offset`を拒否するか警告して無視するか → 拒否する（Monotonicity Invariant）"
- After: state that a new offset not greater than the current per-consumer offset is
  rejected, enforced by a single atomic SQL statement against the per-consumer offset
  table (not a read-then-compare check), and that this enforcement is
  correctness-independent of the existing in-process request-serialization lock.

Add to Consequences: ACK state (`acked_at`'s tracking role) is now recorded per
`(consumer_id, event_id)` rather than as one global column per event, and the ACK
write and offset advancement land together in one transaction.

## Compatibility considerations
No change to ADR-006's `Status` (`Accepted`) or its Alternatives — this is a
Decision Details/Consequences refinement consistent with the existing decision.

## Security considerations
N/A: documentation only, no security-relevant content change beyond describing the
existing atomic-enforcement mechanism.

## Rollback considerations
Revert this file's diff; no other document depends on this ADR's exact wording beyond
cross-references already accounted for in rows 13/14.

## Validation plan
- `uv run python tools/check_docs_quality.py docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- `uv run python tools/check_docs_structure.py docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- Manual cross-reference: confirm the updated text is consistent with rows 13/14's
  updates (no contradicting description of the offset/ACK model across the three
  documents).

## Completion criteria
"Decision Details" and "Consequences" describe the per-consumer delivery/offset model
and the transactional ACK+offset write as the current, canonical design — no remaining
text implies a global ACK flag or a read-then-compare offset check (AC-8).

## Out of scope
"Status", "Summary", "Context", "Rationale", "Alternatives Considered" sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update Monotonicity Invariant bullet in Decision Details | Pending | — | — | |
| 2 | Update Consequences for per-consumer ACK/offset + transactional write | Pending | — | — | |
| 3 | Run `check_docs_quality.py`/`check_docs_structure.py` | Pending | — | — | |

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
- **Related target files**: docs/adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md

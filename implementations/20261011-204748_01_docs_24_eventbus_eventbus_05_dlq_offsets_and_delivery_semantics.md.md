## Goal
- Make `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` describe ACK state as the per-consumer boolean `consumer_delivery.acked`, with no timestamp column and no event-level ACK column (`REQ-001`; consistency with the endpoint reference and ADR-006 per `REQ-004`).

## Scope
- Every passage that describes current behavior with `acked_at`: the ACK postconditions, the NACK interaction notes, the resume-position note, the ACK row and the ACK paragraph of the state table, and the ACKed-then-NACK 409 note.
- No change to other sections, to code, or to other documents.

## Assumptions
- Verified in the current document: `acked_at` appears in the ACK postconditions, the NACK preconditions, the "NACK does not set" sentence, the NACK-checks sentence, the resume-position note, the state table's ACK row, the paragraph below the table, and the 409 line of the transition notes.
- Verified against current source: `consumer_delivery.acked` is an integer boolean; the first ACK sets it and it is never lowered; the ACK route does not read or write an event-level ACK column.
- No passage is an explicit historical or migration note.

## Design decisions
- Change only the column name and the predicate form: "set to the current timestamp" becomes "set"; "`acked_at` unset" becomes "`acked` not set"; "`acked_at IS NOT NULL`" becomes "`acked` is set"; "`acked_at IS NULL`" becomes "`acked` is not set".
- Remove the clause about an event-level ACK column the route "also rejects", since no such column exists.
- Keep the surrounding sentences, anchors, and headings.

## Alternatives considered
- Add a historical note about the old column: rejected; the document describes current behavior and the migration is covered by the schema document.
- Rewrite the state table: rejected; only the predicate wording changes.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Search the file for `acked_at` and list each occurrence.
2. Edit each occurrence as described under Details.
3. Search again; confirm no `acked_at` remains.
4. Run the documentation checkers.

### Method
- Use Edit with the full existing sentence as `old_string` for each occurrence; do not reflow unrelated text.

### Details
- ACK postconditions: "The consumer's `consumer_delivery.acked_at` is set to the current timestamp." becomes "The consumer's `consumer_delivery.acked` flag is set (it is never lowered by a later ACK)."
- NACK preconditions: "(`consumer_delivery.acked_at` unset for that consumer and event)" becomes "(`consumer_delivery.acked` not set for that consumer and event)".
- "NACK does not set the consumer's `consumer_delivery.acked_at`" becomes "NACK does not set the consumer's `consumer_delivery.acked` flag".
- "`nack_event` checks `consumer_delivery.acked_at`" becomes "`nack_event` checks `consumer_delivery.acked`".
- Resume-position note: "(`consumer_delivery.acked_at IS NULL`, or no `consumer_delivery` row ...)" becomes "(`consumer_delivery.acked` not set, or no `consumer_delivery` row ...)".
- State table ACK row: "`consumer_delivery.acked_at IS NOT NULL`" becomes "`consumer_delivery.acked` is set".
- Paragraph under the table: "recorded per consumer in `consumer_delivery.acked_at` and in `consumer_offsets`; the ACK route does not write the event-level `events.acked_at` column" becomes "recorded per consumer in `consumer_delivery.acked` and in `consumer_offsets`; there is no event-level ACK state"; keep the code-evidence parenthetical and the sentence about per-consumer application.
- 409 line: "via `consumer_delivery.acked_at`; the route also rejects an event whose `events.acked_at` is set, a column the ACK route does not write" becomes "via `consumer_delivery.acked`".

## Compatibility considerations
- Documentation only; headings and anchors unchanged, so links from other documents stay valid. Wording matches `eventbus_12_ack_nack_endpoints.md` and ADR-006.

## Security considerations
N/A: documentation only; no secrets or permissions.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` before it is committed.

## Validation plan
- `rg acked_at` on this file returns nothing.
- Run the checkers from `routing.md` "When to run which tool" with explicit paths: `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, `tools/check_needs_confirmation_inventory.py`.

## Completion criteria
- No `acked_at` and no event-level ACK column is described as current behavior in this file.
- The state table and transition notes define ACKed by the boolean `acked`.
- The checkers report no findings and only the listed passages changed.

## Out of scope
- Code, tests, schema, other documents, and unrelated passages of this document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace each acked_at passage with the boolean acked wording | Completed | 20261011-204901 | 20261011-204901 | Eight acked_at passages replaced with the boolean acked wording; no acked_at remains |
| 2 | Add or update tests per Validation plan | Completed | 20261011-204901 | 20261011-204901 | N/A: documentation only N/A: documentation only |
| 3 | Run the documentation checkers and the acked_at search | Completed | 20261011-204901 | 20261011-204901 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_needs_confirmation_inventory: no findings; generator dry-run matches |

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
- **Requirement ID**: `REQ-001` (boolean ACK state), `REQ-004` (consistency)
- **Source issue**: issues/20261011-204519_eb014ackeddoc_replace-stale-acked_at-wording-in-eventbus-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-204704_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-204748
- **Related target files**: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md
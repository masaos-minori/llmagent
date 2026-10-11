## Goal
- Make `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` list the real `events` columns and describe `consumer_delivery` with its real columns and the idempotent boolean upsert (`REQ-002`; consistency per `REQ-004`).

## Scope
- The `events` key-column sentence (remove the ACK column) and the `consumer_delivery` description (columns and upsert).
- No other change.

## Assumptions
- Verified in the current document: the `events` list names an event-level `acked_at`, and the `consumer_delivery` line names `consumer_delivery(consumer_id, event_id, acked_at)` with an upsert that sets `acked_at`.
- Verified against current source: `events` has no ACK column (a migration drops it); `consumer_delivery` has `acked` (integer, default 0), `consumer_delivery_failure_count`, `consumer_last_nack_attempt`, primary key `(consumer_id, event_id)`; the ACK upsert sets `acked` to the higher of the stored and new value.

## Design decisions
- Remove only the `acked_at` item and its parenthetical from the `events` list; keep every other column, the schema-source sentence, and the Known Issue reference.
- Describe `consumer_delivery` by its columns and the idempotent upsert in behavioral terms, without SQL text beyond the conflict target.

## Alternatives considered
- Keep a note that the column existed historically: rejected; the document describes the current schema.
- Add the new columns to the `events` list: rejected; they belong to `consumer_delivery`. The `events` list line already names `consumer_delivery_failure_count`, which is out of scope here and is not changed.

## Implementation
### Target file
`docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md`

### Procedure
1. Search the file for `acked_at` and list each occurrence.
2. Edit the `events` key-column sentence and the `consumer_delivery` line.
3. Search again; confirm no `acked_at` remains.
4. Run the documentation checkers.

### Method
- Use Edit with the exact sentence as `old_string`; keep the rest of each line unchanged.

### Details
- `events` list: delete "`acked_at` (event-level column; not written by the ACK routes, which record acknowledgements per consumer in `consumer_delivery`), " so the list reads `published_at`, `delivery_failure_count`, and so on.
- `consumer_delivery` line: replace with "`consumer_delivery(consumer_id, event_id, acked, consumer_delivery_failure_count, consumer_last_nack_attempt)` — composite PK on `(consumer_id, event_id)`. Tracks per-consumer delivery state; `acked` is a boolean set on the first ACK and never lowered. Idempotent via `INSERT ... ON CONFLICT DO UPDATE`, which keeps the higher of the stored and new `acked` value."

## Compatibility considerations
- Documentation only; headings and anchors unchanged. Wording matches the endpoint reference and ADR-006 (no event-level ACK column).

## Security considerations
N/A: documentation only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` before it is committed.

## Validation plan
- `rg acked_at` on this file returns nothing.
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py` with explicit paths.

## Completion criteria
- The `events` list has no ACK column and the `consumer_delivery` description names the real columns and the boolean upsert.
- The checkers report no findings and only those two passages changed.

## Out of scope
- Code, schema, other documents, and other passages.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the events key columns and the consumer_delivery description | Completed | 20261011-204901 | 20261011-204901 | events key columns and consumer_delivery description corrected; no acked_at remains |
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
- **Requirement ID**: `REQ-002` (schema description), `REQ-004` (consistency)
- **Source issue**: issues/20261011-204519_eb014ackeddoc_replace-stale-acked_at-wording-in-eventbus-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-204704_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-204748
- **Related target files**: docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md
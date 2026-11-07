## Goal

- docs/24_eventbus/eventbus_05 — required-consumer NACK contract wording (AC-005, REQ-007)

## Scope
**Release unit**: N/A: outside the facade-cutover unit

- Phase 3 documentation only; it follows the Phase 1-2 unit and changes no code. Checker-config consolidation stays with compatrm004 (Plan Release unit row).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Clarify line 93 with a two-word consumer attribution and rewrite the line 101 conditional into the required-consumer contract.

## Alternatives considered

- Leave line 93 untouched: accepted partially — the Plan row lists 93/101, so the consumer attribution is made explicit at minimal cost.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
### Procedure
1. Line 93: replace "a NACK that repeats the stored
   `consumer_delivery.consumer_last_nack_attempt`" with "a NACK that repeats that
   consumer's stored `consumer_delivery.consumer_last_nack_attempt`" (single-phrase
   clarification; the rest of the paragraph is already consumer-scoped).
2. Line 101: replace the paragraph with:
   ```markdown
   `nack_event` requires a non-empty `consumer_id` (an empty value raises `ValueError` before any query) and checks `consumer_delivery.acked` for the requesting consumer; a NACK from a consumer that has already ACKed the event is rejected with HTTP 409 `event already acknowledged`.
   ```
3. Leave the rest of the DLQ/offset sections unchanged (the surrounding bullets are
   already consumer-scoped).
### Method
REQ-007 / AC-005. The "Duplicate NACK Behavior" paragraph (line 93) states the
idempotency rule in consumer-scoped terms already and only needs explicit consumer
attribution; the "ACK followed by NACK" paragraph (line 101) still conditions the ACK
guard on "when `consumer_id` is provided", which is the optional-parameter wording the
Issue removes. After docs 03/05, `consumer_id` is a required non-empty argument of
`nack_event()`.
### Details
Two paragraph edits.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling documents 03, 05 (the documented required-consumer contract exists).
  - Blocks: none.

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Revert the documentation commit.

## Validation plan

- Command: `grep -n "when \`consumer_id\` is provided" docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
  Expected: no matches.
- Command: `grep -n "requires a non-empty \`consumer_id\`" docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
  Expected: one match.
- Command: `python3 tools/check_docs_links.py`
  Expected: no broken links.
  conditional-consumer wording remains (AC-005).

## Completion criteria

- the section states the required-consumer NACK contract and no (AC-005, REQ-007)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the eventbus_05 NACK contract wording — Plan Phase 3 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Requirement ID**: REQ-007 / AC-005
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

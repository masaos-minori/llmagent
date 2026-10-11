## Goal
- Update `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` so it describes exactly one ACK contract, including the HTTP 409 returned when an ACK targets an event already in the DLQ (`REQ-006`).

## Scope
- Add a "Conflict Response" subsection to the "Acknowledge Event" section, between "Not Found Response" and "Forbidden Response".
- Add one row for the ACK-on-DLQ case to the ACK/NACK State Transition Table.
- Documentation only; no code, test, or ADR change.

## Assumptions
- Verified in the current document: the 409 description appears only under "Negatively Acknowledge Event" ("Conflict Responses"), and the State Transition Table has no row for an ACK on a DLQ event.
- The route returns 409 with the detail `event already in dead letter queue` after procedure 04, and the repository returns `(True, False, None)` for that case without writing.
- Documentation conventions: English, no line numbers, no concrete configuration values, no implementation counts (`docs/00_governance/governance_01_documentation-policy.md`); the file's front matter and `Keywords` section stay as they are.

## Design decisions
- Describe behavior (status, response body, side effects), not a function-signature table, as the source issue requires.
- Reuse the table's existing column layout and wording style for the new row.
- Do not change the duplicate-ACK response description; the `newly_acked` versus `already_acked` question is Plan `UNK-03`.

## Alternatives considered
- Add the DLQ-ACK case only to the table: rejected; every other response has its own subsection.
- Describe the 4-value repository return: rejected; the contract is three values.

## Implementation
### Target file
`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure
1. Re-read the "Acknowledge Event" section and the State Transition Table.
2. Insert the subsection "Conflict Response" with `**HTTP 409 Conflict**`, stating that it is returned when the event is already in the DLQ (`events.dlq_at`), with the response schema `{"detail": "event already in dead letter queue"}`.
3. Add the table row: Scenario "ACK on a DLQ event", Behavior "the ACK route finds `events.dlq_at` set and rejects the ACK", HTTP status 409, response body `event already in dead letter queue`, side effects "None: no delivery state or offset is written".
4. Run the documentation checkers.

### Method
- Use Edit with the neighboring existing headings as anchors so nothing else changes.
- Keep the heading depth consistent with the other response subsections (`###` for the group, `####` for the schema).

### Details
- Place the new table row after "Unknown event ID (ACK)".
- Keep the statement that ACK state is per consumer; do not reintroduce an event-level `acked_at` column.

## Compatibility considerations
- Anchors and headings referenced from other documents (`eventbus_02_api-reference-index.md`, `eventbus_05_dlq_offsets_and_delivery_semantics.md`) are unchanged; only additions are made.
- ADR-006 is not changed; INV-16 does not state the return shape.

## Security considerations
N/A: documentation only; no secrets or permissions.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` before it is committed.

## Validation plan
- Run the checkers from `routing.md` "When to run which tool" for edited docs, with explicit file paths: `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py`; confirm each reports no findings.
- Manual review: the new text matches the route behavior from procedure 04 and the test from procedure 05.

## Completion criteria
- The ACK section documents the 409 for a DLQ event, and the State Transition Table has the matching row.
- Exactly one ACK contract is described; no 4-value form appears.
- The documentation checkers report no findings.

## Out of scope
- The duplicate-ACK field name (`UNK-03`), ADR-006, the reference API table, and any code or test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the "Conflict Response" subsection to the Acknowledge Event section | Pending | — | — | |
| 2 | Add the ACK-on-DLQ row to the State Transition Table | Pending | — | — | |
| 3 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation only; checkers run in the next step |
| 4 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document ACK-on-DLQ 409)
- **Source issue**: issues/20261011-075321_eb012ack_resolve-ack_event_for_consumer-return-contract-mismatch-between-code-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-153619_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-175858
- **Related target files**: docs/24_eventbus/eventbus_12_ack_nack_endpoints.md

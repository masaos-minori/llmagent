## Goal
- Correct `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` so its duplicate-ACK response uses the field the route actually returns, `already_acked: true`, absent on a first ACK (`REQ-002`: replace `newly_acked`; `REQ-003`: one name across route, tests, and documents).

## Scope
- Three places in the Acknowledge Event material: the already-acknowledged response schema, the field description table, and the Duplicate ACK row of the State Transition Table.
- No change to the route, tests, or any other document.

## Assumptions
- Verified in the current document: `newly_acked` appears in exactly those three places.
- Verified against current source: the ACK route sets `already_acked` only on a duplicate ACK; three test modules and `eventbus_05_dlq_offsets_and_delivery_semantics.md` use `already_acked`.
- The owner has not confirmed the name (Plan `UNK-01`); the default is to match the existing behavior.

## Design decisions
- Keep `already_acked` and fix the reference, because renaming the route field would change a public response shape.
- Describe behavior (presence and value), not a signature table.

## Alternatives considered
- Rename the route field to `newly_acked`: rejected; public response-shape change, three test modules would also change.
- Document both fields: rejected; the route returns only one.

## Implementation
### Target file
`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure
1. Re-read the three places and confirm they still name `newly_acked`.
2. In the already-acknowledged response schema, replace `"newly_acked": false` with `"already_acked": true`.
3. In the field table, replace the `newly_acked` row with an `already_acked` row stating that it is absent on the first ACK and `true` on a duplicate ACK.
4. In the Duplicate ACK row of the State Transition Table, replace `newly_acked: false` with `already_acked: true`.
5. Run the documentation checkers.

### Method
- Use Edit with each full existing line as `old_string`; change nothing else.

### Details
- Field table row: `| \`already_acked\` | boolean | Absent on the first acknowledgement; \`true\` when the consumer had already acknowledged the event |`.
- Do not touch the 409 sections added earlier.

## Compatibility considerations
- Documentation only; behavior is unchanged. Headings and anchors are unchanged.

## Security considerations
N/A: documentation only; no secrets or permissions.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` before it is committed.

## Validation plan
- Run the checkers from `routing.md` "When to run which tool" with explicit paths: `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, `tools/check_needs_confirmation_inventory.py`.
- `rg newly_acked docs/24_eventbus` returns no match for this file.
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py tests/eventbus/test_eventbus_concurrent.py` passes (existing tests).

## Completion criteria
- The document contains no `newly_acked` and describes `already_acked` with the presence rule in all three places.
- The checkers report no findings and only those three places changed.

## Out of scope
- Route, tests, `eventbus_05_dlq_offsets_and_delivery_semantics.md`, and the `acked_at` wording noted as Plan `UNK-02`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace newly_acked with already_acked in the schema, field table, and Duplicate ACK row | Completed | 20261011-201601 | 20261011-201601 | Three places changed in docs/24_eventbus/eventbus_12_ack_nack_endpoints.md; no newly_acked remains. Procedure line 58 abbreviation corrected after stale detector flagged it |
| 2 | Add or update tests per Validation plan | Completed | 20261011-201601 | 20261011-201601 | N/A: documentation only; existing tests are run in step 3 N/A: documentation only |
| 3 | Run the documentation checkers and the existing ACK test modules | Completed | 20261011-201601 | 20261011-201601 | Docs checkers: no findings; ack_nack + ack_endpoint + concurrent: 32 passed; full suite not run (no Python change) |

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
- **Requirement ID**: `REQ-002` (correct the field name), `REQ-003` (one name across route, tests, documents)
- **Source issue**: issues/20261011-201147_eb013ackresp_align-duplicate-ack-response-field-name-between-route-tests-and-documentation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-201351_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-201510
- **Related target files**: docs/24_eventbus/eventbus_12_ack_nack_endpoints.md
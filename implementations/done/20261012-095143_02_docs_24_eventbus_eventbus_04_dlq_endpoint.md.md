## Goal
- State in `docs/24_eventbus/eventbus_04_dlq_endpoint.md` what the DLQ listing's `delivery_failure_count` holds, consistent with the NACK endpoint reference (`REQ-002`, `REQ-003`).

## Scope
- The `items` description in the List DLQ Entries response field table, and at most one short clarifying sentence next to it.
- No change to schemas, examples, status codes, or other sections.

## Assumptions
- Verified against current source: `fetch_dlq` selects `delivery_failure_count` from the `events` table; no statement in `scripts/eventbus` updates that column on NACK, so under the per-consumer model it is a legacy value that is not modified by NACK (it is copied on requeue).
- Verified in the current document: the field is listed by name only inside the `items` row.
- Verified in `eventbus_12_ack_nack_endpoints.md`: the NACK response field is the per-consumer failure count; the DLQ listing value is a different, stored events-level value.
- The owner's answer on external use is not available; the edit states current behavior only.

## Design decisions
- Describe the field in behavioral terms (stored events-level value, not modified by NACK, not the per-consumer count) without line numbers or implementation counts (docs content policy).
- Do not call the value a lifetime count.

## Alternatives considered
- Remove the field from the description: rejected; it is still returned, and removing it would misdescribe the response.

## Implementation
### Target file
`docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Procedure
1. Re-read the `items` row of the field table and confirm it only lists the field name.
2. Edit the row so that `delivery_failure_count` is described as the stored events-level value, a legacy value that NACK does not modify under the per-consumer model and that is not the per-consumer failure count returned by the NACK endpoint.
3. Search both endpoint documents for "lifetime" and confirm no passage calls either value a lifetime count.
4. Run the documentation checkers.

### Method
- Use the Edit tool on the affected row only; keep the table structure.

### Details
- Suggested wording: "`delivery_failure_count` (the stored events-level value; a legacy value that NACK does not modify, not the per-consumer failure count returned by `POST /nack`)".

## Compatibility considerations
- Documentation only; the described response is unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_04_dlq_endpoint.md` before it is committed.

## Validation plan
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py` with explicit paths.
- Search for "lifetime" in `eventbus_04_dlq_endpoint.md` and `eventbus_12_ack_nack_endpoints.md`.

## Completion criteria
- The listing field's meaning is stated and does not contradict the NACK endpoint reference; the checkers report no findings.

## Out of scope
- Other eventbus documents (including the promotion-condition drift in `eventbus_03_dlq_operations.md`), code, tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Describe the DLQ listing delivery_failure_count | Completed | 20261012-095224 | 20261012-095224 | — items row now states the stored events-level legacy value, not the per-consumer count |
| 2 | Add or update tests per Validation plan | Completed | 20261012-095224 | 20261012-095224 | N/A: documentation only N/A: documentation only |
| 3 | Run the documentation checkers and the wording search | Completed | 20261012-095224 | 20261012-095224 | — Four doc checkers no findings; no lifetime wording in either endpoint document |

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
- **Requirement ID**: `REQ-002` (DLQ listing field description), `REQ-003` (consistency)
- **Source issue**: issues/20261012-090140_eb017nackext_confirm-external-consumers-of-nack-response-and-nackresult-counters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-093531_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-095143
- **Related target files**: docs/24_eventbus/eventbus_04_dlq_endpoint.md
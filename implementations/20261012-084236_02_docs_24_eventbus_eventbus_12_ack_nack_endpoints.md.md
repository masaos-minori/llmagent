## Goal
- Correct the NACK response field description in `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` so it names the per-consumer failure count instead of a lifetime count (`REQ-002`).

## Scope
- The `delivery_failure_count` row of the NACK response field table, plus any other passage of this document that calls the value a lifetime or event-level count.
- No change to schemas, examples, status codes, or the state table.

## Assumptions
- Verified against current source: the NACK route requires `consumer_id`, so a successful NACK returns the per-consumer failure count in the `delivery_failure_count` response field.
- Verified in the document: the field table says "Lifetime failure count after this NACK"; the state table already speaks of the per-consumer counter.
- The response field keeps its name; renaming needs owner approval (UNK-02 of the plan).

## Design decisions
- Change the description only, in English, without line numbers or implementation counts (docs content policy).

## Alternatives considered
- Rename the field in the document: rejected; it would contradict the route.

## Implementation
### Target file
`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure
1. Search the document for "lifetime" and "failure count" and list passages describing the NACK response value.
2. Rewrite the field table row to: the per-consumer failure count after this NACK.
3. Fix any other passage that calls the value a lifetime or event-level count; leave the rest untouched.
4. Run the documentation checkers.

### Method
- Use the Edit tool on the affected lines only.

### Details
- Target wording: "Per-consumer failure count after this NACK (the consumer given in `consumer_id`)".
- The state-table row "NACK followed by ACK" already says the value keeps the NACK value; keep it consistent without editing it unless it contradicts the new wording.

## Compatibility considerations
- Documentation only; no change to the described response.

## Security considerations
N/A: documentation only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` before it is committed.

## Validation plan
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py` with explicit paths.
- Search the document for "lifetime" and confirm no remaining description of this field.

## Completion criteria
- The field table names the per-consumer count; no passage calls the value lifetime or event-level; the checkers report no findings.

## Out of scope
- Schemas, examples, state table, other documents, code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the NACK response field description | Completed | 20261012-084422 | 20261012-084422 | — Field description now names the per-consumer count |
| 2 | Add or update tests per Validation plan | Completed | 20261012-084422 | 20261012-084422 | N/A: documentation only N/A: documentation only |
| 3 | Run the documentation checkers and the wording search | Completed | 20261012-084422 | 20261012-084422 | — Four doc checkers no findings; no lifetime wording remains |

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
- **Requirement ID**: `REQ-002` (NACK response field description)
- **Source issue**: issues/20261012-083711_eb016nackres_decide-the-contract-of-legacy-events-level-counters-in-nackresult.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-084200_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-084236
- **Related target files**: docs/24_eventbus/eventbus_12_ack_nack_endpoints.md
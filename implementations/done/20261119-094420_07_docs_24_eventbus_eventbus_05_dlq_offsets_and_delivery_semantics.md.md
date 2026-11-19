## Goal
- Define the `delivery: "replay"` value of the requeue response in the DLQ semantics guide (REQ-005: no undefined response value).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one sentence in the "Requeue (Redelivery)" section of `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`.

## Assumptions
- `dlq_route.py` returns `"delivery": "replay"` on a successful requeue, and `eventbus_09_publish_durability.md` already explains it in its "Requeue Delivery Semantics" section (verified in Step 3a); that guide is not edited here.
- If a documentation checker requires a front matter `related:` entry for the new cross-reference, add `eventbus_09_publish_durability.md` to this file's own `related:` list; no other file changes.

## Design decisions
- State the meaning (consumers receive the new row through the replay path, not a live broker push) and point to the publish durability guide, instead of copying its text.

## Alternatives considered
N/A: a one-sentence documentation addition.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. After the paragraph that ends "...through the existing `seq > since_seq` replay path in the subscribe endpoint.", add one sentence: a successful requeue response carries `"delivery": "replay"`, which states that the requeued row reaches consumers through the replay path and is not pushed through `EventBroker`; see `eventbus_09_publish_durability.md`, section "Requeue Delivery Semantics".

### Method
- English only; plain prose; no file path, port, or config value; reuse the existing term "replay path".

### Details
- Do not add a response example or a field table (docs content policy).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.
- `uv run python tools/check_docs_consistency.py --domain eventbus`.

## Completion criteria
- The guide defines `delivery: "replay"` and points to the publish durability guide; all checkers above pass.

## Out of Scope
- Any other section of the guide and any change to `eventbus_09_publish_durability.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the sentence to the Requeue section | Completed | 20261119-100524 | 20261119-100548 | Step 2 stale check clean; guide clean at baseline Changed: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261119-100548 | 20261119-100548 | Docs checkers pass: quality, structure, content-policy strict, japanese, consistency eventbus; no front matter related entry needed |

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
- **Requirement ID**: `REQ-005` (define the requeue `delivery` value)
- **Source issue**: issues/20261117-123002_adrchk002_eventbus-authz-model.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-092411_adrchk002_eventbus-authz-model.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-094420
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
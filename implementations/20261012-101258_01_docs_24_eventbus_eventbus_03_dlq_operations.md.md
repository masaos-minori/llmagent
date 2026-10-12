## Goal
- Correct the DLQ Promotion Paths and DLQ Background Sweep sections of `docs/24_eventbus/eventbus_03_dlq_operations.md` to per-consumer gating, with a pointer to `eventbus_05_dlq_offsets_and_delivery_semantics.md` for the exact rule (`REQ-001`, `REQ-002`, `REQ-003`).

## Scope
- The "Inline promotion" bullet in DLQ Promotion Paths and the first paragraph of DLQ Background Sweep, plus the orphaned-events explanation only if it depends on the events-level counter.
- No change to other sections, front matter, or the shared-routine and optimistic-guard sentences.

## Assumptions
- Verified in the current document: the inline bullet says a `POST /nack` call "raises `delivery_failure_count` to `max_retry` or beyond"; the sweep paragraph says it searches events where `delivery_failure_count >= max_retry AND dlq_at IS NULL`.
- Verified against current source: the sweep query joins `consumer_delivery` and filters on `consumer_delivery_failure_count` with `dlq_at IS NULL`; the NACK route compares the nacking consumer's per-consumer count with `max_retry`; the events-level counters are not written by NACK.
- Verified in `eventbus_05_dlq_offsets_and_delivery_semantics.md`: the anchors `#inline-promotion-path` and `#background-loop-promotion` exist; `eventbus_05_dlq_offsets_and_delivery_semantics.md` is already in this document's front matter `related` list.
- The orphaned-events sentence ("recorded in the logs"; a non-zero count may indicate an inline-promotion problem) does not depend on the events-level counter and stays.
- The multi-consumer rule is unresolved (`issues/20261012-100156_eb019dlqmulti_*`); this document must not assert it.

## Design decisions
- Describe the gate as the per-consumer failure count reaching the retry limit, without saying how multiple consumers combine; refer to `eventbus_05_dlq_offsets_and_delivery_semantics.md` for that.
- Do not mention the events-level `delivery_failure_count` in these sections.

## Alternatives considered
- Restate the ADR-006 rule here: rejected; the rule is unresolved and duplicating it would create a second statement to maintain.

## Implementation
### Target file
`docs/24_eventbus/eventbus_03_dlq_operations.md`

### Procedure
1. Re-read the DLQ Promotion Paths and DLQ Background Sweep sections.
2. Rewrite the inline bullet: promotion is triggered synchronously when a `POST /nack` call brings the nacking consumer's per-consumer failure count to the retry limit; see the Inline Promotion Path in `eventbus_05_dlq_offsets_and_delivery_semantics.md` for the exact rule.
3. Rewrite the sweep paragraph: the sweep selects events by the per-consumer failure count reaching the retry limit while `dlq_at IS NULL`; see Background Loop Promotion in `eventbus_05_dlq_offsets_and_delivery_semantics.md` for the exact rule.
4. Search the document for `delivery_failure_count` and confirm no promotion passage still uses it.
5. Run the documentation checkers.

### Method
- Use the Edit tool on the affected sentences only.
- Use relative links with the anchors `#inline-promotion-path` and `#background-loop-promotion`.

### Details
- Keep the sentence "Both paths call the same shared promotion routine ..." and the optimistic-locking paragraph unchanged except for the selection condition.

## Compatibility considerations
- Documentation only; no behavior change.

## Security considerations
N/A: documentation only.

## Rollback considerations
- Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_03_dlq_operations.md` before it is committed.

## Validation plan
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, and `tools/check_needs_confirmation_inventory.py` with explicit paths.
- Search the document for `delivery_failure_count`; confirm the two anchors exist in `eventbus_05_dlq_offsets_and_delivery_semantics.md`.

## Completion criteria
- Neither section gives the events-level counter as the promotion condition; the exact rule is delegated to `eventbus_05_dlq_offsets_and_delivery_semantics.md`; the multi-consumer rule is not stated; the checkers report no findings.

## Out of scope
- Code, tests, ADR, `eventbus_05_dlq_offsets_and_delivery_semantics.md`, and the multi-consumer rule (eb019).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the promotion passages and add the pointer to eventbus_05_dlq_offsets_and_delivery_semantics.md | Completed | 20261012-101335 | 20261012-101335 | — Inline bullet and sweep paragraph now use the per-consumer count and link to eventbus_05 anchors |
| 2 | Add or update tests per Validation plan | Completed | 20261012-101335 | 20261012-101335 | N/A: documentation only N/A: documentation only |
| 3 | Run the documentation checkers and the delivery_failure_count search | Completed | 20261012-101335 | 20261012-101335 | — Four doc checkers no findings; no delivery_failure_count left in the document |

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
- **Requirement ID**: `REQ-001` (inline promotion), `REQ-002` (background sweep), `REQ-003` (pointer, no multi-consumer rule)
- **Source issue**: issues/20261012-095413_eb018dlqprom_correct-dlq-promotion-conditions-in-eventbus_03-to-per-consumer-gating.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-101129_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-101258
- **Related target files**: docs/24_eventbus/eventbus_03_dlq_operations.md
## Goal
- Cite the new multi-consumer tests in the verification entry for ADR-006 INV-13 and correct the stale test name found there (`REQ-005`).

## Scope
- The `Implementation` line of the verification entry "Events move to the DLQ after the Retry limit" only.
- No change to the decision text, the invariants, or other entries.

## Assumptions
- Verified in the current document: the entry cites `tests/eventbus/test_eventbus_dlq_promotion.py::TestDLQPROMotionSemantics::test_dlq_promotion_when_delivery_failure_count_gte_max_retry`, which does not exist; the real test is `test_dlq_promotion_when_consumer_delivery_failure_count_gte_max_retry`.
- Verified in the current document: it also cites `tests/eventbus/test_eventbus_dlq.py::test_inline_dlq_promotion_on_nack`, which exists and exercises one consumer.
- Depends on procedure 03: the new test names exist.

## Design decisions
- Correct the stale name and append the multi-consumer tests that exercise the rule; leave the decision text untouched because the ADR rule was adopted unchanged.

## Alternatives considered
- Reword INV-13: rejected; the decision is unchanged.

## Implementation
### Target file
`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure
1. Re-read the verification entry.
2. Replace the stale test name with the real one.
3. Append `tests/eventbus/test_eventbus_dlq_promotion.py::TestMultiConsumerPromotion::test_sweep_does_not_promote_when_other_consumer_below_limit`, `...::test_sweep_does_not_promote_when_other_consumer_acked`, `...::test_inline_does_not_promote_when_other_consumer_below_limit`, and `...::test_inline_promotes_when_last_consumer_reaches_limit` using full paths.
4. Run `tools/check_adr_invariant_matrix.py` and the other ADR and documentation checkers.

### Method
- Use the Edit tool on that single line.

### Details
- Use the full `path::Class::test` form as in neighboring entries.

## Compatibility considerations
- Verification list only; no decision change.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert with `git revert` of the implementing commit, or `git checkout -- docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` before it is committed.

## Validation plan
- Run `tools/check_adr_structure.py`, `tools/check_adr_invariant_matrix.py`, `tools/check_adr_reference.py`, `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, and `tools/check_docs_content_policy.py`; confirm every cited test name exists with `rg`.

## Completion criteria
- Every cited test exists, the multi-consumer tests are cited, and the checkers report no findings.

## Out of scope
- The decision text and other ADR entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the stale test name and cite the new tests | Completed | 20261012-105300 | 20261012-105300 | — Corrected the stale test name and cited the multi-consumer test class |
| 2 | Add or update tests per Validation plan | Completed | 20261012-105300 | 20261012-105300 | N/A: documentation only N/A: documentation only |
| 3 | Run the ADR and documentation checkers and verify the cited test names | Completed | 20261012-105300 | 20261012-105300 | — ADR checkers and docs checkers no findings; ADR-006 stays under the size limit (24456 bytes) |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261012-100156_eb019dlqmulti_resolve-multi-consumer-dlq-promotion-rule-mismatch-between-adr-006-and-code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-102459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-104559
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md
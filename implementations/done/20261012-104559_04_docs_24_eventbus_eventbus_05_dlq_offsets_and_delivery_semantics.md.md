## Goal
- Define "attempting consumer" in `eventbus_05_dlq_offsets_and_delivery_semantics.md` and state its consequence for promotion (`REQ-005`).

## Scope
- The promotion description (the paragraph that says promotion requires every consumer that attempted delivery to have given up, and the Inline Promotion Path / Background Loop Promotion sections if the term appears there).
- No change to state tables or other sections.

## Assumptions
- Verified in the current document: the rule is stated with "every consumer that attempted delivery" without defining the term; an event with no delivery record is stated as never promoted.
- Verified against current source: delivery records are created only by a consumer's ACK or NACK, so a consumer that has only received the event has no record.
- The wording follows the code after procedures 01 and 02.

## Design decisions
- Add one definition and one consequence, in behavioral terms without line numbers or implementation counts (docs content policy).

## Alternatives considered
- Define the term in the ADR: rejected; the ADR decision text is unchanged.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Locate the paragraph near the per-consumer gating statement and the Inline Promotion Path section.
2. Add: a consumer counts as attempting once it has a delivery record for the event, which its ACK or NACK creates; a consumer that has only received the event has no record and does not hold up promotion.
3. Add the consequence: while any attempting consumer is still below its retry limit, or any has ACKed, the event is not promoted.
4. Run the documentation checkers.

### Method
- Use the Edit tool on the affected paragraph only.

### Details
- Keep the anchors `#inline-promotion-path` and `#background-loop-promotion` unchanged, because `eventbus_03_dlq_operations.md` links to them.

## Compatibility considerations
- Documentation only; the described behavior matches the code after procedures 01 and 02.

## Security considerations
N/A: documentation only.

## Rollback considerations
Revert with `git revert` of the implementing commit, or `git checkout -- docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` before it is committed.

## Validation plan
- Run `tools/check_docs_quality.py`, `tools/check_docs_structure.py` with `--schema schemas/doc_front_matter.json`, `tools/check_docs_content_policy.py`, `tools/check_needs_confirmation_inventory.py`, and `tools/check_docs_consistency.py --domain overview` with explicit paths.

## Completion criteria
- The term is defined, the consequence is stated, the anchors are unchanged, and the checkers report no findings.

## Out of scope
- Other sections, the ADR, code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define the attempting consumer and its consequence | Completed | 20261012-105300 | 20261012-105300 | — Defined the attempting consumer and its consequence |
| 2 | Add or update tests per Validation plan | Completed | 20261012-105300 | 20261012-105300 | N/A: documentation only N/A: documentation only |
| 3 | Run the documentation checkers | Completed | 20261012-105300 | 20261012-105300 | — Documentation checkers no findings; anchors unchanged |

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
- **Related target files**: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md
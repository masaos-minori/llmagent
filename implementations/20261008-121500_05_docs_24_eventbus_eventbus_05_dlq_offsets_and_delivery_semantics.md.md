## Goal
Align the resume-position and Last-Event-ID text in the delivery-semantics document with the single replay predicate (REQ-005 of the Plan).

## Scope
- Edit the resume, since_seq precedence, and Last-Event-ID text only.

## Assumptions
- The route fix and tests have landed before this edit.

## Design decisions
- State that the resume position is the first sequence to deliver and that replay converts it to the exclusive bound; since_seq=N returns seq greater than N; Last-Event-ID L resumes at L+1.

## Alternatives considered
- Duplicating the pseudo-code from the other document: rejected; reference it.

## Implementation
### Target file
docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md

### Procedure
1. Read the resume position, since_seq precedence, and Last-Event-ID sections.
2. Edit the sentences so they match the single predicate and the other document.
3. Run the doc checkers.

### Method
Unique-text edits.

### Details
Keep the existing resume-position definition (lowest unacked seq at or below the stored offset, otherwise the stored offset plus one) and add that the first event delivered on reconnect is exactly that position.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The two documents agree on the predicate and the resume rule (REQ-005).

## Out of scope
- Other sections and ADRs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the resume and Last-Event-ID text | Completed | 20261008-122614 | 20261008-122614 |  |
| 2 | Run the doc checkers | Completed | 20261008-122614 | 20261008-122614 |  |

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
- **Requirement ID**: REQ-005 (documentation)
- **Source issue**: issues/20261007-164638_ebresume01_fix-off-by-one-in-eventbus-subscribe-resume-position.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-120658_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-121500
- **Related target files**: docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md
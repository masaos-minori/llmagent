## Goal
Make the subscribe documentation state one replay predicate and the batch advance rule (REQ-005 of the Plan).

## Scope
- Edit the Reconnection and Replay phase text only.

## Assumptions
- The route fix and tests have landed before this edit.

## Design decisions
- Describe the rule once: replay delivers events with seq greater than an exclusive lower bound; since_seq is that bound, the resume position is converted to it, and Last-Event-ID L means events from L+1; batches advance from the last emitted seq.

## Alternatives considered
- Documenting implementation internals: rejected; keep intent and boundary behavior only.

## Implementation
### Target file
docs/24_eventbus/eventbus_03_dlq_operations.md

### Procedure
1. Read the Reconnection, Replay phase, and since_seq precedence text.
2. Edit the Replay phase paragraph and the precedence rules so they state the same predicate and the batch rule.
3. Run the doc checkers.

### Method
Unique-text edits of the affected sentences.

### Details
Phase 1 text: events after the lower bound are replayed in batches, each batch continuing after the last event sent, until fewer than a full batch remains. Reconnection text: Last-Event-ID L resumes with event L+1. Precedence pseudo-steps keep their order.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`.

## Completion criteria
- The document describes one predicate and the batch rule, consistent with the other EventBus document (REQ-005).

## Out of scope
- Other sections.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the replay and reconnection text | Completed | 20261008-122614 | 20261008-122614 |  |
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
- **Related target files**: docs/24_eventbus/eventbus_03_dlq_operations.md
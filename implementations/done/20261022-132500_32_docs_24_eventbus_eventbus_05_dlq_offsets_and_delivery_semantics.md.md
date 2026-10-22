## Goal
Remove the open decision about the file-based helpers and the link to the removed section, keeping the statement that `consumer_offsets` is the only resume source (REQ-005).

## Scope
- In: delete the section `### File-Based Offset Helpers: Open Decision` (about line 239) and rewrite the sentence at about line 237 so it no longer links to `eventbus_07_configuration-and-operations.md#legacy-offset-files`.
- Out: `cycle_failure_count` and `delivery_failure_count` wording (owned by `plans/20261022-130338_plan.md`).

## Assumptions
- The link target section is removed by seq 33; leaving the link would create a broken anchor (found in verification).
- Docs are English, current-specification-only: no history note, no counts.

## Design decisions
- The sentence becomes: `consumer_offsets` is the only source of a consumer's resume position; the service has no file-based offset store.
- Delete the open-decision section whole.

## Alternatives considered
N/A: documentation edit.

## Implementation
### Target file
`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure
1. Rewrite the `## Consumer Offset` paragraph (about line 237): keep the SQLite description, drop the link and the offset-file clause.
2. Delete `### File-Based Offset Helpers: Open Decision` and its two lines.
3. Run the docs checkers.

### Method
Text edit.

### Details
- Run `uv run python tools/check_docs_consistency.py --domain eventbus` to confirm no broken anchor remains after seq 33.

## Compatibility considerations
Documentation of current behavior only.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, and `check_docs_consistency.py --domain eventbus` pass; `rg "Open Decision|legacy-offset-files" docs/24_eventbus` returns no match.

## Completion criteria
- The helper decision section and the dead link are gone; the resume-source statement remains (REQ-005; Plan AC-5).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the consumer-offset paragraph and delete the open-decision section | Completed | 20261022-134045 | 20261022-134045 | Changed: see commit |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-134045 | 20261022-134045 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |

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
- **Requirement ID**: `REQ-005` (documentation of the removed helpers)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
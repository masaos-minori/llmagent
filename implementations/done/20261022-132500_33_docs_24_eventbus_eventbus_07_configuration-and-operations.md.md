## Goal
Remove the `offsets_dir` description by deleting the `## Legacy Offset Files` section (REQ-005).

## Scope
- In: delete the section (about lines 150-152) and one of the two surrounding `---` separators; check the file for any other `offsets_dir` mention (the key table or example, 1 reference counted).
- Out: the Delivery Operations section.

## Assumptions
- The section is linked from `eventbus_05_dlq_offsets_and_delivery_semantics.md` (seq 32 removes that link).
- Docs are English, current-specification-only.

## Design decisions
- Delete the section and keep exactly one `---` separator between the neighbors.

## Alternatives considered
N/A: documentation edit.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure
1. `rg -n offsets_dir docs/24_eventbus/eventbus_07_configuration-and-operations.md` and delete each mention (key table row or text).
2. Delete `## Legacy Offset Files` and its paragraph.
3. Run the docs checkers.

### Method
Text edit.

### Details
- Confirm `rg "Legacy Offset|legacy-offset" docs` returns no match after seq 32 and 33.

## Compatibility considerations
Documentation of current behavior only.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain eventbus` pass.

## Completion criteria
- The section and the key description are gone (REQ-005; Plan AC-5).

## Out of Scope
Every other file of the Plan (each has its own procedure document); ADR text (Plan UNK-01); deleting `/opt/llm/offsets` (Plan UNK-03); offset storage, monotonic advancement, ACK-advanced offsets, and resume computation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the key description and the Legacy Offset Files section | Completed | 20261022-134046 | 20261022-134046 | Changed: see commit |
| 2 | Run the documentation checkers named in `routing.md` Tools | Completed | 20261022-134046 | 20261022-134046 | Verified: tests/eventbus 324 passed, full suite 9649 passed; ruff, mypy, lint-imports, docs checkers pass |

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
- **Requirement ID**: `REQ-005` (documentation of the removed key)
- **Source issue**: `issues/20261022-124119_offhelper_remove-unused-file-offset-helpers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-125806_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-132500
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
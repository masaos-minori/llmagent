## Goal

Record the approval and cancellation boundaries for maintenance work in the trust-boundary document, and update the RAG vector command name it names (REQ-003: approval as an operation property; REQ-007: name matches behavior).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6); the approval and cancellation boundary text is R7-docs-generated (Phase 7)

- In scope: the trust boundary for the maintenance commands, including the row at `docs/91_security/security_01_architecture-and-trust-boundaries.md:229`.

## Assumptions

- The boundary itself does not change: the Agent layer still reaches `rag.sqlite` through `RagMaintenanceService`. What changes is how a run is authorized — through the registered operation's approval level rather than a user flag.

## Design decisions

- The approval boundary is described as a property of the operation, not of the caller, because that is the contract REQ-003 establishes.

## Alternatives considered

- N/A: leaving the flag-authorized description would contradict `tests/agent/commands/test_memory_rebuild_guard.py` (row 56).

## Implementation
### Target file
`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure
1. Update the maintenance trust-boundary text: approval levels `none`, `confirm`, `guard` decide whether a run may start, and `confirm`/`guard` go through the request-bound confirmation path.
2. State that a registered job can be cancelled at a progress callback, and that a `not_cancelable` operation is refused with a stated reason.
3. Replace the command name in the row at `:229` with the renamed form.

### Method

- Keep the existing table format; one description per boundary.

### Details

- N/A: no other section of the file changes.

### Companion test files

- None. This is a documentation row; its validation is the docs checkers.

## Compatibility considerations

- Part of the same release unit as the code rename; the docs-quality rule (row 35) flags the file if the name is left stale while the others are corrected.

## Security considerations

- This document is the record of the trust boundary; the change makes approval enforceable in prose as well as in code.

## Rollback considerations

- N/A: revert the Phase 6 commit for the name and the Phase 7 commit for the boundary text separately.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/91_security/security_01_architecture-and-trust-boundaries.md` | No finding |

## Completion criteria

- The document describes approval as an operation property, describes cancellation, and names only registered commands.

## Out of Scope

- The implementation of the guard, the Built-in Command Index row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the command name in the boundary table | Completed | 20261125-002740 | 20261125-002740 | Phase 6 Phase 6 (R6) part: the boundary row names /session rag-prune-vec. |
| 2 | Add the approval and cancellation boundary text | Completed | 20261125-003636 | 20261125-003636 | Phase 7 Phase 7 (R7) done: the new subsection states that approval levels none/confirm/guard decide whether a run may start, that a confirm or guard grant comes from the request-bound confirmation path, and that a registered job is interrupted at its next progress callback while a not_cancelable operation is refused with the recorded reason. |
| 3 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-003636 | 20261125-003636 | check_docs_quality, check_docs_structure and check_docs_content_policy report no finding. Deviation: check_docs_consistency has no security domain, so this file is covered by the quality and structure gates only. |

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
- **Requirement ID**: REQ-003 (approval levels as an operation property), REQ-007 (name matching behavior), REQ-010 (documentation reflects the implementation)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/91_security/security_01_architecture-and-trust-boundaries.md`
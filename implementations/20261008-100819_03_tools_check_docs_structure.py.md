## Goal
Raise the per-file size ceiling for the Known Issue ledger document in the structure checker so the checker accepts the document's new, owner-approved size (REQ-009 of the Plan: ceiling update).

## Scope
- Change one value in the `SIZE_EXCEPTIONS` mapping of the structure checker: the entry keyed by the ledger document's base name.
- Update the adjacent comment so it states the new acceptance date.

## Assumptions
- The new accepted size is the ledger document's size after the edits of rows 01 (28414 bytes at the time of writing); re-measure immediately before editing and use the actual byte count.
- The user approved raising the ceiling on 2026-10-08.
- The existing tests use only the first mapping entry, so they do not depend on this value.

## Design decisions
- Keep the existing policy "each ceiling equals the file's accepted size, so any further growth fails" rather than adding headroom.
- Do not change `MAX_SIZE` or the other exception.

## Alternatives considered
- Splitting the ledger into several documents: rejected here; it is a documentation restructuring that needs its own issue.
- Raising the global limit: rejected; it would weaken the check for every document.

## Implementation
### Target file
tools/check_docs_structure.py

### Procedure
1. Measure the ledger document: `wc -c docs/00_governance/governance_03_issue-and-uncertainty-management.md`.
2. In `SIZE_EXCEPTIONS`, replace the ledger entry's value with that byte count.
3. Update the comment line that records the acceptance date to include 2026-10-08.
4. Run the validation commands.

### Method
A single-line value edit plus a comment tweak; no logic change.

### Details
The mapping key stays the ledger document's file name. The comment should say the exception was re-accepted on 2026-10-08 after the inventory changed, without restating the numeric value.

## Compatibility considerations
- No behavior change for other documents; `check_size()` logic is untouched.
- The tool is listed in `tools/TOOL_DESCRIPTIONS.md`; no file is added or removed, so no description sync is needed.

## Security considerations
- None: a constant in a read-only checker.

## Rollback considerations
- Revert the one-line change; the checker then reports the ledger as oversized again.

## Validation plan
- `uv run ruff format tools/check_docs_structure.py` then `uv run ruff check tools/check_docs_structure.py`
- `uv run mypy tools/check_docs_structure.py`
- `uv run bandit tools/check_docs_structure.py`
- `uv run pytest tests/tools/test_check_docs_structure.py`
- `uv run python tools/check_docs_structure.py` (expect no size finding)
- `uv run python tools/check_tool_descriptions_sync.py`

## Completion criteria
- The ceiling equals the ledger document's current byte count and the structure checker reports no size finding for it (REQ-009).
- Lint, type, security checks and the tool's tests pass.

## Out of scope
- Any other checker, the global limit, the ledger content, or splitting the ledger.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the ceiling and comment | Completed | 20261008-101607 | 20261008-101607 |  |
| 2 | Run lint, type, security checks and tool tests | Completed | 20261008-101607 | 20261008-101607 |  |
| 3 | Run the structure checker and description sync | Completed | 20261008-101607 | 20261008-101607 |  |

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
- **Requirement ID**: REQ-009 (raise the ledger size ceiling)
- **Source issue**: issues/20261008-094504_kiupd01_register-new-known-issues-and-update-mcp-004-and-rag-002.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-100307_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-100819
- **Related target files**: tools/check_docs_structure.py
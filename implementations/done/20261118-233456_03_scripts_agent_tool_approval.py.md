## Goal

Remove the stale documentation reference at `scripts/agent/tool_approval.py:45` and point it at the
canonical approval documents (REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `grep -n 'docs/' scripts/agent/tool_approval.py` returns only line 45; the cited path
  `docs/05_agent_06_01_tool-execution-and-approval-execution.md` does not exist.

## Design decisions
- Cite `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` (canonical approval
  flow) and `docs/23_agent/agent_06_04_tool-execution-and-approval-canonical.md` (canonical
  terminology), matching the Plan `Problem` section's named canonical documents.

## Alternatives considered
N/A: documentation-only path fix.

## Implementation
### Target file
`scripts/agent/tool_approval.py`
### Procedure
Replace the document path in the comment at line 45 with the canonical paths above.
### Method
N/A: single-line comment change.
### Details
N/A: nothing beyond the path replacement is not inferable from REQ-006.

## Compatibility considerations
N/A: comment-only change.

## Security considerations
N/A: comment-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_preflight.py tests/agent/test_tool_approval_paths.py -q` (unchanged behavior).
- `uv run python tools/check_docs_consistency.py --domain agent` confirms no source file cites a
  non-existent document path (AC-006).

## Completion criteria
No citation of a non-existent document path remains in the file; approval tests pass unchanged.

## Out of Scope
Any behavior change in the approval gate.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the stale document path per Procedure | Completed | 20261119-072741 | 20261119-072741 | Stale path confirmed absent; replaced with the two canonical doc paths |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-072741 | 20261119-072741 | ruff check pass; 82 approval tests pass unchanged; check_docs_consistency --domain agent clean |

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
- **Requirement ID**: `REQ-006` (remove the stale documentation reference)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `scripts/agent/tool_approval.py`

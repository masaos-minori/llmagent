## Goal
State that the posture gate is enforced in the common start path for every launch route (`REQ-005`).

## Scope
- One or two sentences in the security-posture section near the paragraph that describes the Agent's reading of `/health` (lines 56-58).

## Assumptions
- The document has high churn (21 commits in 30 days); keep the edit minimal and rebase before committing.
- The shell document's claim that an independently started shell-mcp refuses to bind becomes accurate and is not edited.

## Design decisions
- Describe boundaries and failure behavior, not the method names (`skills/DESIGN.md` Avoid implementation-reference duplication).

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Procedure
1. After the sentence about `warning` and `failed` checks add: a server refuses to bind (exit status 1) when its posture is not validated, and this check runs in the common start path used by the Agent-launched binaries, `mcp_launcher.py` and `python -m`, so no launch route skips it.

### Method
- Edit the existing paragraph; no new section, table or code block.

### Details
- English only; do not hardcode other document filenames.

## Compatibility considerations
- N/A: documentation-only.

## Security considerations
- N/A: describes an existing control.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`.

## Completion criteria
- The enforcement point is stated and the docs checkers pass.

## Out of Scope
- Other MCP documents
- ADR changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the documentation edit per Implementation > Procedure | Completed | 20261023-125626 | 20261023-125626 | implemented; targeted tests passed (tests/mcp_servers, startup, binaries: 2516 passed); full suite run at the end of the batch |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261023-125626 | 20261023-125626 |  |

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
- **Requirement ID**: `REQ-005` (document the enforcement point)
- **Source issue**: issues/20261023-114021_mcpstart002_posture-gate-bypassed-by-launchers-and-mdq-main.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-114842_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123153
- **Related target files**: docs/22_mcp/mcp_02_02_startup-modes-and-health.md
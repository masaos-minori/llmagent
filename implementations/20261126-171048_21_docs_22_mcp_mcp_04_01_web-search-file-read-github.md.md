## Goal
- Record the symlink-exclusion policy and the traversal limits as failure behavior in the file-read documentation section (REQ-008, AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the file-read section of `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` — add the symlink-exclusion policy and the traversal-limit failure behavior.
- Out of scope: the final consistency sweep of this document, which remains mcpai012's work (Plan Assumptions, judged compatible); the implementation (seq 07, 08).

## Assumptions
- Verified in Step 2: the file-read section describes size and result limits only, with no symlink or traversal-limit policy.
- Overlap with mcpai012 on this file is judged compatible: this document records the facts this Plan establishes; mcpai012 sweeps afterward.
- Documentation is written in English per `skills/DESIGN.md` Output language.

## Design decisions
- The section states the policy as failure behavior: symlink entries are excluded from traversal results, and each limit stop reports a structured truncation reason (`node_limit`, `scanned_file_limit`, `byte_limit`, `deadline`).
- Only the task-scope section mapped in `docs/00_index.md` is edited; other sections of the file are untouched.

## Alternatives considered
- N/A: documentation row with no design decision of its own.

## Implementation
### Target file
`docs/22_mcp/mcp_04_01_web-search-file-read-github.md`

### Procedure
1. In the file-read section, add the symlink-exclusion policy (default exclusion, no opt-in) and the traversal limits with the structured truncation reason.

### Method
- Match the existing section style (policy statements with the enforcing config field names and defaults from seq 01).

### Details
- Cite the plan defaults: `max_tree_nodes=2000`, `max_scanned_files=5000`, `max_total_scan_bytes=10485760`, `traversal_deadline_sec=10.0`.

## Compatibility considerations
- N/A: documentation only; the facts describe behavior established by seq 07, 08.

## Security considerations
- N/A: no secrets; the policy statement documents the symlink-escape closure.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` (structural/formatting rules per `rules/tool-gates.md`); docs consistency checker per the same table.

## Completion criteria
- The file-read section records the symlink policy and traversal-limit failure behavior; the docs checkers pass (AC-6).

## Out of Scope
- The consistency sweep reserved to mcpai012; implementation (seq 07, 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the docs checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` (documentation records the facts this Plan establishes)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`

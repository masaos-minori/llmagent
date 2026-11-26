## Goal

Describe the lifecycle ownership contract in the runtime architecture doc (REQ-012).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 6 is outside R3-ownership)

## Assumptions
- The doc is named by `docs/00_index.md:164` for `HttpServerLifecycleManager / http_lifecycle.py` (Plan Documentation Impact).

## Design decisions
- Update the existing `LifecycleState` description to the record-ownership contract; no new section beyond what the state machine change requires.

## Alternatives considered
- N/A: the docs mapping fixes the target file.

## Implementation
### Target file
`docs/23_agent/agent_02_runtime-architecture.md`

### Procedure
State that one `ManagedProcessRecord` (new, row 02) owns process, pid, pgid, stderr log, state, and last outcome, released only on confirmed exit, and that shutdown and restart follow per-server outcomes.

### Method
Prose update in the existing lifecycle section; keep the doc's structure and Keywords section.

### Details
- Cross-reference the MCP doc (row 19) rather than duplicating the full state table.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` per `rules/tool-gates.md`.

## Completion criteria
- The architecture doc states the single-record ownership contract and per-server outcome states; both doc checkers pass.

## Out of Scope
- The generated reference artifacts (rows 21-23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-132800 | 20261126-132447 | LifecycleState enum/transition list updated to the landed table; ownership paragraph added in Lifecycle Implementation with cross-reference to mcp_03_04; shutdown-guard sentence corrected (suppression errors now raised) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-132900 | 20261126-132447 | Docs row: `check_docs_quality.py` and `check_docs_structure.py` check_docs_quality: no issues; check_docs_structure: all checks passed |

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
- **Requirement ID**: REQ-012 (documentation of the ownership contract)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `docs/23_agent/agent_02_runtime-architecture.md`
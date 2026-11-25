## Goal
Document the execution modes, the context contract, and the key rule (REQ-011), and correct the sentence that says dry-run results are never cached.
## Scope
**Release unit**: N/A: not part of a release unit
## Assumptions
- Documentation is written in English (`skills/DESIGN.md` output language); the final sweep of the MCP design documents stays with the separate documentation work item.
- The edit lands after the code procedures so the text describes final behavior.
## Design decisions
- One new subsection next to the idempotency text; replace line 68's marker-era sentence rather than appending a contradicting one.
## Alternatives considered
N/A: docs-only row.
## Implementation
### Target file
`docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
### Procedure
Edit the idempotency part of the document.
### Method
- Replace the sentence that says error and dry-run results are never cached with: errors are never cached; a preview executes no dedup acquisition and leaves no durable or overlay state.
- Add a subsection defining `preview`, `applied`, no_op, `side_effect_applied`, how the mode is resolved (declared `preview_capability` plus a boolean `dry_run`), and the `X-Execution-Mode` header cross-check.
- State that every side-effecting dispatch, HTTP or programmatic, needs a key and that a keyless one is rejected with idempotency_key_required.
### Details
- Run the documentation checkers listed in `rules/tool-gates.md` (via `tools/run_validation_gates.py`).
## Compatibility considerations
N/A: docs-only.
## Security considerations
N/A: docs-only.
## Rollback considerations
N/A: revert the commit.
## Validation plan
- `uv run python tools/run_validation_gates.py`
## Completion criteria
- The document matches the implemented contract and the gates pass.
## Out of Scope
- Other MCP design documents (final sweep item).
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — |  |
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
- **Requirement ID**: REQ-011
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`

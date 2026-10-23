## Goal
State when `restrict_to` takes effect for each launch path instead of saying only that `run_http()` calls it before uvicorn starts (`REQ-006`).

## Scope
- Edit the sentence at line 26 (`MCPServer.run_http()` calls `ConfigLoader.restrict_to(own_config_file)` before starting uvicorn).

## Assumptions
- Keep the edit to one or two sentences; the document is part of the high-churn MCP set.

## Design decisions
- Describe boundaries and failure behavior: binaries and `mcp_launcher.py` restrict before importing the server module; `python -m` is a development path that restricts in `run_http()`; a server never imports another server.

## Alternatives considered
- N/A: documentation-only row.

## Implementation
### Target file
`docs/22_mcp/mcp_06_01_configuration-file-inventory.md`

### Procedure
1. Rewrite the line 26 sentence to give the three launch paths and the no-cross-import rule.

### Method
- Edit existing text; no new section, table or code block.

### Details
- English only; do not list per-server config names.

## Compatibility considerations
- N/A: documentation-only.

## Security considerations
- N/A: describes an enforced control.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`, `check_docs_japanese.py`.

## Completion criteria
- The document matches the implemented isolation timing and the checkers pass.

## Out of Scope
- ADR-002 text
- Other MCP documents

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the documentation edit per Implementation > Procedure | Completed | 20261023-130632 | 20261023-130632 | implemented; tests/mcp_servers + startup + tools: 3631 passed; full suite run at the end of the batch; Nuitka rebuild not run (plan Phase 5) |
| 2 | Run the documentation checkers named in `routing.md` Tools "When to run which tool" | Completed | 20261023-130632 | 20261023-130632 |  |

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
- **Requirement ID**: `REQ-006` (document when isolation takes effect)
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: docs/22_mcp/mcp_06_01_configuration-file-inventory.md
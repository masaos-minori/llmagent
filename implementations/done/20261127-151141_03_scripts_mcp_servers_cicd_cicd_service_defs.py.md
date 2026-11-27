# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_defs.py

## Goal

Declare `get_workflow_logs` in the `CiBackend` Protocol as returning the structured log result, so the
composite facade and the handler are typed against the new contract.

## Scope
**Release unit**: structured log result contract

Requirement implemented: REQ-004 (the Protocol carries the structured result). Acceptance criterion:
AC-4.

## Assumptions
- The result model is defined by the `cicd_models.py` row; this document only changes the Protocol
  signature.
- The Protocol is read by the service, the composite facade, and the init factory, so the signature
  change must land with the backend, facade, and handler rows in the same release unit.

## Design decisions
- Only the return annotation changes; the method name, parameters, and the constants in this module
  (`_GITHUB_API_BASE`, `_MAX_JOBS_FOR_LOGS`, `build_auth_headers`) stay unchanged.

## Alternatives considered
- Keeping `-> str` and serializing inside the Protocol layer: rejected — the Protocol is the typed
  contract the facade and handler are checked against, and the Plan's Error carrier decision requires a
  machine-distinguishable result.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_defs.py`

### Procedure
- Change `async def get_workflow_logs(self, owner: str, repo: str, run_id: int) -> str` at line 65 to
  return the log result model from the models row.

### Method
- Line 65 is the Protocol declaration the composite backend and the handler are typed against
  (re-verified 20261127); no other Protocol member changes. The module already imports from
  `cicd_models` (`DispatchOutcome`, added by the mcpci002 pass), so the log result model is added to
  that existing import rather than a new import path.

### Details
- N/A: no behavior change in this module.

## Compatibility considerations
- The tool inventory and the request schema shape are unchanged, so
  `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` (reference, not modified) must still
  pass with the new signature.

## Security considerations
- N/A: type contract only.

## Rollback considerations
- N/A: revert the commit (release unit: validated with the backend, facade, and handler rows).

## Validation plan
- Unit: Protocol contract — `uv run pytest tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`
  (reference file, not modified).
- Full sequence per `rules/toolchain.md`, including the import-linter contract that keeps this module
  inside `mcp_servers`.

## Completion criteria
- The Protocol signature matches the backend and the tool inventory is unchanged (AC-4).

## Out of Scope
- The response model (`cicd_models.py` row); the delegation (`cicd_service_github_actions_composite.py`
  row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | CiBackend.get_workflow_logs annotation changed to LogFetchResult |
| 2 | Add or update tests per Validation plan | N/A | — | — | the covering test is a reference file, not a modification target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy Pass; lint-imports Pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs row |

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
- **Requirement ID**: REQ-004 (the `CiBackend` Protocol returns the structured log result)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_defs.py`
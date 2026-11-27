# Implementation Procedure — scripts/mcp_servers/cicd/cicd_server.py

## Goal

Register the workflow-dispatch reconciler at the control-API registry seam so response-loss recovery
answers from recorded evidence instead of re-executing the call.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-004 (recovery searches for the original run before dispatching again),
REQ-007 (the run lookup implements the shared `Reconciler` contract and is registered at the seam).
Acceptance criterion: AC-3.

## Assumptions
- The run lookup itself is implemented in the `cicd_service_github_actions.py` row; this document only
  registers it.
- The control plane is already attached for cicd-mcp through `MCPServer`
  (`scripts/mcp_servers/server.py:226-228`, `433-439`, reference), so no new wiring is needed.
- The lifespan and health changes on this same file belong to the mcpci001 pass (compatible overlap);
  this document adds registration only.

## Design decisions
- Registration uses `register_reconciler(tool_name, reconciler)` from `scripts/mcp_servers/control_api.py`
  (line 84, reference) with the tool name `trigger_workflow`, the entry `CICD_WRITE_TOOLS` already pins
  (`scripts/shared/tool_constants.py:76`, reference).
- Evidence is recorded as a non-sensitive digest per `ReconcileEvidence`
  (`scripts/shared/mcp_call_state_contract.py`, reference); no raw payload is stored.

## Alternatives considered
- Registering inside the service construction path: rejected — the registry seam is the control-API
  module, and the service layer must not know about the control plane.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_server.py`

### Procedure
- Call `register_reconciler("trigger_workflow", <run lookup>)` with the reconciler implemented by the
  backend row, at the point where the control API is attached to this server.
- Bind the call identity around the dispatch in `call_tool` with a ContextVar (the precedent is
  `bind_call_identity`, `scripts/mcp_servers/github/github_service_security.py:66-80`), so the
  backend can record the correlation keyed by `call_key`; the handler contract stays `-> str`
  (Plan Design decision, amended 20261127).

### Method
- No production `register_reconciler` call exists in this module (re-verified 20261127); add the call
  after the app is created, keeping the existing gate and health behavior unchanged.

### Details
- `trigger_workflow` stays explicitly non-retryable; accepted_unconfirmed and `outcome_unknown` are
  never retried automatically (REQ-005, pinned by `tests/shared/test_tool_constants.py:156-164`,
  reference).

## Compatibility considerations
- The tool inventory and the routing entry are unchanged, so `tools/TOOL_DESCRIPTIONS.md` is not
  affected (Plan Predictable fallout check).

## Security considerations
- The reconciler answers from the recorded digest without re-executing the external call (AC-3).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit: reconciler registration seam — `uv run pytest tests/mcp_servers/test_call_state_api.py`
  (reference file, not modified).
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The registered reconciler answers without re-executing the call (AC-3); the recovery path searches
  for the original run before dispatching again.

## Out of Scope
- The run lookup implementation (`cicd_service_github_actions.py` row); the lifespan and health
  (mcpci001).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-222044 | register_reconciler("trigger_workflow", dispatch_reconciler) and ContextVar call-identity bind in call_tool |
| 2 | Add or update tests per Validation plan | N/A | — | — | the covering test is a reference file, not a modification target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261127-222044 | ruff/mypy/lint-imports/bandit/pre-commit pass; covered by tests/mcp_servers/test_mcp_dispatch.py and the cicd suite (317 passed) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs row |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | `reconcile` is sync and the snapshot carries no call arguments; the correlation is recovered from an in-process record keyed by `call_key`, read through a ContextVar call-identity bind added to `call_tool` (Plan Design decision, amended 20261127, user decision) | Yes | 20261127 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-007 (reconciler registration at the control-API seam)
- **Source issue**: issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-005001_mcpci002_cicd-dispatch-reconciliation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-150154
- **Related target files**: `scripts/mcp_servers/cicd/cicd_server.py`
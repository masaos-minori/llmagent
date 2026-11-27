# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py

## Goal

Carry the structured log result through the composite facade instead of a plain string.

## Scope
**Release unit**: structured log result contract

Requirement implemented: REQ-004 (the delegation returns the structured log result). Acceptance
criterion: AC-4.

## Assumptions
- The result model is defined by the `cicd_models.py` row; this document only passes it through.
- The facade keeps its current responsibility: delegation, no policy of its own.
- The `trigger_workflow` delegation in the same file is the mcpci002 pass's work; this document changes
  the log delegation only (Plan Assumption, compatible overlap).

## Design decisions
- The return annotation changes from `str` to the log result model from the models row; no other
  behavior in the facade changes.

## Alternatives considered
- Serializing to JSON inside the facade: rejected — serialization stays at the handler boundary, so the
  facade remains a pass-through and the release unit's tests compare the same object.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`

### Procedure
- Change `get_workflow_logs` (lines 80-82) to return the structured log result from the job backend
  unchanged, with the response-model annotation.

### Method
- Lines 80-82 delegate to `self._job.get_workflow_logs(...)` and return its value unchanged
  (re-verified 20261127); only the annotation and the pinned test expectation change.

### Details
- N/A: no other behavior in this file changes.

### Companion test files
- `tests/mcp_servers/cicd/test_service_github_actions_composite.py`
  - Procedure: replace the pinned string contract at lines 151 and 155
    (`return_value = "=== Job: build ==="` and the returned string; re-verified 20261127, the Plan's
    citation of 146-151 predates the mcpci002 pass) with the structured log result and assert the
    object passes through unchanged.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_composite.py`.

## Compatibility considerations
- Callers that read the handler's JSON string are unaffected because serialization stays at the handler
  boundary (Plan Assumption).

## Security considerations
- N/A: pass-through only.

## Rollback considerations
- N/A: revert the commit (release unit: validated with the Protocol, backend, and handler rows).

## Validation plan
- Unit: delegation — `uv run pytest tests/mcp_servers/cicd/test_service_github_actions_composite.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The structured log result passes through unchanged (AC-4).

## Out of Scope
- Producing the result (`cicd_service_github_actions_job.py` row); the dispatch delegation (mcpci002).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | pass-through returns the structured result unchanged |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | — | — | delegation pin replaced by the structured-result pass-through |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy Pass; test_service_github_actions_composite.py passes |
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
- **Requirement ID**: REQ-004 (structured log result through the composite delegation)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_github_actions_composite.py`, `tests/mcp_servers/cicd/test_service_github_actions_composite.py`
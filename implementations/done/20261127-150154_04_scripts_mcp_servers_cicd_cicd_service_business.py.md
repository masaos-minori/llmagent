# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_business.py

## Goal

Return the structured dispatch outcome from `handle_trigger_workflow` and emit input keys and counts
only in the dry-run preview, so workflow input values never appear in previews, logs, or recovery
output.

## Scope
**Release unit**: structured-state contract

Requirements implemented: REQ-001 (the handler returns the structured outcome), REQ-006 (input values
redacted from previews). Acceptance criteria: AC-2, AC-4.

## Assumptions
- The handler contract stays `-> str` with the outcome JSON-serialized, so `dispatch_tool` and the
  audit `outcome` mapping are unchanged (Plan Assumption).
- Canonicalization of `req.workflow` and `req.repo` is the mcpci001 pass's work on this same file;
  this document does not restate it (compatible overlap recorded in the Plan's Assumptions).
- The audit record carries no raw arguments (`scripts/mcp_servers/audit.py`, reference), so redaction
  applies to previews and recovery output only.

## Design decisions
- The preview emits the input key names and the count, never the values, per REQ-006.
- Recovery output uses the same keys-and-counts form, so no path prints a value.

## Alternatives considered
- Redacting at the logging layer: rejected — REQ-006 names the preview as the producer, and the
  recovery service reads the same preview text.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_business.py`

### Procedure
- Change `handle_trigger_workflow` to return the JSON-serialized structured outcome from the backend.
- Replace the preview string at lines 98-100 so it lists input keys and the count instead of
  `with inputs={req.inputs}`.

### Method
- Lines 98-100 currently embed raw input values in the preview (re-verified 20261127 against the
  current file; the Plan's citation of 70-75 predates the mcpci001 pass); keep the dry-run
  flag and the preview shape, change only the inputs part.

### Details
- Newly changed output: the preview text for a dry run with inputs. Values that contain no inputs are
  unchanged.

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
  - Procedure: replace the immediate-success tests at lines 240-246
    (`assert result == "dispatched"`) with the structured-state contract, and add the preview-redaction
    tests asserting input values are absent and keys and counts are present. (The Plan's citation of
    201-208 predates the mcpci001 pass; re-verified 20261127.)
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py`.

## Compatibility considerations
- Clients that parse the handler's JSON string gain the state field; the tool name and the dispatch
  table entry are unchanged (`tests/mcp_servers/cicd/test_cicd_server_endpoints.py:224`, reference).

## Security considerations
- Input values are absent from previews, logs, and recovery messages (AC-4).

## Rollback considerations
- N/A: revert the commit (release unit: validated with the backend and composite rows).

## Validation plan
- Unit: handler and preview redaction — `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Input values do not appear in the preview (AC-4); the handler returns the structured outcome (AC-2).

## Out of Scope
- The response model (`cicd_models.py` row); reconciler registration (`cicd_server.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261127-222044 | canonicalization is the mcpci001 procedure for this file handler JSON output + await; preview redacted to input keys and count only (inputs [N]: keys) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | — | 20261127-222044 | tests/mcp_servers/cicd/test_cicd_mcp_service.py: immediate-success pins replaced, redaction tests added, _no_runs_found helper with shortened polling window |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261127-222044 | ruff/mypy/lint-imports/bandit/pre-commit pass; cicd suite 317 passed; end-of-unit gates as recorded in the release unit |
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
- **Requirement ID**: REQ-001, REQ-006 (structured outcome from the handler, preview redaction)
- **Source issue**: issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-005001_mcpci002_cicd-dispatch-reconciliation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-150154
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_business.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
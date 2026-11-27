# Implementation Procedure — tests/mcp_servers/cicd/test_cicd_models.py

## Goal

Add the log response-model shape tests for the per-job fields, partial_success, and the totals, and
keep the request-schema pins and the config cross-check passing.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-004, REQ-005 (response-model shape), REQ-002 (the documented limits match
the constants through the config cross-check). Acceptance criteria: AC-1, AC-4.

## Assumptions
- This row keeps its own document because it is cited by two Plan rows (`cicd_models.py` and
  `config/cicd_mcp_server.toml`), so it fails the companion condition of exactly one citing row.
- The assertions describe the behavior defined by the `cicd_models.py` row; this document changes no
  production code.
- The mcpci002 pass adds the dispatch response-model shape tests to this same file; this document adds
  the log response tests only (Plan Assumption, compatible overlap).

## Design decisions
- Keep the request-schema pins at lines 36-104 as the characterization baseline (re-verified 20261127;
  the Plan's citation of 35-54 covers only the first pin); add the response shape
  tests rather than replacing them.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/cicd/test_cicd_models.py`

### Procedure
- Add the response-model shape tests for the per-job fields (status, included bytes, error code,
  truncation state), partial_success, and the totals.
- Add the limit-constant assertions so the documented values in `config/cicd_mcp_server.toml` are
  compared with the module constants.

### Method
- Lines 36-104 pin the request schema shape only (re-verified 20261127; the Plan's citation of 35-54
  covers only the first pin); keep one test per pinned fact
  and add the response-shape tests after them.

### Details
- N/A: no production behavior is defined here.

## Compatibility considerations
- N/A: tests only.

## Security considerations
- N/A: tests only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/cicd/test_cicd_models.py`; full sequence per `rules/toolchain.md`.

## Completion criteria
- The per-job fields, partial_success, and the totals are pinned (AC-4); the documented config values
  equal the constants (AC-1).

## Out of Scope
- The model changes themselves (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | response-model shape tests and the limit-constant assertions added |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | 65 tests pass; ruff Pass; check_test_taxonomy clean |

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
- **Requirement ID**: REQ-002, REQ-004, REQ-005 (log response-model shape and limit constants)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `tests/mcp_servers/cicd/test_cicd_models.py`
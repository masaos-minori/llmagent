# Implementation Procedure — tests/mcp_servers/cicd/test_cicd_models.py

## Goal

Re-pin the schema shape after `extra="forbid"`, the new constraints, canonicalization, and the hard maximums, and add the newly rejected input cases.

## Scope
**Release unit**: N/A: not part of a release unit

Requirements implemented: REQ-004, REQ-005, REQ-006, REQ-007 (model and schema parity, canonicalization, allowlist bounds). Acceptance criteria: AC-3, AC-5.

## Assumptions
- This row keeps its own document because it is cited by two Plan rows (`cicd_models.py` and `config/cicd_mcp_server.toml`), so it fails the companion condition of exactly one citing row.
- The assertions describe the behavior defined by the `cicd_models.py` row; this document changes no production code.

## Design decisions
- Keep the characterization tests at lines 34-45 and 153-170 as the pin, updated to the new shape rather than replaced.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/cicd/test_cicd_models.py`

### Procedure
- Re-pin the schema-shape assertions (lines 34-45) for `extra="forbid"` and the moved descriptions.
- Re-pin the config-parsing assertions (lines 153-170) for the hard maximums and normalization.
- Add cases for the newly rejected inputs: extra request fields, blank `repo`/`workflow`/`ref`, `limit` outside 1..50, `run_id` below 1, wildcard allowlist entries, oversized allowlist entries, `max_log_size_kb` below 1 or above 1024.

### Method
- The current pins assert descriptions, defaults, and parsed values (verified in Step 3a); update the expected values to the model-generated schema, keeping one test per pinned fact.

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
- The published schema equals the model schema (AC-3) and the newly rejected inputs are asserted (AC-5).

## Out of Scope
- The model changes themselves (`cicd_models.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005, REQ-006, REQ-007 (re-pinned schema shape and rejected inputs)
- **Source issue**: issues/20261119-141106_mcpci001_cicd-credential-config-contract.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-152931_mcpci001_cicd-credential-config-contract.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-145310
- **Related target files**: `tests/mcp_servers/cicd/test_cicd_models.py`

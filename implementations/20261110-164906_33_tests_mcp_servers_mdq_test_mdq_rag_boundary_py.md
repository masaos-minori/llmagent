## Goal

Rename the allowed shared-module import entry from the deleted eventbus module to the
generalized module (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/shared/eventbus_schema_fingerprint.py` is deleted and replaced by
  `scripts/shared/schema_fingerprint.py` (row 2); the boundary test's allowlist must point
  at the new module.

## Design decisions
- Swap only the allowlisted filename; the test logic is unchanged.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_rag_boundary.py`

### Procedure
1. Line 74: replace `"eventbus_schema_fingerprint.py",` with `"schema_fingerprint.py",`
   in the `ALLOWED` set.
2. Update the inline comment at line 71-72 ("Shared EventBus schema-shape validator") to
   describe the domain-neutral generalized validator.

### Method
- Confirm the allowlist entry with
  `rg -n 'eventbus_schema_fingerprint|ALLOWED' tests/mcp_servers/mdq/test_mdq_rag_boundary.py`
  before editing.

### Details
- The allowlist guards `scripts/shared/` direct MDQ/RAG access; the generalized module
  opens only in-memory databases and caller-passed connections, so it remains a valid
  exception.

## Compatibility considerations
None; the test still validates the same boundary.

## Security considerations
None beyond the existing allowlist review contract.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/mcp_servers/mdq/test_mdq_rag_boundary.py -v` passes.

## Completion criteria
The allowlist names `schema_fingerprint.py`; the deleted module name no longer appears.

## Out of Scope
Changing the boundary logic itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the allowed import entry to the generalized module | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` — rename the allowed import entry
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`

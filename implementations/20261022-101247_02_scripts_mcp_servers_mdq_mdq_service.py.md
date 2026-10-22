## Goal
Fix the `MdqService._init_db()` docstring so it no longer mentions migrating from a legacy schema (REQ-002).

## Scope
- One docstring line; no code change.

## Assumptions
- `_init_db()` calls `create_production_tables()` only; after the sibling change that function creates the tables and does not migrate (verified in `_init_db()`).

## Design decisions
- New docstring: "Create the production tables."

## Alternatives considered
N/A: one-line docstring edit.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
1. Replace "Create production tables and migrate from legacy schema if needed." with "Create the production tables."

### Method
- Edit the docstring only; do not touch the body.

### Details
- The module docstring format check (baseline-gated) must still pass.

## Compatibility considerations
N/A: docstring only.

## Security considerations
N/A: docstring only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run ruff check scripts/`, `uv run python tools/check_docstrings.py`.

## Completion criteria
- No docstring in the file mentions legacy migration.

## Out of Scope
- Any code in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix the `_init_db()` docstring | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` (docstring no longer mentions legacy migration)
- **Source issue**: `issues/20261021-102212_rmmdqmig_remove-the-mdq.sqlite-legacy-chunks-rebuild.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094132_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101247
- **Related target files**: scripts/mcp_servers/mdq/mdq_service.py

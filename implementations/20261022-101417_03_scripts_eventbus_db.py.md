## Goal
Remove the re-export of `migrate_legacy_offsets` and its `__all__` entry from the `eventbus.db` facade (REQ-001).

## Scope
- One import line, the `# Offset migrator` comment, and the `__all__` entry in `scripts/eventbus/db.py`.

## Assumptions
- The facade is imported by routes and tests; after removal no importer uses the name (the only non-test importer is `app.py`, changed by its own procedure; the tests of the import are removed).

## Design decisions
- Remove the comment group together with its single entry so `__all__` has no empty section.

## Alternatives considered
N/A: removal required by the Plan.

## Implementation
### Target file
`scripts/eventbus/db.py`

### Procedure
1. Delete `from eventbus.offset_migrator import migrate_legacy_offsets`.
2. Delete the `# Offset migrator` comment and `"migrate_legacy_offsets",` from `__all__`.

### Method
- Apply after the `app.py` procedure and before deleting the module.

### Details
- Keep the remaining re-exports and their order.

## Compatibility considerations
The facade loses one name that has no remaining caller.

## Security considerations
N/A: re-export removal.

## Rollback considerations
Revert the commit.

## Validation plan
- `uv run pytest tests/eventbus -q`; `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run python tools/generate_reference_table.py --check` (the facade feeds the reference block; regeneration is done in the docs procedure).

## Completion criteria
- The file names neither the module nor the function.

## Out of Scope
- Other re-exports.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the import, comment, and `__all__` entry | Pending | — | — | |
| 2 | Tests are covered by the test-file procedure | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (remove the re-export)
- **Source issue**: `issues/20261021-102244_rmoffimp_remove-the-legacy-offset-import.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-094316_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-101417
- **Related target files**: scripts/eventbus/db.py

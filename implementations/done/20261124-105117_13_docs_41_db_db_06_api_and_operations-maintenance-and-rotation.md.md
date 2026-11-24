## Goal
Describe `prune_old_memories` as removal-pending instead of a supported maintenance operation (REQ-003).

## Scope
**Release unit**: terminology-sweep

- Edits only `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`; applied with the other documents of the release unit because the documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it or to `agent_09_01` instead of restating it.
- Where code still implements the retired feature the document cites SHARED-003, and where policy is undecided it cites SHARED-004; no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Only the retired-feature descriptions named in Procedure change; valid names such as the `agent/memory/` path, the `USER MEMORY` snippet framing, and the retrieval mode labels stay.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.

## Design decisions
- Edit one bullet and one sentence.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`

### Procedure
1. Replace the `prune_old_memories` bullet with: it is retired with the `/memory prune` command and removal-pending (SHARED-003); it is not a supported maintenance operation.
2. Change "Each of `vacuum_db`, `purge_old_sessions` and `prune_old_memories` takes a `MaintenanceMode`" to name `vacuum_db` and `purge_old_sessions` only.

### Method
- Use the Edit tool.

### Details
- The function still exists in code; do not describe its effect.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_consistency.py --domain db`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The maintenance list names only supported operations plus the removal-pending note.

## Out of Scope
- Any other file, code, configuration, generated references, and manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-110725 | 20261124-110725 | Changed: 41/db_db_06_api_and_operations-maintenance-and-rotation |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261124-110725 | 20261124-110725 | Release unit terminology-sweep eight consistency domains, docs structure/quality/content-policy, ADR checks, known-deviation sync, needs-confirmation inventory, reference and authority drift, DB separation, 75 cited ADR tests and 117 tests pass; preservation findings on the ADR-004 label are intended |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-104416_adrdoc004_docs-regenerate-cross-validate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-105117
- **Related target files**: `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`
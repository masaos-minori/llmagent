## Goal
Update the ADR-008 label in the Related ADRs list within the file's size headroom (REQ-004).

## Scope
**Release unit**: terminology-sweep

- Edits only `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`; applied with the other documents of the release unit because the documents cross-link and are validated together.

## Assumptions
- The amended ADR-008 (Decision Details 22 to 25, INV-20 to INV-22) is the contract; the document links to it or to `agent_09_01` instead of restating it.
- Where code still implements the retired feature the document cites SHARED-003, and where policy is undecided it cites SHARED-004; no `Needs Confirmation` marker is added, because unregistered markers fail `tools/check_needs_confirmation_inventory.py`.
- Only the retired-feature descriptions named in Procedure change; valid names such as the `agent/memory/` path, the `USER MEMORY` snippet framing, and the retrieval mode labels stay.
- Before removing or renaming a heading, search for links to its anchor (`rg -n "#<anchor>" docs`) and keep or update them in the same edit set.

## Design decisions
- One bullet; the label is short because the file has 19 bytes of headroom under its size ceiling.

## Alternatives considered
N/A: documentation only; the Plan fixes the approach.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure
1. Replace "ADR-008: SQLite Four-Database Separation" with "ADR-008: Six SQLite Stores: Separation and Lifecycle", keeping the rest of the bullet.

### Method
- Use the Edit tool; confirm with `wc -c` that the file grows by at most 19 bytes (36248 now, ceiling 36267).

### Details
- Do not change the ceiling in `tools/check_docs_structure.py`.

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no security-relevant change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_reference.py`; `uv run python tools/check_docs_structure.py`.
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_content_policy.py`.

## Completion criteria
- The label names six stores; the size check passes.

## Out of Scope
- Any other file, code, configuration, generated references, and manifests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the document per Implementation | Completed | 20261124-110725 | 20261124-110725 | Changed: 10/adr_adr_02_01_004_platform-environment-failure-handling-policy |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-104416_adrdoc004_docs-regenerate-cross-validate.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-105117
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
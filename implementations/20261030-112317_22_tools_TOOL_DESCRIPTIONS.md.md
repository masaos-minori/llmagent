# Implementation Procedure: TOOL_DESCRIPTIONS.md manifest-mode registration

## Goal

Register the generator's manifest mode and flags in `tools/TOOL_DESCRIPTIONS.md`
(REQ-008 registration half; keeps `tool-descriptions-sync` green).

## Scope

**In scope:**
- Update the two existing `generate_reference_table.py` rows — summary row at
  `tools/TOOL_DESCRIPTIONS.md:50` and usage row at `:107` — to mention `--manifests`
  (write manifests + re-render docs) and the extended two-way `--check`.

**Out of scope:**
- New tool rows (no new tools are created by this plan); generator code (doc 05).

## Assumptions
- The `tool-descriptions-sync` hook (`.pre-commit-config.yaml:30-34`) fires on
  `tools/*.py` + `TOOL_DESCRIPTIONS.md` + workflow yml changes, so this row must land
  with docs 05/14.

## Design decisions
- Edit the existing rows in place; no new table rows — the mode is a flag set on an
  already-registered tool.

## Alternatives considered
N/A: docs-only row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Row `:50`: append manifest-mode clause (`--manifests` writes
   `registry/manifests/*.yaml` and re-renders guarded blocks; `--check` detects
   manifest↔source and block↔manifest drift).
2. Row `:107`: extend the flag column with `--manifests`.

### Method
Docs-only table edit.

### Details
- Keep wording within the existing column style (single cell, no line breaks).

## Compatibility considerations
Must be committed together with docs 05/14 changes so the sync hook sees code and
description updated in the same pass.

## Security considerations
N/A.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pre-commit run tool-descriptions-sync --all-files`; docs checker sequence
  (`routing.md`).

## Completion criteria
Both rows describe the manifest flags and the sync hook passes.

## Out of Scope
Generator implementation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | With docs 05/14 |
| 2 | Run the documentation checker sequence (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`, `REQ-008`
- **Source issue**: `issues/20261029-104505_adrcov001_contract-manifests-invariant-coverage.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_adrcov001_contract-manifests-invariant-coverage.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-112317
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

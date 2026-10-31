# Implementation Procedure: TOOL_DESCRIPTIONS.md manifest-mode registration

## Goal

Register the generator's manifest mode and flags in `tools/TOOL_DESCRIPTIONS.md`
(REQ-008 registration half; keeps `tool-descriptions-sync` green).

## Scope

**In scope:**
- Update the two existing `generate_reference_table.py` rows — summary row at
  `tools/TOOL_DESCRIPTIONS.md:53` and usage row at `:115` (re-verified 2026-10-31) —
  to mention `--manifests` (write manifests + re-render docs) and the extended two-way
  `--check`.
- Add one new row for `tools/_contract_manifests.py` (doc 05 helper module):
  `check_tool_descriptions_sync` requires a row for every `tools/*.py` except
  `__init__.py`, so the helper must be registered in the same commit as doc 05.

**Out of scope:**
- Other new tool rows; generator code (doc 05).

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
1. Row `:53`: append manifest-mode clause (`--manifests` writes
   `registry/manifests/*.yaml` and re-renders guarded blocks; `--check` detects
   manifest↔source and block↔manifest drift).
2. Row `:115`: extend the flag column with `--manifests`.
3. Add a summary + usage row pair for `tools/_contract_manifests.py` (private manifest
   IR helper: entry models, schema validation, YAML load/write, render primitives).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261031-104900 | 20261031-111503 | With docs 05/14 Summary rows: generate_reference_table.py (:53, manifest-mode clause) and _contract_manifests.py (:54) landed in the doc-05 cycle. This cycle extended the usage row (:116) with --manifests semantics and two-way --check wording, and added the _contract_manifests.py usage row (private helper, after :116) mirroring the _adr_authority_core.py pattern. Cited export names verified against tools/_contract_manifests.py (MANIFEST_VERSION, ManifestError, write_manifest, load_manifest, escape_table_cell, render_symbol_table). |
| 2 | Run the documentation checker sequence (`routing.md` Tools) | Completed | 20261031-110000 | 20261031-111503 | check_tool_descriptions_sync -> "No issues found"; full pre-commit run --all-files green (23 hooks, incl. tool-descriptions-sync fired by this file). |

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
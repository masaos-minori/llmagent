# mcpcompat001-update-the-compat-checker-catalog-entries

Plan source: `plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md`
Generated: 2026-10-28T01:32:16+09:00

## Goal

Update the two `check_compat_shims.py` catalog rows in `tools/TOOL_DESCRIPTIONS.md` so the
catalog describes the two new always-on syntax-tree rules (REQ-005; AC-7).

## Scope

- The summary-table row at current L28:
  > | `check_compat_shims.py` | Consistency checker | Detect leftover backward-compatibility stubs and shims |
- The detail-table row at current L97 (the long `check_compat_shims.py` description row).
- Nothing else in the file changes.

## Assumptions

- Verified 2026-10-28: L28 and L97 are the file's only two `check_compat_shims.py` rows; the
  detail row currently documents pattern matching, the `--check-removed-names` and
  `--check-doc-symbols` stages, and the manifest schema, but nothing AST-based.
- `tools/check_tool_descriptions_sync.py` compares these rows against the tool's state and is
  the gate named in the plan target row; it runs after procedure 17's implementation strings are
  final, so this edit lands in the same change set as 17-18.

## Design decisions

- Summary row gains "and syntax-tree rules for removed import and construction paths" — one
  clause, no detail leakage into the summary table (catalog style: summary rows stay short).
- Detail row gains one appended sentence covering both rules and the always-on wiring:
  existing wording about the opt-in flags and manifest schema stays byte-for-byte.

## Alternatives considered

- Rewriting the detail row from scratch: rejected — the existing wording is accurate for the
  pre-existing stages; only an append is warranted (minimal-diff policy).

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Replace the L28 summary cell text "Detect leftover backward-compatibility stubs and shims"
   with "Detect leftover backward-compatibility stubs and shims, including removed import and
   construction paths via syntax-tree rules".
2. Append to the L97 detail row, after its final clause about `--check-doc-symbols`:
   ``` text
   . Two always-on syntax-tree (AST) rules also run on every `*.py` file: one flags imports of
   Health names from the removed `shared.mcp_config` re-export path (canonical path:
   `shared.mcp_health`), the other flags `McpToolDiscoveryService` constructions that omit the
   required `posture_gates` argument; negative-test exemptions go through manifest entries
   (e.g. `mcp-posture-gate-negative-test`), never through code-side suppression
   ```

### Method

Two in-row text edits; table structure (pipes, line count) unchanged.

### Details

- No new backticked callable reference in `docs/` is created (the catalog lives under `tools/`),
  so the `--check-doc-symbols` symbol stage is unaffected.

## Compatibility considerations

- Must land in the same commit as procedure 17: `check_tool_descriptions_sync.py` fails on
  catalog drift otherwise.
- If procedure 17's landed rule names or wording differ from this document's quoted strings,
  align this row with the landed implementation text (contract pairing noted in procedure 18).

## Security considerations

- None; documentation-only.

## Rollback considerations

- Revert together with procedure 17.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py` — in sync (AC-7).
- `uv run python tools/check_tools_readme_sync.py` and any docs-checker coverage of
  `tools/TOOL_DESCRIPTIONS.md` listed in `routing.md` — clean.

## Completion criteria

- Both catalog rows describe the two new rules, and the sync checker passes (REQ-005, AC-7).

## Out of Scope

- The rule implementations — procedure 17.
- The rule tests — procedure 18.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Same commit as procedure 17 |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | Sync checker is the guard |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | check_tool_descriptions_sync |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | This document is the doc edit |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-104222_mcpcompat001_remove-mcp-compat-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110516_mcpcompat001_remove-mcp-compat-paths.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-013216
- **Related target files**: tools/TOOL_DESCRIPTIONS.md

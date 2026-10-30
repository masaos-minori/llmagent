# Implementation Procedure: `tools/TOOL_DESCRIPTIONS.md`

## Goal

Register `check_component_mandatoriness.py` in the tools index (plan row: register the checker per the routing.md Tools rule; `check_tool_descriptions_sync.py` enforces `tools/*.py` ↔ this file sync).

## Scope

- One new index row in `tools/TOOL_DESCRIPTIONS.md` (index table starts at :15-19, alphabetically ordered `check_*` rows, e.g. `check_adr_invariant_matrix.py` :21, `check_canonical_source_registry.py` :27).
- If the index count in the heading (`## Index (53 modules)`, :15) is derived from row count, update it (the sync checker's expectation governs; verify at edit time).

## Assumptions

- Lightweight row: one table row.
- Cross-plan overlap: toolexec001 (row 21) and adrcov001 (row 22) also append rows here. Append-only edits; land in batch order toolexec001 → adrcov001 → mcpgate001 (each plan's checker lands with its own row) and re-run the sync checker after each.

## Design decisions

- Row text: `| \`check_component_mandatoriness.py\` | Consistency checker | Three-way drift check: component-mandatoriness registry vs generated \`agent_08_04\` classification table vs \`config/agent.toml\` required values (ADR-004 Group 3 item 13) |` — inserted in alphabetical position among `check_*` rows.

## Alternatives considered

- N/A: registration format is fixed by the file's table shape.

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. Insert the row alphabetically (after `check_canonical_source_registry.py`-family rows, before `check_compat_shims.py` — exact slot verified at edit time against the merged file state after the other two plans' rows).
2. Update the index count if the heading number is not checker-agnostic.

### Method

Single-row insertion; land only after the checker file itself exists (row 8) — the sync checker fails on a described-but-missing tool.

### Details

- Keep the description imperative and checker-style, matching sibling rows' tone.

## Compatibility considerations

- `uv run python tools/check_tool_descriptions_sync.py` is the enforcing gate (its own description at :13); CI runs it per `rules/toolchain.md`.

## Security considerations

- N/A: index metadata.

## Rollback considerations

- N/A: revert the commit (row removal), together with row 8 if the tool itself is reverted.

## Validation plan

- `uv run python tools/check_tool_descriptions_sync.py`; `uv run python tools/check_auto_check_inventory.py` if a CI/pre-commit step for the new checker is documented (row 8 Procedure 6).

## Completion criteria

- The new tool appears exactly once in the index, the sync checker reports no drift, and the row matches the checker's implemented behavior.

## Out of Scope

- The checker implementation (row 8), CI wiring edits (row 8 Procedure 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the index row after row 8 lands | Pending | — | — | Cross-plan append order noted |
| 3 | Run `check_tool_descriptions_sync.py` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Row 8 (the checker file) must exist before its description lands | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 (drift checker registration; routing.md Tools rule)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`

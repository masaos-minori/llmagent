## Goal
Extend the MCP configuration-file inventory with the `[dedup]` key contract: the three optional capacity-threshold keys and the `legal_hold_states` list key, with validation ranges and absent-means-unset defaults (REQ-007 threshold mechanism without numeric values; REQ-003 legal hold as a configuration entry).

## Scope
**Release unit**: health exposure
One `[dedup]` inventory subsection added to the Layer 2 section of one page; the isolation-policy and reload text stays as it is.

## Assumptions
- Verified by reading the file: `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` carries no `AUTO-GENERATED` guard block (in `docs/22_mcp/` the only guarded block is in `mcp_01_tool_ownership_matrix.md`) and lists no `[dedup]` keys today, so the inventory is manually maintained and edited directly per the file's conventions.
- Owner decision `U-2`: legal hold is configuration-based, no DDL and no store-identity fingerprint change; the existing four `[dedup]` keys (`db_path`, `retention_days`, `lease_seconds`, `max_attempts`) stay as they are.
- Threshold and hold values are operator-supplied (`U-1`); the 10 committed `config/*_mcp_server.toml` files carry none of the new keys and stay valid unchanged.

## Design decisions
- Per the page's own "Configuration Value Ownership" convention, numeric defaults live in `scripts/shared/mcp_dedup_config.py` and the config files; this page adds only the new keys' names, ranges, valid list values, and absent semantics.

## Alternatives considered
N/A: docs-only change.

## Implementation
### Target file
- `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
### Procedure
- Add a `[dedup]` key subsection under `## Layer 2 — MCP Server Local Application Configuration`, in the file's existing `| Key | Scope |` table style: `max_dedup_rows` (integer, 1..10000000), `max_dedup_growth_per_hour` (integer, 1..1000000), `max_dedup_wal_mb` (integer, 1..4096), and `legal_hold_states` (list of stored state names: `pending`, `completed`, `failed`, `interrupted`).
- State the rules: absent means unset (no per-metric status computed; absent or empty `legal_hold_states` means no hold); out-of-range, non-integer, or unknown-state-name values fail closed at startup (`ConfigParseError`), like the existing four `[dedup]` keys; no committed `config/*_mcp_server.toml` file changes because the keys are optional; the keys are excluded from the store identity fingerprint (`_config_fingerprint`).
- Cross-link the sweep/hold semantics in [db_03_07](../41_db/db_03_07_mcp-dedup-and-execution-snapshot.md) and the health exposure in [mcp_02_02](mcp_02_02_startup-modes-and-health.md), matching the page's existing link style.
### Method
- Direct manual edit (no generated block to regenerate); no numeric threshold value is written into the page.
### Details
- The subsection names the keys only; validation stays with `load_dedup_section()` in `scripts/shared/mcp_dedup_config.py`, the startup gate `scripts/mcp_servers/server.py` already runs.

## Compatibility considerations
N/A: docs-only change.

## Security considerations
N/A: docs-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` — the exact command the Plan's validation row names for this file; the file has no guarded `AUTO-GENERATED` block, so the gate must stay passing unchanged and the edit is direct manual maintenance.
- `uv run python tools/check_docs_consistency.py --domain mcp` (the Plan target-file row names `tools/check_docs_consistency.py`); `rules/tool-gates.md` docs checkers (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`) also apply to any `docs/*.md` edit.

## Completion criteria
The inventory lists the four existing `[dedup]` keys and the four new optional keys with ranges, valid list values, absent semantics, and fail-closed validation; it states that no committed config file and no store identity changes; the Plan's generated-reference gate stays passing.

## Out of Scope
Editing any `config/*_mcp_server.toml` file (not a target row); numeric threshold values (`U-1`); the config-validation code and metrics wiring (other Plan rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-212603 | 20261123-212654 | adversarial verification: no AUTO-GENERATED guard confirmed, no [dedup] keys listed today, Key/Scope table style confirmed, ranges match sibling procedure seq 08 changed: docs/22_mcp/mcp_06_01_configuration-file-inventory.md ([dedup] key contract subsection: existing 4 keys + 4 new optional keys with ranges, absent semantics, fail-closed, fingerprint exclusion) |
| 2 | Run the documentation checkers named in the Validation plan | Completed | — | 20261123-212654 | quality/structure/content_policy pass; generate_reference_table --check no drift; consistency --domain mcp: only the pre-existing seq 03 warning, no finding on this file; documentation-only case replaced test runs |

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
- **Requirement ID**: `REQ-007` (threshold keys and validation range, fail closed, no numeric values), `REQ-003` (legal hold as a `[dedup]` configuration entry)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
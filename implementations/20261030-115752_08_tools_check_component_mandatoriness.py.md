# Implementation Procedure: `tools/check_component_mandatoriness.py`

## Goal

Create the three-way CI drift checker: registry file ↔ generated `agent_08_04` classification table ↔ `config/agent.toml` `required` values; any drift fails (REQ-005 drift enforcement; plan AC-4: the checker fails on any registry/table/config drift).

## Scope

- New tool `tools/check_component_mandatoriness.py` (new), following the `tools/check_db_separation.py` live-repo checker pattern (its header at :1-30 defines the convention: module docstring with numbered checks, Rule/Usage/Exit-codes sections, `--format json`, exit 0/1).
- No test row exists in the plan's target table for this checker's synthetic-repo negative tests (plan Design Key Components 3 asks for them) — recorded as an additional-target-file discovery to register before implementation (see Assumptions).

## Assumptions

- Rows 1 (registry), 9 (generated block), and existing `config/agent.toml` are the three inputs.
- Missing test row: the plan's Tests section omits `tests/tools/test_check_component_mandatoriness.py` although the Design section requires synthetic-repo negative tests. Needs Confirmation: register it as an 30th target row (additional-target-file discovery, workflow Step 3) — do not silently add test edits to unrelated rows.
- `check_db_separation.py` pattern: static parsing of repo files, no network, no DB.

## Design decisions

- Three checks (numbered in the module docstring like `check_db_separation.py`): 1) registry ↔ `agent_08_04` table: entry `component_id` (new)/`classification`/`rationale` must equal the rendered guard-block rows; 2) registry ↔ config: every configured `[mcp_servers.*]` key has a registry entry with `required` agreeing with the config value; every registry entry exists as a configured server; 3) table freshness: the `agent_08_04` block is the AUTO-GENERATED guard block produced by row 9 (a hand-edited table outside the markers is drift).
- Import the loader from `scripts.shared.component_mandatoriness` (tools may import scripts; `sys.path` bootstrapping follows existing tools' convention) so entry validation logic is not duplicated.
- Output style: human-readable violations + `--format json`; exit 0 clean / 1 violations (same as `check_db_separation.py` :26-30).

## Alternatives considered

- Folding the check into `tools/generate_reference_table.py --check` — rejected: `--check` compares rendered blocks against generator output (drift of docs vs generator), not config-vs-registry semantics; merging them would couple config validation into the doc pipeline (row 14 of adrcov001 already pins that pipeline's contract).
- Living only in startup validation — rejected: startup enforces at runtime (row 5); CI must fail before merge (plan AC-4), and a dev-only startup abort cannot be a CI gate.

## Implementation

### Target file

`tools/check_component_mandatoriness.py` (new)

### Procedure

1. Module docstring: numbered check list, `Rule: ADR-004 Decision Group 3 item 13`, `Usage`, `Exit codes` sections mirroring `check_db_separation.py`.
2. `_load_registry()` (new): `load_component_mandatoriness()` from row 2; load failure exits 1 with an "undeterminable mandatoriness" violation.
3. `_load_agent_08_04_table()` (new): locate the guard-block markers row 9 defines in `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`, parse the markdown table rows (`Server | Classification | Rationale`).
4. `_load_config_requireds()` (new): parse `config/agent.toml` `[mcp_servers.*]` tables via `tomllib`, read `required` (default `True` matching `scripts/shared/mcp_config.py:326` normalization).
5. Cross-check the three inventories; collect `Violation(component_id, check, detail)` records; print/report per `--format`.
6. Register the checker in `tools/TOOL_DESCRIPTIONS.md` (row 29 owns that edit) and in CI/pre-commit (Needs Confirmation: add a CI step — the plan's Validation plan runs it as a standard gate; adrcov001 row 14 already restructures `ci.yml`, so land this after it and append the step there).

### Method

Static repo inspection like `check_db_separation.py`; pure functions with a `main(argv) -> int` entry.

### Details

- Check 1 compares the rendered table cell text exactly (classification column shows `required` for all 10 today).
- Check 2 flags: config server missing from registry (unknown), registry entry missing from config (orphan), and value conflicts (`required = false` vs `classification: required`).
- Exit 1 for any violation; message format `<check>: <component_id>: <detail>` for greppability.

## Compatibility considerations

- New standalone tool; CI wiring is additive. Landing order with adrcov001 row 14 (ci.yml edits) recorded above.

## Security considerations

- The checker is a fail-closed CI gate; it must exit non-zero on a missing registry file, not skip.

## Rollback considerations

- Delete the file + its TOOL_DESCRIPTIONS row + any CI step (single commit revert).

## Validation plan

- Live-repo run: `uv run python tools/check_component_mandatoriness.py` exits 0 on the all-required configuration.
- Synthetic negative tests (pending target registration, see Assumptions) mirror `check_db_separation.py`'s test style; until registered, validate manually with a temp-dir fixture.
- Gates: `uv run ruff check tools`, `uv run mypy scripts` unaffected (tools type-checked per `rules/toolchain.md`).

## Completion criteria

- On the live repo the checker exits 0; on a synthetic drift (conflict, orphan, unknown, hand-edited table) it exits 1 naming the component and check (plan AC-4).

## Out of Scope

- Startup enforcement (rows 4-5), the generator block itself (row 9), TOOL_DESCRIPTIONS row content (row 29).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the checker per Procedure 2-5 | Pending | — | — | Needs rows 1, 9 |
| 2 | Register synthetic-repo test file as additional target row (Needs Confirmation), then its tests | Pending | — | — | Plan target-table gap |
| 3 | Run the validation sequence (`rules/toolchain.md`) + live-repo run | Pending | — | — | |
| 4 | CI/pre-commit step appended after adrcov001 row 14 lands | Pending | — | — | Cross-plan order |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Registry (row 1) and generated table (row 9) must exist for checks 1/3 | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

#### Marker edit record
- `(new)` マーカー編集（この doc が導入する新規コンポーネント）は `tools/mark_new_115752.py`（冪等）に記録済み。

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005 (registry drift-checked against the approved classification table; AC-4)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tools/check_component_mandatoriness.py` (new)

## Goal

Add the typed metadata fields to `RuntimeTool` and remove the risk-lowering default from `build_runtime_tool()` (REQ-002, AC-02).

## Scope
**Release unit**: contract-and-producers

## Assumptions
- The vocabulary comes from `scripts/shared/tool_metadata.py` (row 01), which lands in the same release unit.

## Design decisions
- `build_runtime_tool()` keeps its shape; only the required argument set grows, so producer call sites keep their current style.
- `agent_safety_tier` becomes a required argument: the current `WRITE_DANGEROUS` default is the last default that lowers risk, and it is removed rather than re-pointed at another default.

## Alternatives considered
- N/A: the plan's design section fixes the shape of this change.

## Implementation
### Target file
`scripts/shared/runtime_tool.py`
### Procedure
- Extend the `RuntimeTool` frozen dataclass with the new required fields and change `resource_scope_keys` to the key-to-kind mapping; remove the `agent_safety_tier` default from `build_runtime_tool()`.
- Correction 2026-11-21 (Step 3a): this row said "TypedDict"; `RuntimeTool` is a frozen dataclass — the TypedDict is `McpTool` (row 68).
### Method
- New required fields on `RuntimeTool` (new): `side_effect_class` (new), `retry_policy`, `reconciliation_policy` (new), `idempotency_required` (new), `preview_capability` (new), `policy_version`.
- `resource_scope_keys` value type becomes the key-to-`ResourceKeyKind` mapping.
- No default value is added for any new field: a missing value raises, matching the current behavior of the four schema-2.0 fields.
### Details
- Verified 2026-11-21: `AgentSafetyTier` currently defaults to `WRITE_DANGEROUS` and `is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys` are required.
- The shared test factory `tests/shared/runtime_tool_factory.py` is the only place that supplies the permissive defaults; production call sites must not gain defaults.
### Companion test files
- `tests/shared/test_runtime_tool.py`
  - Procedure: Replace the existing safe-default assertions (the `TestStrictBuilder` and `TestFixtureBuilderEquivalence` groups) with required-field assertions for the new fields, including that no default lowers risk.
  - Validation: `uv run pytest tests/shared/test_runtime_tool.py -v`
- `tests/shared/runtime_tool_factory.py`
  - Procedure: Make `build_fixture_runtime_tool()` supply the new required fields, since the production builder no longer has defaults; keep the permissive behaviour confined to the fixture (T-02).
  - Validation: `uv run pytest tests/shared/test_runtime_tool.py -v` and `PYTHONPATH=scripts uv run lint-imports`

## Compatibility considerations
- Every producer declaration and every consumer that reads these fields is in the same release unit; this file alone does not pass validation.

## Security considerations
- REQ-002 is fail-closed: an absent value must raise at build time, not fall back to a lower-risk value.

## Rollback considerations
- N/A: revert the commit within the release unit.

## Validation plan
- Run the validation sequence in `rules/toolchain.md`.

## Completion criteria
- `build_runtime_tool()` rejects a call that omits any required field, and no default that lowers risk remains in the function.
- The import-linter contract keeps `tests/shared/runtime_tool_factory.py` out of production imports.

## Out of Scope
- N/A: this document covers only its target file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue; Phase 2; release unit: contract-and-producers Implemented: runtime_tool.py required field set; resource_scope_keys mapping. |
| 2 | Add or update tests per Validation plan | Completed | — | 2026-11-21 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue test_runtime_tool.py + runtime_tool_factory.py updated: 42 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261121-203300 | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue Targeted gates green 2026-11-21. Allowed red states: production/test callers of build_runtime_tool (rows 08-21, 34-39, 43-59) pending in-unit. unit-end validation: full suite 13314 passed / 7 skipped; ruff format+check clean; mypy 590 files clean; lint-imports 6 kept; diff-cover 97% (fail-under 90) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Gate lifted by owner decision 2026-11-21: issues/20261120-115845_mcpdl006_two-layer-failure-verification.md phase all - the reconciliation field values and the replay boundary are defined by that issue |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261120-114211_agentcfg003_runtime-tool-metadata.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-105007_agentcfg003_runtime-tool-metadata.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-115519
- **Related target files**: `scripts/shared/runtime_tool.py`, `tests/shared/test_runtime_tool.py`, `tests/shared/runtime_tool_factory.py`
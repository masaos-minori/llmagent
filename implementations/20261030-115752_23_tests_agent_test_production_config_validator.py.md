# Implementation Procedure: `tests/agent/test_production_config_validator.py`

## Goal

Add the downgrade-rejected and unknown-classification-fatal regressions for the mandatoriness cross-check (plan Tests New: fail-before/pass-after in this file; REQ-004 contract lock, AC-3).

## Scope

- `tests/agent/test_production_config_validator.py`: new test class/methods only; existing tests (:15 onward, strict-key and safety-tier suites) stay byte-identical as characterization locks.
- No production edits (rows 4-5 own them); tests are red until row 4 lands.

## Assumptions

- Tests call `ProductionConfigValidator().validate_against_registry(...)` (row 4's (new) method) with synthetic registry maps built from row 2's `ComponentClassification` (new) — no dependence on the live registry file except one all-required positive test that loads it via `load_component_mandatoriness()`.
- Pipeline-level fatality (AC-3's "aborts startup") is asserted in two layers: unit-level (this file: error list non-empty for conflict/unknown) and pipeline-level (row 24's startup-validation regression).

## Design decisions

- Three new tests: `test_required_false_conflicts_with_registry_required` (new) (downgrade rejected — one error naming component, approved classification, config value, registry path, pinned with `pytest.raises`-free error-string `match` on row 4's message format); `test_configured_server_absent_from_registry_is_error` (new); `test_live_registry_agrees_with_all_required_config` (new) (empty error list for the real repo state — AC-6 guard).
- Fail-before/pass-after ordering: commit tests before row 4 (red = collection error on missing method), then row 4 turns them green (plan Tests section "fail-before/pass-after").

## Alternatives considered

- Synthetic registry only, no live-file test — rejected: AC-2/AC-6 need a pinned assertion that the shipped registry and shipped config actually agree.

## Implementation

### Target file

`tests/agent/test_production_config_validator.py`

### Procedure

1. Imports: `ComponentClassification` (new), `load_component_mandatoriness` (new) (row 2, (new)) alongside the existing `ProductionConfigValidator` import.
2. Add a `TestComponentMandatorinessCrossCheck` (new) class with the three tests above.
3. Synthetic map helper `_registry_map(**required_ids)` (new) constructing `ComponentClassification` (new) entries with fixed field values.

### Method

Unit-level direct calls on the validator; no ctx/pipeline mocks (pipeline wiring is row 24's scope).

### Details

- Message pinning uses row 4 Details' exact strings so the fatal operator output is contract-tested (REQ-008).
- The orphan case (registry entry with no configured server) is asserted as non-fatal: it must not appear in the error list (row 4 Design decision 3).

## Compatibility considerations

- New tests only; existing file behavior untouched. Red window between this row and row 4 is planned (test-first).

## Security considerations

- N/A: tests only; they lock the fail-closed semantics.

## Rollback considerations

- Delete the new class + helper (single commit revert).

## Validation plan

- `uv run pytest tests/agent/test_production_config_validator.py`; `uv run pytest tests/agent` (plan Phase 3 "Done when"); ruff/mypy gates per `rules/toolchain.md`.

## Completion criteria

- All three tests green after row 4 merges: the downgrade fixture produces exactly one named conflict error, the unknown fixture exactly one unknown-classification error, the live-repo fixture zero errors (plan AC-3, AC-6).

## Out of Scope

- Pipeline fatal wiring (row 5), publication-order test (row 24), loader tests (row 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the new class + three tests (red) | Pending | — | — | Before row 4 |
| 2 | Green after rows 2+4 merge | Pending | — | — | |
| 3 | Run file + `tests/agent` + gates | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 2 | Rows 2 (loader) and 4 (validator method) must merge | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (downgrade-rejected / unknown-fatal regressions; AC-3)
- **Source issue**: `issues/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261030-001153_mcpgate001_mcp-mandatory-construction-contracts.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-115752
- **Related target files**: `tests/agent/test_production_config_validator.py`

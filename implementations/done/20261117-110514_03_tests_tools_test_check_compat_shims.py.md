## Goal
Add checker tests to `tests/tools/test_check_compat_shims.py` for every new contract-guard rule — a positive case (reintroduction fails), a negative case (strict source passes), and an allowed-historical case where the rule has a historical allowance — plus a regression case that the unchanged `db.store` / `eventbus.db` prohibitions still fail on a reintroduced import (`REQ-006`, `REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit. Fixture-based positive/negative tests can be written and run before procedure 02 wires the rules (they import the helper functions directly); only the `check_all`-level wiring tests and any live-tree negative assertions become meaningful once procedure 02 lands after compat002.

- Extend `tests/tools/test_check_compat_shims.py` with new test classes following the file's existing `tmp_path`-fixture conventions.
- No other test file changes: `tests/tools/test_compat_checker_precompiled.py` and `tests/tools/test_no_compatibility_policy_gate.py` keep their current contracts (the gate test only asserts zero live findings, which holds once compat002 lands and procedure 02 wires the rules).

## Assumptions
- Procedure 01's function names exist as specified: `check_dataclass_field_defaults`, `check_optional_guarded_params`, `check_attempts_ddl_nullability`, `check_historical_doc_phrases`, `check_contract_guards` (all `(new)` in procedure 01 and imported from `tools._compat_leftover_phrases`).
- The file is already allowlisted by the `check-compat-shims-test-data` fixture entry in `tools/compat_exceptions.toml`, so in-file synthetic fixtures do not self-flag in live scans; no new manifest entry is added.
- Synthetic fixtures are written to `tmp_path` files like the existing `TestPatternDetection` cases; the content-keyed guards fire regardless of temp path, and the doc-phrase guard fires for a temp path containing a `docs/` segment (e.g. `tmp_path / "docs" / "x.md"`), matching the helper's segment-aware `_in_scope`.

## Design decisions
- Test direct helper functions for rule behavior and `checker.check_all` only for the wiring assertion, so a wiring regression and a rule regression produce different failing tests.
- Strict-source negative cases for `REQ-001` assert on the real `scripts/agent/workflow/models.py` (read, not written) in addition to a mirrored strict fixture — this is the only rule whose live negative case is ungated today.
- Fixture names use realistic shapes (`class WorkflowDef` with `stages: list[StageDefinition] = field(default_factory=list)`; `def begin_stage_if_new(..., lease_duration_sec: int | None = None)`; a `CREATE TABLE IF NOT EXISTS attempts` block with `owner_id TEXT,`) so the tests pin the exact reintroduced patterns the guards must catch.

## Alternatives considered
- A new test file `tests/tools/test_compat_contract_guards.py`: rejected — it is not a row of the plan's frozen `Implementation Target Files` table, and the plan pins tests to the existing checker test file.
- Only `check_all`-level tests: rejected — they cannot distinguish which rule fired and would couple rule tests to the compat002 landing gate.

## Implementation
### Target file
- `tests/tools/test_check_compat_shims.py`

### Procedure
1. Add `TestContractDataclassDefaults` (positive: `test_retry_on_default_fails`, `test_stages_default_factory_fails`, `test_retry_policy_default_fails`, `test_field_kwarg_default_fails`; negative: `test_default_free_contract_passes` against a strict mirrored fixture and `test_live_models_source_has_no_findings` reading `scripts/agent/workflow/models.py`).
2. Add `TestContractLeaseParam` (positive: `test_defaulted_lease_param_fails`, `test_optional_annotation_lease_param_fails`, `test_kwonly_defaulted_lease_param_fails`; negative: `test_required_lease_param_passes` — a bare `lease_duration_sec: int` parameter, mirroring `attempt_ops.lease_expires_from`).
3. Add `TestContractAttemptsDdl` (positive: `test_nullable_owner_id_column_fails`, `test_nullable_lease_expires_at_column_fails`; negative: `test_not_null_columns_pass`, `test_other_tables_not_scanned`).
4. Add `TestContractHistoricalDocPhrase` (positive: `test_current_tense_age_threshold_fails` in a `tmp_path/docs/` fixture; allowed-historical: `test_removed_marker_allowed`, `test_historical_marker_allowed`, `test_withdrawn_marker_allowed` — marker on the line itself and on a line within the preceding 10; negative: `test_age_threshold_outside_docs_scope_passes` for a `scripts/`-scoped fixture).
5. Confirm the `db.store` / `eventbus.db` import regression cases already in the file cover both `from db.store import` and `from eventbus.db import` forms; add any missing case (`test_db_store_import_still_flagged`, `test_eventbus_db_import_still_flagged`) (`REQ-005`).
6. Add `TestContractGuardsWiring` asserting `checker.check_all(content, path, set())` reports the guard finding for one representative fixture per rule with default flags (always-on, no flag needed) — these assert the procedure 02 wiring.
7. Run `uv run pytest tests/tools/test_check_compat_shims.py -v`.

### Method
- Follow the file's existing conventions: class-grouped tests, `tmp_path` synthetic files, direct helper imports (`from tools._compat_leftover_phrases import ...`), `checker.check_all(...)` for wiring.
- Assert on the issue-string shape (`backward compatibility leftover` and the `filepath:lineno` prefix) as existing cases do.

### Details
- Fixture imports for the dataclass positive cases must be self-contained (`from dataclasses import dataclass, field` in the fixture source) so `ast` parsing is realistic.
- Wiring tests pass an empty allowlist explicitly so an accidental allowlist widening would fail the test.
- The gate interplay is covered by the existing `tests/tools/test_no_compatibility_policy_gate.py`; no change there.

## Compatibility considerations
- Tests must not print or embed a literal `legacy age threshold` phrase unprotected — the file's allowlist entry exempts the test file from checker scans, matching the existing pattern for test data.
- No new dependencies; stdlib + pytest only, consistent with the file's current imports.

## Security considerations
- Test fixtures are inert strings written to temp files; no subprocess or network. The `tmp_path` fixture keeps cleanup automatic.

## Rollback considerations
- Pure test additions to one file; revert the commit removes them with no residue.

## Validation plan
- `uv run pytest tests/tools/test_check_compat_shims.py -v` — every new rule has positive/negative/allowed-historical cases and passes once procedures 01 and 02 are implemented.
- `uv run pytest tests/tools -v` and `uv run pytest -m repo_scan -v` — no regressions in the sibling checker tests or the policy gate.
- Run the tests before procedure 02 lands: rule-level tests pass against procedure 01's helper; `TestContractGuardsWiring` and live-tree assertions are expected to run in the same change as procedure 02 (the wiring).

## Completion criteria
- Each of `REQ-001`–`REQ-004` has positive, negative, and (where the rule has an allowance) allowed-historical cases in the file; the `db.store` / `eventbus.db` regression case is present; `check_all` wiring is asserted for every new rule; the whole file passes under `pytest tests/tools`.

## Out of Scope
- Helper rule implementation (procedure 01), `check_all` wiring (procedure 02), `tools/TOOL_DESCRIPTIONS.md` (procedure 04), and changes to `tests/tools/test_compat_checker_precompiled.py` or `tests/tools/test_no_compatibility_policy_gate.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117 | 20261117 | Rule-level tests can land after procedure 01; wiring tests land with procedure 02 6 test classes / 28 cases added; file now 191 passed 28 new cases across 6 classes; targeted file 191 passed |
| 2 | Add or update tests per Validation plan | N/A | — | — | This document is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261117-120000 | test file lint/mypy clean; 191 tests pass; batch-end gates still pending targeted/lint green; batch-end full-suite gates pending |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261117-120000 | No docs owned here |

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
- **Requirement ID**: `REQ-006` (tests for every new rule) plus the `REQ-005` unchanged-prohibitions regression case
- **Source issue**: `issues/20261116-114953_compat004_compat-regression-guards.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-235333_compat004_compat-regression-guards.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-110514
- **Related target files**: `tests/tools/test_check_compat_shims.py`
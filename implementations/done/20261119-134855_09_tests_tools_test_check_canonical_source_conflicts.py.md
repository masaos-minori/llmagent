## Goal

- Add failing-fixture tests to `tests/tools/test_check_canonical_source_conflicts.py` covering `REQ-006`–`REQ-009`, `REQ-012`–`REQ-013` and the registry-fix confirmation (`AC-12`/`T12`) before the checker fixes in seq 02 and the config fixes in seq 03 (Plan Phase 2 step 1: test-first).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new pytest fixtures/tests (T06–T09, T11, T12) in this file only.
- Out of scope here: the routing parametrization rewrite — `tests/tools/test_check_canonical_source_conflicts_routing.py` is the companion of the seq 02 code document (`REQ-011`).

## Assumptions

- Fixtures inlined under pytest `tmp_path` (tmp registry TOML + tmp ADR/source files), not committed (Plan Assumptions).
- Baseline pins that must stay green (verified 2026-11-19): the `CANONICAL-008` multiple-specifications tests (this file, lines 102–112) and the `CANONICAL-009` empty-area tests (lines 446–463).
- Code-uniquification target is `CANONICAL-012` (Plan `REQ-009` as amended 2026-11-19; `CANONICAL-009` is already taken by the empty-area detector).

## Design decisions

- Fixture shape per requirement (Plan Test Design):
  - `T06` (`AC-06`): fixture whose conflict is detectable only by the nine semantic detectors — assert findings appear when the validator path succeeds, proving `_run_detection_functions` ran on the main path.
  - `T07` (`AC-07`): registry validation error that does not name a `decision_target` (e.g. a missing source path) — assert exactly one blocking finding (drives the wrapper substring-gate removal and the GV-021 severity mapping).
  - `T08` (`AC-08`): one registry error matched by multiple entries — assert exactly one finding per `(code, decision_target)` with the entry list in the finding detail (no cross-product duplication).
  - `T09` (`AC-09`): fixture combining the version-error path with all other detectors — assert no finding code repeats and the version error carries `CANONICAL-012`.
  - `T11` (`AC-11`): `main(["--help"])` output contains the actual default `config/documentation_canonical_sources.toml`.
  - `T12` (`AC-12`): a fixture registry replicating the four defective rows probed 2026-11-19 (bootstrap-ddl source path, posture-failure-handling notes, governance.policy row, overview claim type) — asserts the pre-fix run reports those conflicts and, paired with the seq 03 corrected rows (read via the repo registry path), the corrected registry yields exit 0 across both checkers; this fixture also pins the UNK-04 final row values chosen for `REQ-016`/`REQ-019`.
- Dead-code guard for `REQ-012`: no new test imports anything on the vulture removal list (UNK-03); existing tests that import kept helpers are untouched.

## Alternatives considered

- Extend the routing test file with these fixtures — rejected: those tests belong to the code row's companion (Plan companion rule); detection fixtures belong to the main conflicts test file.

## Implementation
### Target file
`tests/tools/test_check_canonical_source_conflicts.py`
### Procedure
1. Write T06–T09, T11, T12 fixture tests first; run against the current checker to confirm each fails on its known defect.
2. Hand off to seq 02 (checker fixes) and seq 03 (registry rows); re-run this file after each fix batch until green.
3. Keep the existing tests — including the `CANONICAL-008` and `CANONICAL-009` pins — green throughout.

### Method
- Test-first red/green cycle per Plan Phase 2; one defect class per fix batch.

### Details
- Deterministic assertions only: compare finding sets as sorted lists (no reliance on set iteration order) so the tests stay stable after the seq 02 sorting fixes.
- The `T12` fixture must build tmp copies of the defective rows (it cannot mutate the repo registry); the corrected-registry half of `T12` runs the real repo registry after seq 03 lands, guarded with the clean-run baseline (exit 0).

## Compatibility considerations

- The old assertions that pinned the defective behavior (e.g. duplicated findings, dropped target-less errors) are updated in the same commit as the new tests, each cited to the Plan `AC` it replaces.
- The `HAS_REGISTRY_VALIDATOR` import contract with `tools/check_canonical_source_registry.py` is exercised as-is; the seq 01 fixes do not change the imported signatures.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- Revert this test file alone; no production code depends on it.

## Validation plan

- `uv run pytest tests/tools/test_check_canonical_source_conflicts.py -v` — green after seq 02/03 complete; each new test red before its fix.
- `uv run pytest tests/tools/ -v` for cross-file regressions (routing companion, registry tests).
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- T06–T09, T11, T12 exist and pass against the fixed checker and corrected registry; all baseline tests including the `CANONICAL-008`/`CANONICAL-009` pins pass; no finding code repeats in any fixture run (`AC-09`).

## Out of Scope

- Checker code fixes (seq 02), registry config fixes (seq 03), and the routing parametrization (seq 02's companion section).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add T06–T09, T11, T12 failing-fixture tests | Completed | 2026-11-19 | 2026-11-19 | Written test-first inline during the member 02 run (seq-order batch decision, recorded in the Final Report): red evidence captured before the seq 02 fixes (doc 02 Design decisions / Execution Status). Verification 2026-11-19: all six fixture classes present as specified — `TestMainPathDetectorsT06`, `TestWrapperBlockingT07`, `TestWrapperDedupT08` (pins exactly one `007` + one `001` per duplicate pair), `TestCodeUniquenessT09` (no code repeats; version error carries `CANONICAL-012`; exact-12-codes assertion), `TestHelpDefaultT11`, `TestRegistryRowCorrectionsT12` (defective-rows half + corrected-rows half pinning the UNK-04 re-pointing values + clean-run exit 0). T07 note: the Plan's severity mapping materialized as `CANONICAL-013` HIGH/BLOCKING (doc 02 Design decisions) |
| 2 | Re-run after each seq 02/03 fix batch until green | Completed | 2026-11-19 | 2026-11-19 | File re-run after each doc 02 fix batch and after the doc 03 row fixes (the T12 corrected-rows half was skip-marked "blocked on seq 03" during member 02 and unskipped by member 03); final state 45 tests green in this file, `CANONICAL-008` and `CANONICAL-009` baseline pins untouched, `uv run pytest tests/tools/` cross-file run green for the three checker test files |

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
- **Requirement ID**: `REQ-006` (main path), `REQ-007` (wrapper gate), `REQ-008` (dedup), `REQ-009` (unique codes), `REQ-012` (dead code), `REQ-013` (help text), `REQ-016`/`REQ-019` (pinned via T12 fixture)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `tests/tools/test_check_canonical_source_conflicts.py`

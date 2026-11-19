## Goal

- Add failing-fixture tests to `tests/tools/test_check_canonical_source_registry.py` covering `REQ-001`–`REQ-005` before the checker fixes in seq 01 (Plan Phase 1 step 1: test-first), and keep the existing tests green.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new pytest fixtures/tests for T01–T05 in this file only.
- Companion relationship: this file is the test companion of `tools/check_canonical_source_registry.py` (Plan target-table row 1); the fixes themselves are in the seq 01 document.

## Assumptions

- Fixtures are built in-memory / under pytest `tmp_path` (tmp registry TOML + tmp ADR files), not committed as standalone fixture files (Plan Assumptions; the earlier `/tmp/opencode/fixture_registry.toml` probe is the reference shape).
- Baseline: the file has 13 test functions (verified 2026-11-19); all must stay green after the additions.
- T-test mapping follows the Plan's Test Design table (`T01`–`T05`, `AC-01`–`AC-05`).

## Design decisions

- Fixture shape per requirement:
  - `T01` (`AC-01`): registry entry with `claim_type = "architecture-decision"` referencing an ADR file whose `## Status` is `Draft` — assert `validate`/`validate_all` reports exactly one error of the "non-Accepted status" class and no duplicate class (drives the seq 01 severity fix and pairs with the conflicts-side single-warning assertion in seq 09).
  - `T02` (`AC-02`): run the validation flow from a cwd different from the repo root (monkeypatch cwd to `tmp_path`) and assert identical findings — drives the `Path.cwd()` fix.
  - `T03` (`AC-03`): `main(["--unknown-option"])` raises `SystemExit` with code 2 (argparse behavior; regression guard per the 2026-11-19 re-verification).
  - `T04` (`AC-04`): no test imports any helper targeted for removal; add an import/attribute-absence assertion only where the Plan's dead-code list must stay deleted (post-fix guard), keeping UNK-03's "keep anything a passing test imports" rule.
  - `T05` (`AC-05`): two consecutive validation runs over the same fixture produce byte-identical error lists.
- Use the module's public entry points (`load_registry`, `RegistryEntry.validate`, `validate_registry_schema`, `main`) so the tests survive internal refactors.

## Alternatives considered

- Commit a fixture TOML/ADR pair under `tests/fixtures/` — rejected: Plan Assumptions require inlined pytest fixtures.

## Implementation
### Target file
`tests/tools/test_check_canonical_source_registry.py`
### Procedure
1. Write T01–T05 fixture tests first; run them against the current checker to confirm they fail exactly on the known defects (`T03` passes immediately as a behavior lock per the 2026-11-19 re-verification).
2. Hand off to the seq 01 document for the fixes; after each fix batch, re-run this file and un-fail the corresponding test.
3. Keep the 13 existing tests green throughout.

### Method
- Test-first red/green cycle per Plan Phase 1: red on current code → seq 01 fix → green.

### Details
- Fixture ADRs must include a `## Status` section (the checker's `_find_status_section` contract) so `T01` exercises the Draft-vs-Accepted path, including the missing-section error text "ADR-sourced entry missing ## Status section".
- `T02` must pass an absolute `--registry`/path so cwd is the only variable.

## Compatibility considerations

- The existing 13 tests pin current contracts (including entry-validation error texts); new tests must not re-pin behavior the Plan removes — where the Plan changes behavior (duplicate severity class), the new test replaces the expectation, and any conflicting old assertion is updated in the same commit with a comment citing the Plan `AC-01`.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- Revert this test file alone; no production code depends on it.

## Validation plan

- `uv run pytest tests/tools/test_check_canonical_source_registry.py -v` — all tests green after seq 01 completes; each new test red before its fix.
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- T01–T05 exist and pass against the fixed checker; the 13 baseline tests pass; no committed fixture files outside the test module.

## Out of Scope

- Checker code fixes (seq 01) and conflicts-side tests (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add T01–T05 failing-fixture tests (`REQ-001`–`REQ-005`) | Completed | 2026-11-19 | 2026-11-19 | Written test-first inline during the member 01 run (seq-order batch decision, recorded in the Final Report): red evidence captured before the seq 01 fixes (doc 01 Execution Status rows 1–2 cite T01/T02 red→green). Verification 2026-11-19: all five fixture classes present as specified — `TestSingleSeverityNonAcceptedAdr` (T01, Draft-ADR fixture `_T01_ADR_TEXT` with a `## Status` section, asserts exactly one error and `validate_all` warnings == []), `TestRepoRootAnchoring` (T02, foreign-cwd monkeypatch, absolute registry path), `TestUnknownOptionGuard` (T03, exit 2 behavior lock), `TestDeadCodeRemoved` (T04, attribute-absence guards + surviving-entry-points lock), `TestDeterministicOutput` (T05, byte-identical CLI and schema-validation runs) |
| 2 | Re-run after each seq 01 fix batch until green | Completed | 2026-11-19 | 2026-11-19 | File re-run after each doc 01 removal batch (batch A/B/C gates in doc 01 row 3); final state 23 test functions green, the 13 baseline tests unchanged and green; no fixture files committed (in-memory / `tmp_path` only; `tests/fixtures/` does not exist) |

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
- **Requirement ID**: `REQ-001` (severity consistency), `REQ-002` (cwd-independent paths), `REQ-003` (unknown-option guard), `REQ-004` (dead code), `REQ-005` (deterministic output)
- **Source issue**: issues/20261117-123010_adrchk010_canonical-registry-checkers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-115842_adrchk010_canonical-registry-checkers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-11-19 13:48:55
- **Related target files**: `tests/tools/test_check_canonical_source_registry.py`

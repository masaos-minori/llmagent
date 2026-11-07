# Implementation Procedure: tests/tools/test_check_compat_shims.py

## Goal
Update the checker's test suite to the finalized baseline: 17 `fixture` entries only, doc-claim
self-tests (true positives + historical false negatives), and production-category-zero enforcement
tests.

## Scope
- Target file: `tests/tools/test_check_compat_shims.py` (MODIFY).
- Release unit: `policy-finalization` (lands after compatrm001/002/003 procedure docs execute).
- Related requirement / acceptance criteria: REQ-008 / AC-002 (frozen target row 3);
  supports REQ-002, REQ-003 / AC-001.

## Assumptions
- The checker changes of `implementations/20261107-103000_01_tools_check_compat_shims.py.md` and
  the manifest changes of `implementations/20261107-103000_02_tools_compat_exceptions.toml.md`
  land before or with this change; the test updates match their final shape.
- Manifest parity is 17 `[[compatibility_exceptions]]` entries, all `category = "fixture"`; the
  checker source is permitted by the new `[checker_self_reference]` table, not by a
  `compatibility` entry.
- `tests/conftest.py` puts `tools/` on `sys.path`, so the module imports as `check_compat_shims`.

### Verification findings (adversarial re-verification 2026-11-07, HEAD `be4d74463`; corrected during implementation)

- `TestManifestParity` EXISTS at line 587, pinned to the old 21-path allowlist (including the 3 migration doc paths and `tools/check_compat_shims.py` via the compatibility entry). Step 1 is "rewrite" it: expected allowlist becomes the 18 fixture paths plus `tools/check_compat_shims.py` supplied by the new `[checker_self_reference]` table (19 paths total); the parity class must also assert the entry count (18) and that every category is `fixture`.
- `TestProductionCategoryZero` does NOT exist. `TestManifestValidation` (line 493) covers unknown-category rejection (`category="bogus"`). Step 3 becomes "add" a new class asserting rejection for the valid-but-forbidden categories `migration`, `compatibility`, `fallback` (and unknown `production` still rejected), matching the new stderr message naming the bad id, plus subprocess `main()` exit-code tests.
- Manifest ids do not carry a `fixture-` prefix (e.g. `tool-registry-reset-helper`, `conftest-reset-helper`). The parity class pins entry count, category values, and the path set — not an id prefix. Final manifest state per sibling document 02: 18 `fixture` entries (17 retained + `deploy-init-db-schema-gate-test` for `tests/deploy/test_init_db_schema_gate.py`).
- `check-compat-shims-test-data` (`tests/tools/test_check_compat_shims.py` itself) remains an entry inside the retained 17; the recount lands on 18 with the new entry.

## Design decisions
- Keep the existing approval-subset and syntax-tree-rule tests (they pin `COMPAT_PATTERNS`
  approval-stage entries and the two AST rules) untouched — those checker surfaces are unchanged.
- Rewrite `TestManifestParity` (class at line 587) rather than patch it entry-by-entry: its pins
  (21 paths, `migration-` id prefix, 3 migration docs in the flagged set) all change at once.
- Self-tests use `tmp_path` manifests passed directly to `load_exceptions()` /
  `validate_exceptions()` and direct check-function calls on tmp files (the established pattern in
  this file), plus one subprocess `main()` run for exit-code proof.

## Alternatives considered
- Adding new classes only and leaving `TestManifestParity` pinned to the old 21-entry baseline:
  rejected — the parity class is the regression lock for the manifest and must move with it.
- Driving everything through `main()` subprocesses: rejected for unit-level assertions (slower,
  coarser); subprocess kept only for exit-code and production-category blocking tests.

## Implementation

### Target file
- `tests/tools/test_check_compat_shims.py` (MODIFY).

### Procedure
1. Add `TestManifestParity`: expected entry count 18; all categories equal `fixture`; pinned path
   set = the 18 fixture paths (the 17 retained paths plus `tests/deploy/test_init_db_schema_gate.py`;
   the 3 migration doc paths and the compatibility entry's path are absent); the checker source path
   remains in the flagged set via the `[checker_self_reference]` table read in `load_exceptions()`.
2. Add `TestDocClaimPatterns` (REQ-002 self-tests):
   - True positive: write a tmp `.md` containing each of the five new doc-claim patterns' match
     text in plain present-tense prose. Use synthetic sentences such as "the system applies
     migrations on startup", "the forward migration updates the schema", "the migration ledger
     tracks versions", "the schema migrates forward on open", and "the verified-backup gate
     admits the file"; assert each is flagged by the removed-name check.
   - These synthetic strings are deliberately different from the existing live doc text: the
     checker's historical-context exemption already covers every current migration-claim doc
     (verified 2026-11-07: `--check-removed-names` reports zero findings at HEAD), so reusing
     those sentences in fixtures would assert the opposite of the intended behavior.
   - False-positive guard: write the same synthetic sentences with marker words (`Historical:`,
     `legacy`, `was:`, `removed`, `archive only`, `resolved`) on the same or a preceding line,
     e.g. "removed: the migration ledger tracks versions"; assert zero findings (the
     `_is_historical_context()` 10-line window rule).
3. Add `TestProductionCategoryZero` (REQ-003 / AC-001): a tmp manifest copy with one
   `category = "production"` entry must make `validate_exceptions()` exit non-zero naming the bad
   id; assert the same for `migration`, `compatibility`, and `fallback` values (only `fixture` is
   accepted); a subprocess `main()` run against such a manifest returns exit code 1; the real
   repo manifest passes with exit code 0.
4. Update the fixture-manifest evidence test for `check-compat-shims-test-data` (this file is
   itself an exception entry — unchanged, but recount it inside the 17).
5. Add a checker-self-reference behavior test: with the new `[checker_self_reference]` table the
   checker source stays allowed while doc paths formerly covered by the deleted
   `check-compat-shims-source` entry are no longer exempt (a tmp dirty doc is flagged).

### Method
- Direct function calls with `tmp_path` manifests/files (existing pattern, e.g. the tmp-file
  removed-name tests around lines 643-691); subprocess runs use
  `sys.executable -m tools.check_compat_shims --check-removed-names --check-doc-symbols` with an
  explicit file argument list.

### Details
- `_VALID_CATEGORIES` narrowing (to `fixture` only) happens in the checker doc; this file asserts
  the post-change behavior — do not duplicate the set literal here.
- Historical-marker lines must sit on or above the line containing the retired phrase (the checker
  scans a 10-line window); the false-positive tests encode exactly that layout.
- Fixture strings must not quote live doc sentences (see Design decisions): the live corpus is
  already historical-context-exempt, so quoting it would produce false test failures.

## Compatibility considerations
- The manifest baseline and checker patterns are prerequisites (docs 01, 02 of the same plan).
  Until they land, the rewritten parity class fails — sequenced within one release unit.

## Security considerations
- No new permissions, network, or secret handling. Tests write only under `tmp_path`.

## Rollback considerations
- Test-only change: revert with `git checkout -- tests/tools/test_check_compat_shims.py`. Rollback
  is safe only together with docs 01/02 (same unit).

## Validation plan
- Targeted: `uv run pytest tests/tools/test_check_compat_shims.py -v`.
- Full: `uv run pytest` (no cross-suite coupling expected).

## Completion criteria
- All tests pass against the post-doc01/doc02 checker + manifest state; 17-entry parity pinned;
  true-positive and historical false-negative self-tests green; production-category manifests
  rejected with non-zero exit.

## Out of Scope
- The repository-wide initiative gate (own target row:
  `tests/tools/test_no_compatibility_policy_gate.py`).
- Any checker or manifest content changes (docs 01, 02).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite TestManifestParity (18 fixture entries + checker self-reference; no id prefix) | Completed | 20261107-184026 | 20261107-184026 | 18 fixture entries + self-ref, no id prefix |
| 2 | TestDocClaimPatterns | Completed | 20261107-184026 | 20261107-184026 | true positive + historical guard |
| 3 | TestProductionCategoryZero | Completed | 20261107-184026 | 20261107-184026 | incl. subprocess exit codes |
| 4 | Fixture-entry recount | Completed | 20261107-184026 | 20261107-184026 | `check-compat-shims-test-data` |
| 5 | Checker-self-reference behavior test | Completed | 20261107-184026 | 20261107-184026 | via `[checker_self_reference]` |
### Blocker Log
- None.

### Work Items Created
- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-008 / AC-002
- **Source issue**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-064415_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-103000
- **Related target files**: `tests/tools/test_check_compat_shims.py`
- **Companion**: `tools/check_compat_shims.py`, `tools/compat_exceptions.toml`
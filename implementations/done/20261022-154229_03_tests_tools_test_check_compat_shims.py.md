## Goal

Add regression coverage for the new behavior in `tests/tools/test_check_compat_shims.py`: manifest validation, expiry failure, migration parity, the report-only symbol stage, valid-reference and historical-context cases, while keeping the existing 41 tests passing unchanged (REQ-006; AC-5).

## Scope

- Modify `tests/tools/test_check_compat_shims.py` only.
- Add new test functions/classes; do not alter the existing 41 tests.

## Assumptions

- Existing imports (`check_all`, `main`, `ROOT_DIR`, `pytest`) stay; new tests import `load_exceptions`, `validate_exceptions`, `check_doc_symbols` from `tools.check_compat_shims` and `check_function_references` from `tools._docs_consistency_lib`.
- The live repository manifest has 20 valid entries.

## Design decisions

- Use temporary manifests (via `tmp_path`) for the validation/expiry cases so no fixture file lingers.
- Keep the live-manifest parity check as one test comparing loaded paths to the 20 needed paths.

## Alternatives considered

- Hard-coding the 20 paths in the test — rejected: a parity test against the live manifest catches drift when the corpus changes.

## Implementation

### Target file

`tests/tools/test_check_compat_shims.py`

### Procedure

1. Extend the imports to bring in `load_exceptions`, `validate_exceptions`, `check_doc_symbols`.
2. Add a manifest-validation test class covering missing field, bad category, bad date, duplicate id, and expired entry.
3. Add a parity test asserting the loaded paths equal the 20 needed paths.
4. Add symbol-stage tests: stale reference reported, defined function not reported, historical-context line not reported, allowance not reported.
5. Run the targeted suite and the full suite.

### Method

- Manifest validation: write a TOML string to `tmp_path / "compat_exceptions.toml"`, call `validate_exceptions(load_exceptions(path)[0])`, and assert it flags the defect (e.g. an `expires` earlier than today fails with exit code 1 naming the id).
- Parity: `paths = load_exceptions(ROOT_DIR / "tools" / "compat_exceptions.toml")[1]`; assert it equals the expected 20-path set.
- Symbol stage: build a temp docs dir with a doc naming a deleted function (modeled on the former Glossary example), a doc naming a `scripts/`-defined function, a historical-context line, and an allowance; assert only the stale reference surfaces as a `WARNING`.

### Details

- The existing 41 tests span 8 classes (`TestRootDirResolution`, `TestPatternDetection`, `TestAdrProhibitedPatterns`, `TestDirectoryPositionalArgument`, `TestWorkflowEnforcementPatterns`, `TestRemovedNameReintroduction`, `TestRemovedCommandNamePatterns`, `TestCheckAllRemovedNamesGating`) and must keep passing.
- Live-repository smoke: `--check-doc-symbols` prints Warnings and exits 0; the corpus yields 12 findings before post-filtering.

## Compatibility considerations

N/A: test-only change; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is added.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/tools/test_check_compat_shims.py` | Unit | `uv run pytest tests/tools/test_check_compat_shims.py -q`; `uv run pytest -q` | New tests pass; the 41 existing tests pass unchanged |

## Completion criteria

`pytest tests/tools/test_check_compat_shims.py -q` passes with the 41 existing tests unchanged plus the new manifest-validation, parity, and symbol-stage tests; the full suite `pytest -q` passes.

## Out of Scope

- Changing the behavior under test (that belongs to `tools/check_compat_shims.py`).
- Modifying any other test file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add manifest, expiry, parity, and symbol-stage tests | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (regression tests for manifest validation, expiry, parity, stale/valid/historical reference cases)
- **Source issue**: `issues/20261022-124220_compatexp_add-expiring-compat-exceptions-and-symbol-check.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130804_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-154229
- **Related target files**: `tests/tools/test_check_compat_shims.py`

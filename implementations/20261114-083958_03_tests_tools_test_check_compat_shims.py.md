## Goal

Add the positive, negative, scope, and two-line tests for the eleven patterns and re-point the fixtures that use the retired historical markers (REQ-003, REQ-002, REQ-004 / AC-1 to AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Fixture phrases are built by concatenation (for example two string literals joined at runtime) so this test file needs no new entry in `tools/compat_exceptions.toml` (REQ-003).
- Positive fixtures write into a `tmp_path` layout that mimics the pattern's scope prefix, so the scope filtering is exercised.

## Design decisions
- One parametrized positive test over `LEFTOVER_PHRASES (new)` asserts `check_all` reports an issue naming the pattern and that `main()` exits 1 on such a file (AC-1).
- The two-line case splits `mirror... exactly` over adjacent lines and asserts the join reports it (AC-2).

## Alternatives considered
- New manifest entries for the fixture phrases: rejected; concatenation keeps the manifest untouched (Plan Design).

## Implementation
### Target file
`tests/tools/test_check_compat_shims.py`
### Procedure
Update the marker-dependent fixtures, add the new test classes, then run the test file.
### Method
Extend the existing test-file style (`tmp_path` fixtures, `check_all` assertions).
### Details
- Lines 386-402: the `_update_null_fill` historical-context fixtures write `**Status**: resolved`; `resolved` leaves the marker set, so switch these fixtures to a `removed` context (the flagging test is unchanged).
- Lines 427-432: the `ToolRouteResolver` section exemption fixture titles the section `## ToolRouteResolver (historical)`; `historical` leaves the set, so retitle with a `removed` marker and keep the exemption assertions.
- Lines 511-514: the slash-command exemption fixture writes `**Status**: resolved`; switch to a `removed` context (AC-4).
- New: parametrized positive test over every entry of `LEFTOVER_PHRASES (new)` built by concatenation under a `tmp_path` mimicking `scripts/...` (AC-1); the adjacent-line split case for `mirror... exactly` (AC-2); negative tests that bare bypass text outside `scripts/rag/`, "replaces the oldest turns", and unrelated additive prose produce no issue, plus one scope test writing an in-scope phrase outside its prefix (AC-3); an assertion that the reduced marker set equals `legacy` and `removed` (AC-4).

## Compatibility considerations
- Test-only change; no production import path changes.

## Security considerations
- N/A: test data is concatenated literals.

## Rollback considerations
- Revert the test file; no production dependency.

## Validation plan
- `uv run pytest tests/tools/test_check_compat_shims.py` passes.
- `uv run python tools/check_compat_shims.py --check-removed-names` still reports no finding on the live documents (AC-4).
- The parametrized run covers all eleven patterns (count matches the table).

## Completion criteria
- AC-1 to AC-4 fixtures exist and pass; the file needs no `compat_exceptions.toml` change.

## Out of Scope
- The helper, checker, descriptions, and path-filter rows are their own procedures. Phase 4 of the Plan (live-repository smoke run) is executed only after the sweep Plan's procedures have run; any pattern with a residual match is removed from this change and reported, never exempted (REQ-007, UNK-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-003, REQ-002, REQ-004
- **Source issue**: issues/done/20261110-171157_rmcompat008_compat-checker-patterns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122408_rmcompat008_compat-checker-patterns.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-083958
- **Related target files**: `tests/tools/test_check_compat_shims.py`

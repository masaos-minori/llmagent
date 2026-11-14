## Goal

Run the helper check from `check_all` and reduce `_HISTORICAL_CONTEXT_MARKERS` from twelve entries to `legacy` and `removed` (REQ-001, REQ-004 / AC-1, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The helper row (`tools/_compat_leftover_phrases.py (new)`) lands first; this edit is an import plus one call line.
- `tools/compat_exceptions.toml` is not edited: the new patterns need no fixture entries because the fixtures live in the test file built by concatenation and the checker source stays self-safe.

## Design decisions
- The call is always-on inside `check_all` (like the two syntax-tree rules), not behind a flag: re-adding a leftover phrase in scope must make `main()` exit non-zero (REQ-001).
- Net size stays at or under the recorded ceiling: the import and call line are offset by removing ten marker entries and the comment block from the frozen set.

## Alternatives considered
- Gating the call behind `include_removed_names`: rejected; the Issue requires the phrases to fail by default like every `COMPAT_PATTERNS` entry.

## Implementation
### Target file
`tools/check_compat_shims.py`
### Procedure
Apply the edits listed in Details in file order, then run the unit tests and both static gates.
### Method
Add `from tools._compat_leftover_phrases import check_leftover_phrases (new)` to the module imports; edit the frozen set; extend `check_all`.
### Details
- Lines 344-363: `_HISTORICAL_CONTEXT_MARKERS` holds twelve entries (`legacy`, `historical`, `archive only`, `resolved`, `was:`, `removed`, and the six Japanese entries `解消`, `解決`, `廃止`, `撤廃`, `削除済み`, `確認済み`) plus the mixed-language comment block: reduce the set to `legacy` and `removed` and rewrite the comment to state that the remaining markers had no live finding after the migration and sweep cleanups (Plan Step 1 re-measures on the live documents first; REQ-004 / AC-4).
- Line 494: the sole consumer of the set inside the historical-context window test of `check_removed_name_reintroduction()` needs no change.
- Lines 657-689: `check_all` combines `check_compat_patterns`, `check_adr_prohibited_patterns`, and the two always-on syntax-tree rules: append `check_leftover_phrases(content, filepath, allowlist)` to the always-on combination after `check_adr_prohibited_patterns` and mention the phrase check in the docstring's summary.

## Compatibility considerations
- The exit-code contract is unchanged (non-zero on any issue); the bare default invocation gains the new findings source. Phase 4 of the Plan (live-repository smoke run) is executed only after the sweep Plan's procedures have run; any pattern with a residual match is removed from this change and reported, never exempted (REQ-007, UNK-04).

## Security considerations
- N/A: no new input handling; the file is not deployed.

## Rollback considerations
- Revert the import, the call, and the frozen-set edit; the marker reduction is independent of the helper call.

## Validation plan
- `uv run pytest tests/tools/test_check_compat_shims.py` passes with the new fixtures.
- `uv run python tools/check_compat_shims.py --check-removed-names` reports no finding on the live documents with the reduced set (AC-4).
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` keeps the file at or below its recorded ceiling.
- `uv run ruff check tools/check_compat_shims.py` and `uv run mypy tools/check_compat_shims.py` are clean.

## Completion criteria
- `_HISTORICAL_CONTEXT_MARKERS == frozenset({"legacy", "removed"})`, `check_all` returns phrase issues for in-scope fixture text, and the size gate passes.

## Out of Scope
- The test fixtures, tool descriptions, and path filters are their own rows. Phase 4 of the Plan (live-repository smoke run) is executed only after the sweep Plan's procedures have run; any pattern with a residual match is removed from this change and reported, never exempted (REQ-007, UNK-04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261115 | 20261115 | Import moved into the tools. import block; _HISTORICAL_CONTEXT_MARKERS reduced to {legacy, removed}; wired into check_all; sys.path insert block kept before the new import |
| 2 | Add or update tests per Validation plan | N/A | — | — | Tests consolidated in the single-directory batch (procedure 03) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261115 | 20261115 | ruff check and mypy clean; file at 36241 B ≤ 36243 ceiling; removed-name smoke run reports no finding; full suite 12199 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Documentation handled by procedure 04 |

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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/done/20261110-171157_rmcompat008_compat-checker-patterns.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-122408_rmcompat008_compat-checker-patterns.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-083958
- **Related target files**: `tools/check_compat_shims.py`

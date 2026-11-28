## Goal

Make `tools/check_test_taxonomy.py` judge the MDQ test modules as a classified area, so the classification rule (`REQ-003`, machine-readable test classification) applies to `tests/mcp_servers/mdq/` instead of only reporting modules that already carry a marker (`AC-3`).

## Scope
**Release unit**: mdq-taxonomy-gate

- One tuple element is added to `CLASSIFIED_AREAS`; the matching logic, the categories, the baseline handling, and the report rendering are unchanged.
- The area is activated in the same commit as the markers on the 38 modules (plan Phase 4), because the area reports `unclassified-module` for a module that has no marker.

## Assumptions

- At current HEAD `CLASSIFIED_AREAS` is at line 66 and `in_classified_area()` is at line 223. The
  plan recorded 219 for the function at the evidence revision; the procedure cites the current
  position, and the difference is a line shift, not a rule change.
- `in_classified_area()` matches by prefix (`module_path.startswith(f"{area}/")`), so the entry is written as `tests/mcp_servers/mdq` and matches every module under it.
- `tests/tools/test_check_test_taxonomy.py` builds its own temporary root and never asserts the contents of `CLASSIFIED_AREAS`; its findings are produced from paths under `tests/agent/`, so the addition keeps that module green.
- No MDQ module is added to `tools/test_taxonomy_baseline.txt`, which has no MDQ entry today, because the baseline is for modules that cannot be classified.

## Design decisions

- Add the area rather than seed the baseline: the baseline records modules that cannot be classified, and every MDQ module can be, so a baseline entry would hide the gap the plan is closing.
- Keep `CLASSIFIED_AREAS` a tuple of repository-relative prefixes, consistent with the existing entries, so the CI report step (`--junit-xml`) groups the MDQ modules into the contract and characterization sections without a new grouping rule (`AC-6`).

## Alternatives considered

- Add the 38 modules to the baseline instead: rejected, it contradicts the plan's stated intent that every MDQ module is classifiable.
- Widen the rule to classify every `tests/` module: rejected, it would report findings for areas the plan does not own.

## Implementation
### Target file
`tools/check_test_taxonomy.py`

### Procedure
1. Add `tests/mcp_servers/mdq` to `CLASSIFIED_AREAS` (line 66).

### Method

- The tuple is written across continuation lines to stay inside `line-length = 88` (`pyproject.toml:99`), because `("tests/agent", "tests/shared", "tests/mcp_servers/mdq")` on one line exceeds the limit.
- Land this change in the same commit as the markers on the 35 modules (the plan's `mdq-taxonomy-gate` release unit), so the gate does not report `unclassified-module` for a module that has no marker.

### Details

- Entry order: appended after the two existing areas, which keeps the existing entries' order stable for `tests/tools/test_check_test_taxonomy.py`.
- `module.path` is relative to `--root`, whose default is the repository root (`_parse_args()`), so the prefix matches the paths the checker reports.

## Compatibility considerations

- The change activates findings for MDQ modules only: once the markers land, `uv run python tools/check_test_taxonomy.py` reports no finding for `tests/mcp_servers/mdq/` (`AC-3`).
- Between the area activation and the marker application the checker reports `unclassified-module` for the 38 modules; that is the reason the plan declares Phase 4 and Phase 5 as one release unit.
- Module size is 17221 B, below the 24576 B gate in `tools/check_module_size.py`.

## Security considerations

- `N/A: static checker configuration only.` No runtime path, scope, or authorization behavior is involved.

## Rollback considerations

- `N/A: revert the commit.` The change is one tuple element with no persisted state.

## Validation plan

- `uv run python tools/check_test_taxonomy.py` — no finding for `tests/mcp_servers/mdq/` (`AC-3`)
- `uv run pytest tests/tools/test_check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`, including `uv run ruff check tools/check_test_taxonomy.py` and `uv run mypy tools/check_test_taxonomy.py`.

## Completion criteria

- `tests/mcp_servers/mdq` is in `CLASSIFIED_AREAS` (`AC-3`).
- Every MDQ module carries exactly one taxonomy marker and every contract module carries a citation, so the checker run reports no finding for the area (`AC-3`).
- No MDQ module appears in `tools/test_taxonomy_baseline.txt` (`AC-3`).
- The CI report step groups the MDQ modules into the two sections and a characterization failure remains report-only (`AC-6`).

## Out of Scope

- The `pytestmark` lines and the 7 citation additions on the 38 modules (plan rows 8 and 11-44, 45-47).
- Any change to the checker's categories, citation forms, or baseline handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 5, same commit as Phase 4 (release unit) |
| 2 | Add or update tests per Validation plan | Pending | — | — | The checker run is the test; `tests/tools/test_check_test_taxonomy.py` is unchanged |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003 (machine-readable test classification), AC-3, AC-6
- **Source issue**: `issues/20261119-142132_mdqmcp010_mdq-release-readiness.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-095153
- **Related target files**: `tools/check_test_taxonomy.py`

## Goal

Fix `GRAPH_DOC_NAME`'s stale filename constant so `GRAPH_DOC_PATH` resolves to the current on-disk `docs/00_governance/governance_01_documentation-policy.md` (REQ-001), fixing `tests/tools/test_check_dependency_graph_cycles.py::TestRealGraphIntegration::test_real_repo_graph_has_no_cycle` and restoring `tools/check_dependency_graph_cycles.py`'s no-argument default resolution used by `.github/workflows/governance-docs-consistency.yml`.

## Scope

In scope: change `GRAPH_DOC_NAME`'s literal string value in `tools/check_dependency_graph_cycles.py` (line 38) from `"00_governance_01_documentation-policy.md"` to `"governance_01_documentation-policy.md"`. Out of scope: `GRAPH_DOC_PATH`'s `DOCS_DIR / "00_governance" / GRAPH_DOC_NAME` construction pattern (already correct), and any other file in this Plan (each has its own implementation procedure document).

## Assumptions

- The docs reorg that renamed `docs/00_governance/00_governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md` is complete and correct (confirmed via `ls docs/00_governance/` showing the new name on disk).
- No other code references `GRAPH_DOC_NAME`'s old literal value directly (only via the `GRAPH_DOC_NAME`/`GRAPH_DOC_PATH` symbols, confirmed via `rg "GRAPH_DOC_NAME|GRAPH_DOC_PATH"` finding only this file and its own test file).

## Design decisions

- Change only the string literal, not the path-construction expression — the `DOCS_DIR / "00_governance" / GRAPH_DOC_NAME` pattern is shared with sibling tools and was deliberately added (per `plans/done/20260924-115855_plan.md`) to survive doc moves; only the filename value drifted.

## Alternatives considered

- Hardcoding the full path directly instead of keeping the `DOCS_DIR / "00_governance" / GRAPH_DOC_NAME` composition: rejected — would diverge from the sibling-tool pattern this file already follows and lose the benefit of a single-point-of-change filename constant.

## Implementation

### Target file

`tools/check_dependency_graph_cycles.py`

### Procedure

1. Open `tools/check_dependency_graph_cycles.py` and locate line 38: `GRAPH_DOC_NAME = "00_governance_01_documentation-policy.md"`.
2. Change the string literal to `"governance_01_documentation-policy.md"`.
3. Leave line 39 (`GRAPH_DOC_PATH = DOCS_DIR / "00_governance" / GRAPH_DOC_NAME`) unchanged.

### Method

Direct string-literal edit (single line), no structural change.

### Details

- Before: `GRAPH_DOC_NAME = "00_governance_01_documentation-policy.md"`
- After: `GRAPH_DOC_NAME = "governance_01_documentation-policy.md"`
- Confirm `docs/00_governance/governance_01_documentation-policy.md` exists on disk before/after the edit (it already does; the edit only updates the constant to match it).

## Compatibility considerations

- `.github/workflows/governance-docs-consistency.yml` invokes this tool with no path argument (line 57), relying on `GRAPH_DOC_PATH`'s default resolution — this fix restores that resolution rather than changing it, so no compatibility impact beyond fixing the currently-broken default.

## Security considerations

N/A: a filename-constant correction in a CI/dev-tooling script; no security-relevant behavior change.

## Rollback considerations

- To rollback: `git revert` the commit containing this change, or manually restore the line to its prior (stale) value. No data migration or state involved — a pure source-code string change.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tools/check_dependency_graph_cycles.py` | Integration: real-repo-path regression test | `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` | All tests pass, including `TestRealGraphIntegration::test_real_repo_graph_has_no_cycle` |
| `tools/check_dependency_graph_cycles.py` | Manual smoke test matching CI invocation | `uv run python tools/check_dependency_graph_cycles.py` (no argument) | Exit 0, no missing-file error |

## Completion criteria

- `uv run pytest tests/tools/test_check_dependency_graph_cycles.py -q` passes with no failures.
- `uv run python tools/check_dependency_graph_cycles.py` (no argument) runs without a missing-file error.

## Out of scope

- Any further `docs/` file renames or restructuring.
- `tools/check_issue_inventory_conformance.py` and `tests/tools/test_check_docs_quality.py` (covered by their own implementation procedure documents from this same Plan).
- Any of the other 96 full-suite test failures tracked under separate issues/plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Changed `GRAPH_DOC_NAME` from `"00_governance_01_documentation-policy.md"` to `"governance_01_documentation-policy.md"` |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed — existing `TestRealGraphIntegration` test already covers this fix once the constant is corrected |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 13 tests pass; smoke test exits 0 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for this tools/ file |

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
- **Requirement ID**: REQ-001: fix `GRAPH_DOC_NAME`'s stale filename constant
- **Source issue**: issues/20260927-075236_docs001_stale-pre-reorg-governance-doc-paths-in-checker-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-080744_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091010
- **Related target files**: tools/check_dependency_graph_cycles.py

## Goal

Fix `GOVERNANCE_DOC_NAME`'s stale filename constant so `GOVERNANCE_DOC_PATH` resolves to the current on-disk `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (REQ-002), fixing `tests/tools/test_check_issue_inventory_conformance.py::TestGovernanceDocPathIntegration::test_governance_doc_path_resolves_on_disk` and restoring `tools/check_issue_inventory_conformance.py`'s no-argument default resolution used by `.github/workflows/governance-docs-consistency.yml`.

## Scope

In scope: change `GOVERNANCE_DOC_NAME`'s literal string value in `tools/check_issue_inventory_conformance.py` (line 61) from `"00_governance_03_issue-and-uncertainty-management.md"` to `"governance_03_issue-and-uncertainty-management.md"`. Out of scope: `GOVERNANCE_DOC_PATH`'s `DOCS_DIR / "00_governance" / GOVERNANCE_DOC_NAME` construction pattern (already correct and deliberately added per `plans/done/20260924-115855_plan.md`), and any other file in this Plan (each has its own implementation procedure document).

## Assumptions

- The docs reorg that renamed `docs/00_governance/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/governance_03_issue-and-uncertainty-management.md` is complete and correct (confirmed via `ls docs/00_governance/` showing the new name on disk).
- No other code references `GOVERNANCE_DOC_NAME`'s old literal value directly (confirmed via `rg "GOVERNANCE_DOC_NAME|GOVERNANCE_DOC_PATH"` finding no matches outside this file's own definition — it is not otherwise referenced elsewhere).

## Design decisions

- Change only the string literal, not the path-construction expression — `plans/done/20260924-115855_plan.md`'s REQ-003 deliberately added this `DOCS_DIR / "00_governance" / GOVERNANCE_DOC_NAME` pattern mirroring `check_dependency_graph_cycles.py`'s `GRAPH_DOC_PATH`; only the filename value drifted after a later docs rename.

## Alternatives considered

- Hardcoding the full path directly instead of keeping the `DOCS_DIR / "00_governance" / GOVERNANCE_DOC_NAME` composition: rejected — would diverge from the sibling-tool pattern this file was specifically designed to mirror.

## Implementation

### Target file

`tools/check_issue_inventory_conformance.py`

### Procedure

1. Open `tools/check_issue_inventory_conformance.py` and locate line 61: `GOVERNANCE_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"`.
2. Change the string literal to `"governance_03_issue-and-uncertainty-management.md"`.
3. Leave line 64 (`GOVERNANCE_DOC_PATH = DOCS_DIR / "00_governance" / GOVERNANCE_DOC_NAME`) unchanged.

### Method

Direct string-literal edit (single line), no structural change.

### Details

- Before: `GOVERNANCE_DOC_NAME = "00_governance_03_issue-and-uncertainty-management.md"`
- After: `GOVERNANCE_DOC_NAME = "governance_03_issue-and-uncertainty-management.md"`
- Confirm `docs/00_governance/governance_03_issue-and-uncertainty-management.md` exists on disk before/after the edit (it already does; the edit only updates the constant to match it).

## Compatibility considerations

- `.github/workflows/governance-docs-consistency.yml` invokes this tool with no path argument (line 52), relying on `GOVERNANCE_DOC_PATH`'s default resolution — this fix restores that resolution rather than changing it, so no compatibility impact beyond fixing the currently-broken default.

## Security considerations

N/A: a filename-constant correction in a CI/dev-tooling script; no security-relevant behavior change.

## Rollback considerations

- To rollback: `git revert` the commit containing this change, or manually restore the line to its prior (stale) value. No data migration or state involved — a pure source-code string change.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tools/check_issue_inventory_conformance.py` | Integration: real-repo-path regression test | `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q` | All tests pass, including `TestGovernanceDocPathIntegration::test_governance_doc_path_resolves_on_disk` |
| `tools/check_issue_inventory_conformance.py` | Manual smoke test matching CI invocation | `uv run python tools/check_issue_inventory_conformance.py` (no argument) | Exit 0, no missing-file error |

## Completion criteria

- `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -q` passes with no failures.
- `uv run python tools/check_issue_inventory_conformance.py` (no argument) runs without a missing-file error.

## Out of scope

- Any further `docs/` file renames or restructuring.
- `tools/check_dependency_graph_cycles.py` and `tests/tools/test_check_docs_quality.py` (covered by their own implementation procedure documents from this same Plan).
- Any of the other 96 full-suite test failures tracked under separate issues/plans.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Changed `GOVERNANCE_DOC_NAME` from `"00_governance_03_issue-and-uncertainty-management.md"` to `"governance_03_issue-and-uncertainty-management.md"` |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no new test needed — existing `TestGovernanceDocPathIntegration` test already covers this fix once the constant is corrected |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | All 21 tests pass; smoke test resolves path correctly (exit 1 = conformance violations found, not missing file) |
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
- **Requirement ID**: REQ-002: fix `GOVERNANCE_DOC_NAME`'s stale filename constant
- **Source issue**: issues/20260927-075236_docs001_stale-pre-reorg-governance-doc-paths-in-checker-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-080744_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091010
- **Related target files**: tools/check_issue_inventory_conformance.py

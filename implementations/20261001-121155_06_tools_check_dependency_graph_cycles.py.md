## Goal
- Point the graph cycle checker at the new document (REQ-006).

## Scope
- In: the changes listed under Implementation > Details in `tools/check_dependency_graph_cycles.py`.
- Out: every other file and every unlisted part of `tools/check_dependency_graph_cycles.py`.

## Assumptions
- `GRAPH_DOC_NAME = "governance_01_documentation-policy.md"`, `GRAPH_DOC_PATH = DOCS_DIR / "00_governance" / GRAPH_DOC_NAME`, `TARGET_SECTION = "Software Runtime Dependency Graph"` (re-verified 2026-10-01); error messages interpolate `GRAPH_DOC_NAME`.
- The module docstring's first paragraph names `docs/00_governance_01_documentation-policy.md`.
- Baseline: radon `main` grade C (16); vulture and bandit clean; tests 13 passed; tool exit 0.
- The CI workflow `.github/workflows/governance-docs-consistency.yml` runs the tool without a path argument; no CI change needed.
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Change only the constant and the docstring path; `TARGET_SECTION` and parsing logic stay unchanged.

## Alternatives considered
- Search all governance docs for the section: rejected — broader behavior change than the relocation requires.

## Implementation
### Target file
- `tools/check_dependency_graph_cycles.py`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff tools/check_dependency_graph_cycles.py` that nothing outside Details changed.

### Details
- Set `GRAPH_DOC_NAME = "governance_05_change-impact-and-dependency-graphs.md"`.
- Docstring: replace `docs/00_governance_01_documentation-policy.md's` with `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md's`.
- Run only after seq 02 created the new document; the Policy still contains the section until seq 01 Part B, so both states pass.

## Compatibility considerations
- `tests/tools/test_check_dependency_graph_cycles.py` imports `GRAPH_DOC_NAME`/`GRAPH_DOC_PATH`; behavior follows automatically.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- tools/check_dependency_graph_cycles.py` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `uv run python tools/check_dependency_graph_cycles.py` — exit 0.
- `uv run pytest tests/tools/test_check_dependency_graph_cycles.py` — 13 passed.
- `uv run ruff format tools/check_dependency_graph_cycles.py`, `uv run ruff check tools/check_dependency_graph_cycles.py`, `uv run mypy tools/check_dependency_graph_cycles.py`, `uv run bandit tools/check_dependency_graph_cycles.py` — clean.
- `uv run radon cc tools/check_dependency_graph_cycles.py -s -n C` — `main` still C (16), no new block.

## Completion criteria
- Constant and docstring point to the new document; all validations pass.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm seq 02 Completed | Pending | — | — | |
| 2 | Change GRAPH_DOC_NAME and docstring | Pending | — | — | |
| 3 | Run tool, tests, ruff, mypy, bandit, radon | Pending | — | — | |

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
- **Requirement ID**: REQ-006 (graph checker reads the new document) — Plan Implementation steps Step 4
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: tools/check_dependency_graph_cycles.py

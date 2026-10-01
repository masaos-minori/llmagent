## Goal
- Update the test docstrings that name the Policy as the graph location (REQ-006).

## Scope
- In: the changes listed under Implementation > Details in `tests/tools/test_check_dependency_graph_cycles.py`.
- Out: every other file and every unlisted part of `tests/tools/test_check_dependency_graph_cycles.py`.

## Assumptions
- The module docstring ('TestRealGraphIntegration ... reads the actual current docs/00_governance_01_documentation-policy.md') and the `TestRealGraphIntegration` class docstring ('Exercises the parser against docs/00_governance_01_documentation-policy.md's actual current content') name the Policy (re-verified 2026-10-01).
- Test behavior already follows the tool constants via import; no assertion changes are needed.
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Docstring-only change; no test logic change.

## Alternatives considered
- Add a new test asserting the new file name: rejected — `TestRealGraphIntegration` already fails if the configured document lacks the section.

## Implementation
### Target file
- `tests/tools/test_check_dependency_graph_cycles.py`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff tests/tools/test_check_dependency_graph_cycles.py` that nothing outside Details changed.

### Details
- Replace both occurrences of `docs/00_governance_01_documentation-policy.md` with `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`.

## Compatibility considerations
- None beyond docstrings.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- tests/tools/test_check_dependency_graph_cycles.py` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `uv run pytest tests/tools/test_check_dependency_graph_cycles.py` — 13 passed.
- `uv run ruff check tests/tools/test_check_dependency_graph_cycles.py` and `uv run ruff format --check tests/tools/test_check_dependency_graph_cycles.py` — clean.

## Completion criteria
- No docstring names the Policy as the graph location; tests pass.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the two docstrings | Completed | 20261001-154910 | 20261001-154950 | Changed tests/tools/test_check_dependency_graph_cycles.py docstrings only. Docs N/A: no task-scope row. |
| 2 | Run pytest and ruff | Completed | 20261001-154910 | 20261001-154955 | 13 passed and ruff clean. Final full suite run follows seq 05. |

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
- **Requirement ID**: REQ-006 (docstrings name the new graph location) — Plan Implementation steps Step 4
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: tests/tools/test_check_dependency_graph_cycles.py
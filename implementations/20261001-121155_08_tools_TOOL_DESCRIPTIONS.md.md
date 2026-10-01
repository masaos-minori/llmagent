## Goal
- Update the tool description row that names the graph's source document (REQ-006).

## Scope
- In: the changes listed under Implementation > Details in `tools/TOOL_DESCRIPTIONS.md`.
- Out: every other file and every unlisted part of `tools/TOOL_DESCRIPTIONS.md`.

## Assumptions
- Only the detailed-table row for `check_dependency_graph_cycles.py` names `docs/00_governance_01_documentation-policy.md`; the summary-table row ('依存性チェック | ソフトウェアランタイム依存グラフの循環検出') names no document (Plan corrected in Step 3a).
- `tools/TOOL_DESCRIPTIONS.md` is written in Japanese and is outside `docs/` (the English-only rule does not apply); keep its language.
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Replace only the document path in that row.

## Alternatives considered
- N/A: one path substitution.

## Implementation
### Target file
- `tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff tools/TOOL_DESCRIPTIONS.md` that nothing outside Details changed.

### Details
- In the detailed-table row, replace `docs/00_governance_01_documentation-policy.md` with `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`; keep the rest of the row unchanged.

## Compatibility considerations
- `tools/check_tool_descriptions_sync.py` checks tool-name rows, not paths; it must still pass.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- tools/TOOL_DESCRIPTIONS.md` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` — pass.
- `grep -n 'governance_01_documentation-policy' tools/TOOL_DESCRIPTIONS.md` — no line for `check_dependency_graph_cycles.py`.

## Completion criteria
- The row names the new document; sync check passes.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the path in the detailed-table row | Completed | 20261001-155000 | 20261001-155030 | Changed tools/TOOL_DESCRIPTIONS.md one path. Docs N/A: no task-scope row. |
| 2 | Run the sync check | Completed | 20261001-155000 | 20261001-155030 | Sync check passed. Final full suite run follows seq 05. |

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
- **Requirement ID**: REQ-006 (tool description names the new document) — Plan Implementation steps Step 4
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
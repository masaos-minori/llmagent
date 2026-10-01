## Goal
- Bring the Policy to at most 24576 bytes by removing 9 in-file duplicate sentences (REQ-001) and the 8 relocated sections, replaced by one pointer section (REQ-003), with no checker regression (REQ-007).

## Scope
- In: the changes listed under Implementation > Details in `docs/00_governance/governance_01_documentation-policy.md`.
- Out: every other file and every unlisted part of `docs/00_governance/governance_01_documentation-policy.md`.

## Assumptions
- State re-verified 2026-10-01: 31309 bytes; the 9 duplicate sentences are the trailing 'Canonical source kind: ...; conflict destination: ...' sentences in the `### external-behavior`, `### api-contract`, `### production-effective-value`, `### configuration-schema`, `### database-schema`, `### operational-procedure`, `### security-policy`, `### documentation-metadata`, `### unconfirmed-claim` subsections (the other 4 subsections carry 'Boundary against' sentences instead and keep them).
- Moved sections (bytes incl. heading): Update Rule 931, Change Impact Rule 1221, Change-Impact Matrix 455, RACI Model 687, Software Runtime Dependency Graph 2276, Deployment Management Graph 440, Documentation Reference Graph 501, Governance Applicability Matrix 661.
- Policy-internal references to moved content outside the moved sections: `## Purpose` ('... and dependency graph management'), 'RACI approval' in `### ADR Acceptance Evidence Standard` and `## Merge Conditions` (twice), `## Keywords` ('dependency graph', 'RACI'). The `## ADR Section Header Standardization` mention of 'dependency graph' refers to the ADR index and is unrelated.
- Part B depends on Plan Step 3 (seq 02 created the new document) and Step 4 (seq 06 repointed the graph checker) being Completed; otherwise `check_dependency_graph_cycles.py` would fail.
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Remove only sentences duplicated in `### Resolution Matrix`; keep each subsection's definition sentence and every 'Boundary against' sentence.
- One pointer section `## Change Impact and Dependency Graphs` at the former `## Update Rule` position (before `## Review Rule`), which also states where the RACI Model referenced by 'RACI approval' is defined; do not add per-occurrence links (keeps bytes low).
- Do not touch `## Area Canonical Maps` (`canon001`), `## ADR Section Header Standardization` (`langdoc001`), `## Merge Conditions` / `## Non-Goals` / `## Related Documents` bodies other than adding one Related Documents bullet (cross-file assertion in `tests/tools/test_check_docs_quality.py`).

## Alternatives considered
- Link every 'RACI' mention individually: rejected — adds bytes and churn for no extra clarity once the pointer section names the location.

## Implementation
### Target file
- `docs/00_governance/governance_01_documentation-policy.md`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff docs/00_governance/governance_01_documentation-policy.md` that nothing outside Details changed.

### Details
- Part A (Plan Step 2): delete the trailing sentence starting ' Canonical source kind:' from each of the 9 subsections listed in Assumptions, keeping the preceding sentence unchanged.
- Before Part B: save the 8 moved section bodies (heading line to the line before the next `## `) to a scratch file for the byte comparison done in seq 02's validation.
- Part B (Plan Step 5): delete the 8 sections `## Update Rule`, `## Change Impact Rule`, `## Change-Impact Matrix`, `## RACI Model`, `## Software Runtime Dependency Graph`, `## Deployment Management Graph`, `## Documentation Reference Graph`, `## Governance Applicability Matrix`.
- Insert before `## Review Rule`: `## Change Impact and Dependency Graphs` followed by one paragraph: 'The Update Rule, Change Impact Rule, Change-Impact Matrix, RACI Model (the accountable-party model behind "RACI approval" in `## Merge Conditions` and `### ADR Acceptance Evidence Standard`), and the dependency-graph taxonomy (Software Runtime Dependency Graph, Deployment Management Graph, Documentation Reference Graph, Governance Applicability Matrix) are defined in [Change Impact and Dependency Graphs](governance_05_change-impact-and-dependency-graphs.md).'
- `## Purpose`: replace '... ADR conventions, and dependency graph management.' with '... and ADR conventions; change-impact rules and dependency graphs are defined in [Change Impact and Dependency Graphs](governance_05_change-impact-and-dependency-graphs.md).'
- `## Related Documents`: append `- [Change Impact and Dependency Graphs](governance_05_change-impact-and-dependency-graphs.md)`.
- `## Keywords`: remove the `dependency graph` line (moved to the new document); keep `RACI` (still used in this document).

## Compatibility considerations
- `tools/check_dependency_graph_cycles.py` must already read the new document (seq 06) before Part B removes the graph from this file.
- `tests/tools/test_check_docs_quality.py` snapshot rows for this file come only from `## Area Canonical Maps` subsections, which are untouched; the governance_01/governance_04 cross-file finding comes from `## Non-Goals` / `## Related Documents`, also kept.
- `canon001`, `govpath001`, `langdoc001` (procedure `implementations/20261001-120650_14_...`) edit other parts of this file; rebase before Part B.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_01_documentation-policy.md` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `wc -c docs/00_governance/governance_01_documentation-policy.md` — at most 24576 (expected about 23.8 KB).
- `grep -c 'Canonical source kind:' docs/00_governance/governance_01_documentation-policy.md` — 0.
- `uv run python tools/check_docs_structure.py "docs/00_governance/*.md"` — no size finding; no new finding.
- `uv run python tools/check_docs_quality.py` — no new line for this file (baseline 14); `uv run pytest tests/tools/test_check_docs_quality.py` — still only the pre-existing `05_agent_*` failure; governance_01/governance_04 cross-file assertion holds.
- `uv run python tools/check_dependency_graph_cycles.py` — exit 0 (after seq 06).
- `grep -n -E '^## (Update Rule|Change Impact Rule|Change-Impact Matrix|RACI Model|Software Runtime Dependency Graph|Deployment Management Graph|Documentation Reference Graph|Governance Applicability Matrix)$' docs/00_governance/governance_01_documentation-policy.md` — no output.

## Completion criteria
- File size at most 24576 bytes.
- 9 duplicate sentences removed; definitions and Boundary sentences unchanged.
- 8 sections removed; pointer section, Purpose, Related Documents, and Keywords updated as specified; no other change.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Part A: remove 9 duplicate sentences (Plan Step 2) | Pending | — | — | |
| 2 | Save the 8 moved section bodies for byte comparison | Pending | — | — | |
| 3 | Confirm seq 02 and seq 06 Completed | Pending | — | — | |
| 4 | Part B: remove 8 sections; add pointer, Purpose, Related Documents, Keywords edits (Plan Step 5) | Pending | — | — | |
| 5 | Run Validation plan and record size | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-007 (de-duplicate; remove moved sections and add pointer; no regression) — Plan Implementation steps Step 2 (Part A) and 5 (Part B)
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md

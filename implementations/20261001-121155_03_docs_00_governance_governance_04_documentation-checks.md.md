## Goal
- Repoint every statement in the Documentation Checks document that locates a moved section in the Policy to the new document (REQ-004).

## Scope
- In: the changes listed under Implementation > Details in `docs/00_governance/governance_04_documentation-checks.md`.
- Out: every other file and every unlisted part of `docs/00_governance/governance_04_documentation-checks.md`.

## Assumptions
- Current references (re-verified 2026-10-01): `### 12. Area Dependency Graph Validation` names `docs/governance_01_documentation-policy.md` three times; `GV-015` (item 4 of the follow-up list) names `docs/governance_01_documentation-policy.md`'s four relation-type sections; `## Change Impact Assessment` links `governance_01_documentation-policy.md#change-impact-rule`.
- Execution order across this Plan's procedures follows Plan Implementation steps: Step 1 baseline -> Step 2 (seq 01 Part A) -> Step 3 (seq 02) -> Step 4 (seq 06, 07, 08) -> Step 5 (seq 01 Part B) -> Step 6 (seq 03) -> Step 7 (seq 04, 05) -> Step 8 verification.

## Design decisions
- Use the correct path `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md` in new text (do not copy the directory-less form).
- Do not touch other occurrences of the directory-less `docs/governance_0N_*` form (owned by `govpath001`).

## Alternatives considered
- Leave GV-015 unchanged as a historical record: rejected — it states the current location of the four sections as fact (Current-Specification-Only Policy).

## Implementation
### Target file
- `docs/00_governance/governance_04_documentation-checks.md`

### Procedure
1. Confirm the prerequisite procedures named in Assumptions are Completed.
2. Apply the changes in Details, in the listed order.
3. Run the Validation plan and compare with the Plan Design baseline.
4. Record results in Execution Status Notes.

### Method
- Targeted edits only; confirm with `git diff docs/00_governance/governance_04_documentation-checks.md` that nothing outside Details changed.

### Details
- `### 12. Area Dependency Graph Validation`: replace the three occurrences of `docs/governance_01_documentation-policy.md` with `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`.
- GV-015: replace `` `docs/governance_01_documentation-policy.md`'s `` with `` `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`'s ``.
- `## Change Impact Assessment`: change the link to `[Change Impact Rule and Change-Impact Matrix](governance_05_change-impact-and-dependency-graphs.md#change-impact-rule)` (drop the word 'Policy's').
- Do not edit `## Merge Condition Validation` or other sections.

## Compatibility considerations
- The governance_01/governance_04 cross-file similarity asserted by `tests/tools/test_check_docs_quality.py` comes from `## Non-Goals` / `## Related Documents`; untouched.

## Security considerations
- N/A: documentation/tool path change only; no secrets, network access, or runtime behavior beyond which file the checker reads.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_04_documentation-checks.md` (or delete the file if newly created). Revert seq 01 Part B before seq 02/06 to keep the graph checker passing.

## Validation plan
- `grep -n 'governance_01_documentation-policy.md' docs/00_governance/governance_04_documentation-checks.md` — no remaining line that locates a moved section (remaining lines, if any, refer to sections still in the Policy).
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md` — no new finding; the `#change-impact-rule` anchor resolves.
- `uv run python tools/check_docs_quality.py` — no new line for this file (baseline 5).

## Completion criteria
- All three reference sites point to the new document; links resolve; no other change.

## Out of scope
- Rule wording changes; stale-path cleanup (`govpath001`); `## Area Canonical Maps` (`canon001`); ADR quotes (`langdoc001`); the external-behavior matrix discrepancy (`issues/20261001-112149_unknowns.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm seq 02 (new document) Completed | Pending | — | — | |
| 2 | Edit ### 12, GV-015, and Change Impact Assessment link | Pending | — | — | |
| 3 | Run Validation plan | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (repoint references to moved sections) — Plan Implementation steps Step 6
- **Source issue**: issues/20261001-104656_docsize001_reduce-documentation-policy-below-structure-size-limit.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-112149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-121155
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md

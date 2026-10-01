## Goal
- REQ-006: replace the three Japanese ADR boilerplate quotes with the translated English boilerplate; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/00_governance/governance_01_documentation-policy.md`.
- Out: every other line of `docs/00_governance/governance_01_documentation-policy.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- Prerequisite gate: `plans/done/20261001-105822_plan.md` (langadr001) Execution Status Steps 2-16 must be `Completed` (ADR H1 titles, boilerplate, and ADR-008 Assumptions translated) before this procedure starts. If not, record the blocker in Blocker Log and stop; do not translate independently (Plan Blocker Log, Steps 6-7).

## Design decisions
- Single source: the ADR text after translation; the Policy quotes it so a grep finds both.
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- Keep the existing English glosses: rejected — they differ from the wording langadr001 specifies for bullets 1 and 3, which would leave the Policy quoting text no ADR contains.

## Implementation
### Target file
- `docs/00_governance/governance_01_documentation-policy.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/00_governance/governance_01_documentation-policy.md` that only the listed lines changed.

### Details
- Current lines:
  - 389: `- "この章は設計判断の根拠にしない" (Do not use this chapter as the basis for design decisions)`
  - 390: `- "該当しない場合は「対象外」と記載する" (If not applicable, write "Not applicable")`
  - 391: `- "ADR本文を現行実装へ無条件に合わせず、差異はKnown Issueで管理する" (Do not unconditionally align ADR text to current implementation; manage discrepancies via Known Issues)`
- Change:
  - Replace each bullet with a single English quote copied verbatim from the translated ADR boilerplate (e.g. from `docs/10_adr/ADR-001-workflow-engine-mandatory.md` `## Implementation Notes` / `## Known Deviations`), dropping the Japanese text and the parenthetical gloss.
  - Note: the langadr001 procedures fix the boilerplate wording as 'This chapter is not a basis for design decisions.' / 'If not applicable, write "Not applicable".' / 'Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.' — but their statement that this matches these existing glosses is inaccurate for bullets 1 and 3. The ADR text actually produced by langadr001 is authoritative; copy it, not the old glosses.

## Compatibility considerations
- `docsize001` (`plans/20261001-112149_plan.md`), `canon001`, and `govpath001` also edit this file; `## ADR Section Header Standardization` is not moved by docsize001. Rebase before editing and change only lines 389-391 (Plan Risks).
- `tests/tools/test_check_docs_quality.py` expects governance_01 within-file pairs from `## Area Canonical Maps` only; this section is not involved.

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_01_documentation-policy.md`; no other file in this Plan depends on this edit.

## Validation plan
- `uv run python tools/check_docs_japanese.py` — file not listed.
- Full-width grep (AC-007 pattern) on the file — no output.
- `grep -F` of each new quote in `docs/10_adr/ADR-001-workflow-engine-mandatory.md` (or another ADR containing it) — match found.
- `uv run python tools/check_docs_quality.py` — no new line for this file (baseline 14); `uv run pytest tests/tools/test_check_docs_quality.py` — no new Added/Removed entry for this file.

## Completion criteria
- The three bullets quote the translated ADR boilerplate verbatim; no Japanese characters remain.
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm prerequisite gate (langadr001 Steps 2-16 Completed) | Completed | 20261001-142055 | 20261001-142055 |  |
| 2 | Apply the change in Implementation > Details | Completed | 20261001-142055 | 20261001-142055 |  |
| 3 | Run the Validation plan and compare with the Plan Design baseline | Completed | 20261001-142055 | 20261001-142055 |  |
| 4 | Self-review meaning and record result in Notes | Completed | 20261001-142055 | 20261001-142055 | Lines 389-391: three Japanese boilerplate quotes replaced with the translated ADR boilerplate copied verbatim (each sentence found by grep -F in 6-14 ADRs; written as plain sentences because the second contains double quotes); old English glosses dropped per procedure; size finding only shrank (31309->31109); quality findings unchanged; full suite deferred to batch end per user decision; docs-mapping step N/A |

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
- **Requirement ID**: REQ-006, REQ-007 (AC-006, AC-007) — Plan Implementation steps Step 7
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
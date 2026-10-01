## Goal
- REQ-001: retire the obsolete 'Japanese alternative' bilingual rule; the file ends with no Japanese or full-width characters and no new checker findings (REQ-007: no regression).

## Scope
- In: the lines listed under Implementation > Details in `docs/00_governance/governance_02_documentation-metadata.md`.
- Out: every other line of `docs/00_governance/governance_02_documentation-metadata.md` and every other file.

## Assumptions
- Current content re-verified on 2026-10-01 (plan-to-implementation-procedure Step 3a); line numbers are a locating aid and may shift — locate by content.
- No prerequisite gate: this row does not depend on langadr001 output.

## Design decisions
- The rule is a leftover of the bilingual convention retired on 2026-08-20 (`cccfca75b` added the English-only rule; `c15d152c8` already converted item 6) — align, do not delete, so the numbered list keeps its references stable.
- Edit only the Japanese/full-width text and the minimal surrounding words (Plan Implementation intent).

## Alternatives considered
- Delete item 3 entirely: rejected — renumbers items 4-7 and loses the explicit statement of the English-only rule in the glossary context.

## Implementation
### Target file
- `docs/00_governance/governance_02_documentation-metadata.md`

### Procedure
1. Check the prerequisite gate in Assumptions (if any); stop and log a blocker if unmet.
2. Locate each line listed in Details by content.
3. Apply the change described in Details.
4. Run the Validation plan.
5. Self-review the meaning and record the result in Execution Status Notes.

### Method
- Targeted single-line edits; confirm with `git diff -U0 docs/00_governance/governance_02_documentation-metadata.md` that only the listed lines changed.

### Details
- Current lines:
  - 112: `3. **Bilingual text**: Use English preferred form with Japanese alternative in parentheses on first occurrence.`
- Change:
  - Replace item 3's text with: `3. **Bilingual text**: Do not add non-English alternatives; all `docs/` text is English per `skills/DESIGN.md` Output language. Alternative forms are the English variants listed in the Terminology Glossary.` (Plan Design proposed wording; refine wording only, not meaning).
  - Keep item numbering and items 1-2, 4-7 unchanged; item 6 (`"Needs Confirmation (Requires Confirmation)"`) is explicitly out of scope.

## Compatibility considerations
- No checker parses this rule; `skills/DESIGN.md` stays unchanged (Plan Out-of-Scope).

## Security considerations
- N/A: documentation wording change only.

## Rollback considerations
- Revert with `git checkout -- docs/00_governance/governance_02_documentation-metadata.md`; no other file in this Plan depends on this edit.

## Validation plan
- `uv run python tools/check_docs_quality.py` — no new line for this file versus the Plan Design baseline (4 lines).
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_02_documentation-metadata.md` — no new finding.
- `grep -n 'Japanese alternative' docs/00_governance/governance_02_documentation-metadata.md` — no output.

## Completion criteria
- Item 3 no longer mentions a Japanese alternative and points to `skills/DESIGN.md` Output language.
- No other line in the file changed (`git diff` shows one changed line).
- Only the listed lines changed.

## Out of scope
- Pre-existing findings in this file listed in the Plan Design baseline; any line not listed in Details; ADR files; tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Details | Pending | — | — | |
| 2 | Run the Validation plan and compare with the Plan Design baseline | Pending | — | — | |
| 3 | Self-review meaning and record result in Notes | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (AC-001) — Plan Implementation steps Step 2
- **Source issue**: issues/20261001-104622_langdoc001_remove-japanese-text-from-non-adr-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-110459_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-120650
- **Related target files**: docs/00_governance/governance_02_documentation-metadata.md

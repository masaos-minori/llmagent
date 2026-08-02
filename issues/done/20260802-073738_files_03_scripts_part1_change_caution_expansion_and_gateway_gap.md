# Expand docs/01_overview-files-03-scripts-part1.md change-caution notes to other subdirectories; add missing repository_gateway.py

## Priority
Medium

## Summary
`docs/01_overview-files-03-scripts-part1.md` (~lines 67-71) contains a valuable "変更時の注意点" (cautions when changing) section describing coupled-change pitfalls (e.g. `idempotency_ops.py` vs `attempt_ops.py` responsibility confusion). Separately, `repository_gateway.py` exists in source and is mentioned in this cautions section, but is missing from the file's main responsibility table.

## Reason for Change
The change-caution format is one of the most valuable patterns in this document set (it prevents implementers from making coupled-but-separate-responsibility mistakes) and should be extended to other subdirectories (services/, workflow/, etc.) that currently lack it. The `repository_gateway.py` omission from the responsibility table undermines the table's completeness/trustworthiness.

## Implementation Intent
Add `repository_gateway.py` to the responsibility table in this file, and separately propose/apply the same "変更時の注意点" pattern to other file-listing documents covering `services/`, `workflow/`, etc. subdirectories.

## Target Files or Areas
`docs/01_overview-files-03-scripts-part1.md`; potentially other `docs/01_overview-files-03-scripts-part*.md` files covering `services/`, `workflow/`, etc.

## Required Changes
- Add `repository_gateway.py` to the responsibility table in `docs/01_overview-files-03-scripts-part1.md`, with a one-line description of its role.
- Confirm whether the omission was intentional (e.g. considered internal-only) or an oversight before adding it.
- Identify which other `docs/01_overview-files-03-scripts-part*.md` files cover subdirectories (services/, workflow/) that could benefit from a similar "変更時の注意点" section, and add one where a genuine coupled-change pitfall exists (do not invent cautions where none apply).

## Acceptance Criteria
`repository_gateway.py` appears in the responsibility table; at least the subdirectories with a clear coupled-change risk have an equivalent cautions section.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-files-03-scripts-part1.md` and potentially sibling part files updated.

## Out of Scope
Do not add a cautions section to subdirectories where no genuine coupled-change risk exists — this section should not become boilerplate.

## AI Implementation Instruction
Verify `repository_gateway.py`'s actual responsibility from source before writing its table description. Only add cautions sections backed by a real, identifiable coupling risk in the code, not speculative ones.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §4 強化候補 (files-03-scripts-part1), §6A (repository_gateway.pyの分類漏れ)
- Generated at: 2026-08-02

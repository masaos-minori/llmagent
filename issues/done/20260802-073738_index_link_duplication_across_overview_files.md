# Consolidate duplicate `01_overview.md` index links across Overview/Architecture detail files

## Priority
Medium

## Summary
Each Overview/Architecture detail file (`01_overview-arch-*.md`, `01_overview-files-*.md`) contains its own link row back to the index file `01_overview.md`, breaking the intended single-index navigation structure.

## Reason for Change
Duplicated index links across 15 files create update-drift risk (e.g. if the index file is renamed or split) and undermine the "single point of navigation" design intent.

## Implementation Intent
Confirm the exact duplicated link pattern across the 15 files, then standardize it to a single consistent back-reference convention rather than removing navigation entirely.

## Target Files or Areas
`docs/01_overview.md` and all `docs/01_overview-arch-*.md` / `docs/01_overview-files-*.md` detail files (15 files) — confirm exact list by grep before editing.

## Required Changes
- Grep for the duplicated index-link line pattern across all `docs/01_overview-*.md` files.
- Decide on one canonical back-reference format (e.g. a single "↑ Back to `01_overview.md`" line placed consistently).
- Apply the canonical format uniformly.

## Acceptance Criteria
All 15 detail files use the same single-line back-reference format to `01_overview.md`; no file has a different or redundant multi-line index reference.

## Testing Expectations
Not required (documentation-only). Manually verify each file's back-reference link resolves correctly after the change.

## Documentation Impact
All `docs/01_overview-*.md` detail files updated for consistency.

## Out of Scope
Do not change the content or structure of `01_overview.md` itself in this issue.

## AI Implementation Instruction
Grep first to confirm the actual scope (which files and what exact duplicated text) before editing. Keep changes to the link line only — do not touch surrounding content.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §1 (連結文書としての問題)
- Generated at: 2026-08-02

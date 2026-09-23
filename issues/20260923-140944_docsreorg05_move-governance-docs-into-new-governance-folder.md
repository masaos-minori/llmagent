# Move governance docs into new governance folder

## Priority
Medium

## Summary
`git mv` the 5 governance-area files from `docs/` (flat) into a new `docs/00_governance/`
subfolder, with no filename or content change beyond what this issue's own required
fixes call for.

## Background
A separate investigation (2026-09-23) evaluated reorganizing `docs/` into area-based
subfolders while keeping every existing filename unchanged. This issue is the physical
move for the `00_governance` area, the first and lowest-risk batch (small file count,
these are policy/meta docs rather than deeply cross-referenced technical reference
docs).

## Problem
`docs/00_governance_01_documentation-policy.md`, `docs/00_governance_02_documentation-metadata.md`,
`docs/00_governance_03_issue-and-uncertainty-management.md`,
`docs/00_governance_04_documentation-checks.md`, and `docs/00_index.md` currently sit
directly under `docs/` alongside all other areas' files, with no folder grouping.

## Reason for Change
Grouping governance/meta docs into their own folder is the first step of the broader
`docs/` reorganization, validating the move process (tooling readiness + reference
fixups + baseline updates) on the smallest, lowest-risk batch before larger areas.

## Implementation Intent
Use `git mv` only — do not rename any file. Move exactly these 5 files into
`docs/00_governance/`. After the move, fix any reference that literally breaks under
plain relative-path resolution but is not yet covered by the folder-independent lookup
(if `docsreorg01` has not yet landed when this issue is executed, treat that as a hard
blocker per Dependencies — do not attempt to manually rewrite all affected references
as a substitute).

## Target Files or Areas
- `docs/00_governance_01_documentation-policy.md` → `docs/00_governance/00_governance_01_documentation-policy.md`
- `docs/00_governance_02_documentation-metadata.md` → `docs/00_governance/00_governance_02_documentation-metadata.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md` → `docs/00_governance/00_governance_03_issue-and-uncertainty-management.md`
- `docs/00_governance_04_documentation-checks.md` → `docs/00_governance/00_governance_04_documentation-checks.md`
- `docs/00_index.md` → `docs/00_governance/00_index.md`
- `tests/tools/test_check_docs_quality.py` (`EXPECTED_WITHIN_FILE_PAIRS` — 13 existing
  entries reference these files by their current bare relative-path key)

## Required Changes
- `git mv` each of the 5 files listed above into `docs/00_governance/`.
- Update `tests/tools/test_check_docs_quality.py`'s `EXPECTED_WITHIN_FILE_PAIRS`: change
  each of the 13 keys currently prefixed with the bare filename (e.g.
  `"00_governance_01_documentation-policy.md:..."`) to include the new folder prefix
  (e.g. `"00_governance/00_governance_01_documentation-policy.md:..."`), following the
  same key format already used for the existing `eventbus/*.md` subfolder entries in
  that same frozenset.
- Confirm `docsreorg01` (folder-independent reference resolution) and `docsreorg02`
  (subfolder-aware domain checkers, specifically `check_dependency_graph_cycles.py`'s
  `GRAPH_DOC_NAME` and `check_needs_confirmation_inventory.py`'s `INVENTORY_DOC_NAME`)
  have landed before merging this move.

## Constraints
- `git mv` only — no filename changes, no content rewriting beyond what
  `docsreorg04`'s canonical-reference update already covers.
- Do not move any file outside this list.

## Acceptance Criteria
- `git log --follow` on each moved file shows continuous history through the move.
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero new findings introduced by this move.
- `uv run python -m tools.check_docs_quality` passes (or reports only pre-existing,
  unrelated findings).
- `uv run pytest tests/tools/test_check_docs_quality.py -q` passes with the updated
  `EXPECTED_WITHIN_FILE_PAIRS`.
- `uv run pre-commit run --all-files` passes (covers `adr-invariant-matrix`,
  `docs-consistency`, and related hooks touched by `docsreorg02`).

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pytest tests/tools/ -q`

## Documentation Impact
This issue is itself the documentation-location change for the governance area; no
further documentation-impact statement beyond the required baseline/reference updates
listed above.

## Out of Scope
- Any filename change or prefix removal.
- Any content edit to the 5 moved files beyond what is already covered by
  `docsreorg04`.
- Moving any file belonging to a different area.

## Dependencies
- Depends on: `docsreorg01` (folder-independent cross-reference resolution),
  `docsreorg02` (subfolder-aware domain checkers).
- Should land together with, or immediately after, the relevant part of `docsreorg04`
  (canonical routing reference updates) and `docsreorg03` is not affected by this area
  (no CI workflow filters reference governance docs by prefix).

## Unresolved Questions
N/A: none — file list and current EXPECTED_WITHIN_FILE_PAIRS entry count were directly
confirmed during issue drafting.

## AI Implementation Instruction
Move only the 5 files listed, using `git mv`, into `docs/00_governance/`. Do not rename
any file. Update only the `EXPECTED_WITHIN_FILE_PAIRS` keys that reference these 5
files. If `docsreorg01`/`docsreorg02` have not landed yet, stop and report `Blocked`
rather than proceeding with a manual reference-rewrite workaround.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-140944
- **Related target files**: docs/00_governance_01_documentation-policy.md, docs/00_governance_02_documentation-metadata.md, docs/00_governance_03_issue-and-uncertainty-management.md, docs/00_governance_04_documentation-checks.md, docs/00_index.md, tests/tools/test_check_docs_quality.py

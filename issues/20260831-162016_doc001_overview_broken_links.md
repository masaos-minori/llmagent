# docs/01_overview.md references two nonexistent files

## Priority
Low

## Summary
`docs/01_overview.md` links to `01_overview-arch.md` and `01_overview-files.md`, neither of
which exists; the actual files use a `-arch-*`/`-files-*` naming pattern with additional
suffixes.

## Background
Discovered incidentally while running `uv run python tools/check_docs_consistency.py --domain
overview` to validate an unrelated governance-policy documentation change. This finding is
unrelated to that change.

## Problem
`tools/check_docs_consistency.py --domain overview` reports: `reference to
removed/nonexistent doc file '01_overview-arch.md'` and `reference to removed/nonexistent doc
file '01_overview-files.md'`, both at `01_overview.md`. `docs/00_index.md`'s own Document
References by Task table describes the actual structure as `01_overview.md` indexing
`01_overview-arch-*.md` and `01_overview-files-*.md` (i.e., multiple suffixed files per
prefix), so the two references in `01_overview.md` are pointing at a singular filename that
was likely split into multiple files at some point without updating this reference.

## Reason for Change
A standing, automatically-detected broken link in the system-overview document — the first
document new readers are directed to per `docs/00_index.md`'s Recommended Reading Order —
degrades navigation and leaves the documentation consistency checker permanently reporting an
error that will mask genuinely new link breakages introduced by future changes.

## Implementation Intent
Update the two references in `01_overview.md` to either link to the actual current index
entry point for each split (if one exists) or to the correct set of suffixed files, matching
whatever pattern `docs/00_index.md` and the actual files under `docs/` currently use.

## Target Files or Areas
- `docs/01_overview.md` — primary target
- `docs/00_index.md` — read-only reference for the correct current file-naming pattern
- The actual `docs/01_overview-arch-*.md` and `docs/01_overview-files-*.md` files — read-only reference to confirm which specific files should be linked

## Required Changes
- Replace the `01_overview-arch.md` reference with a correct link (or set of links) to the
  actual current `01_overview-arch-*.md` file(s).
- Replace the `01_overview-files.md` reference with a correct link (or set of links) to the
  actual current `01_overview-files-*.md` file(s).

## Constraints
- Do not rename or restructure the actual `01_overview-arch-*.md` / `01_overview-files-*.md`
  files — only fix the referencing links in `01_overview.md`.

## Acceptance Criteria
- `uv run python tools/check_docs_consistency.py --domain overview` reports zero
  removed/nonexistent doc file references for `01_overview.md`.
- The corrected links resolve to files that actually exist under `docs/`.

## Testing Expectations
Not required beyond re-running `uv run python tools/check_docs_consistency.py --domain
overview` to confirm the two errors are gone and no new ones were introduced.

## Documentation Impact
This issue is itself the documentation fix.

## Out of Scope
- Any other consistency finding in the `overview` domain not related to these two specific
  broken references.
- Restructuring `01_overview.md` beyond fixing these two links.

## Dependencies
N/A: none

## Unresolved Questions
- Whether `01_overview.md` should link to a single representative file per prefix or to every
  suffixed file individually — needs a look at how the equivalent links are handled elsewhere
  in the document before deciding.

## AI Implementation Instruction
- Confirm the actual current filenames under `docs/` for both the `-arch-*` and `-files-*`
  patterns before editing the links — do not guess a replacement filename.
- Make only the two link corrections described here; do not perform broader edits to
  `01_overview.md`.
- Re-run the cited consistency check after editing to confirm the fix.

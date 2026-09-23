# Make docs cross-reference resolution folder-independent

## Priority
High

## Summary
Change how `tools/check_docs_structure.py` resolves front-matter `related`/`source`
entries and body Markdown links, from "relative to the referencing file's own
directory" to a repository-wide basename lookup across all of `docs/**/*.md`. This is
a prerequisite for the planned `docs/` folder reorganization (see Dependencies):
without it, moving files into subfolders breaks every cross-folder reference.

## Background
A separate investigation (2026-09-23) evaluated reorganizing `docs/` into area-based
subfolders (`00_governance/`, `01_overview/`, `10_adr/`, `21_rag/`, `22_mcp/`,
`23_agent/`, `24_eventbus/`, `40_shared/`, `41_db/`, `90_deployment/`, `91_security/`)
while keeping every existing filename unchanged (no prefix removal, no renaming).

## Problem
`tools/check_docs_structure.py`'s `check_related_links()` and `check_links()` both
resolve a referenced filename as `(path.parent / entry).resolve()` — i.e. relative to
the *referencing* file's own directory, not a repository-wide search. Measured against
the current `docs/` tree: of 650 front-matter `related`/`source` entries, 58 already
cross what would become a folder boundary under the planned reorg; of 811 body
Markdown links, 240 do. Moving files into the planned subfolders would make all 298 of
these references resolve to a non-existent path and start failing
`check_docs_structure.py`, even though the referenced files still exist.

## Reason for Change
The planned folder reorganization (see Dependencies) explicitly keeps every filename
unchanged and moves files only. Every filename in `docs/**/*.md` is currently globally
unique (verified: zero duplicate basenames across the entire tree today), so a global
basename lookup is unambiguous and safe to adopt now, before any files move. Doing this
first avoids having to manually rewrite 298 relative-path references by hand once files
relocate, and keeps `check_docs_structure.py` passing throughout the migration.

## Implementation Intent
Build one basename → path index by scanning `docs/**/*.md` once per invocation, and use
it to resolve `related`/`source` entries and body Markdown link targets, instead of
`path.parent`-relative resolution. Preserve the existing behavior of reporting a
"references missing file" / "broken link" issue when a referenced basename does not
exist anywhere in the index. Also update the tool's default glob (`docs/*.md`) to be
recursive (`docs/**/*.md`), since it currently would not even see files already living
in `docs/adr/`, `docs/eventbus/`, or `docs/databases/` unless the caller passes an
explicit recursive glob.

Do not change how a reference is *written* (still a bare filename with no directory
component) — only how it is *resolved*. If an existing reference already includes a
relative directory component (e.g. `adr/ADR-010-rag-fallback.md` or
`../00_governance_01_documentation-policy.md` — both exist in the tree today), the
lookup should still resolve it correctly; do not require removing those.

## Target Files or Areas
- `tools/check_docs_structure.py` (`check_related_links`, `check_links`, default glob
  in `main()`)
- `tests/tools/test_check_docs_structure.py` (or equivalent test file for this tool —
  confirm exact path before editing)

## Required Changes
- Build a single repository-wide basename index (`docs/**/*.md`) once per tool
  invocation.
- Change `check_related_links()` to resolve each `related`/`source` entry against this
  index instead of `path.parent`-relative resolution.
- Change `check_links()` to resolve each body Markdown link target the same way.
- Keep reporting an issue when a referenced basename is not found in the index anywhere
  (do not silently drop the check).
- Add a defensive check (test or explicit runtime check) for what happens if two files
  ever do share a basename in the future — decide and document whether this raises an
  error or is treated as ambiguous/unresolved, since a silent "pick one" would be an
  unnoticed regression, given the whole reorg's continued safety depends on
  basename uniqueness.
- Change the default glob pattern in `main()` from `docs/*.md` to `docs/**/*.md` so
  subfolder files are covered without callers having to pass it explicitly.

## Constraints
- Must not weaken the existing broken-reference detection: a truly missing file must
  still be reported.
- Must continue to correctly resolve references that already include a directory
  component (`adr/ADR-010-rag-fallback.md`, `../00_governance_01_documentation-policy.md`)
  — do not assume every reference is a bare filename.
- Basename uniqueness across `docs/**/*.md` is a load-bearing assumption; do not treat
  it as guaranteed forever without a check (see Required Changes).
- **Known limitation this issue does not solve**: this change only makes the automated
  checker (`check_docs_structure.py`) tolerate a bare-filename cross-folder reference.
  It does not fix how the same bare-filename link renders for a human reading the file
  directly on GitHub or in a plain Markdown viewer — those follow the literal relative
  path and will 404 once the referencing and referenced files are moved into different
  folders. This issue accepts that trade-off (keeping the automated safety net green
  without a large manual link-rewrite) but does not claim to preserve human-facing link
  click-through across folders; record this explicitly rather than silently.

## Acceptance Criteria
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports the same set of "missing file" / "broken link" findings before and after this
  change, for the current (pre-move) `docs/` tree.
- A test fixture that places two files in different directories, with one referencing
  the other by bare filename only, passes after the change (this currently would fail
  under `path.parent`-relative resolution if the two files are not in the same
  directory).
- A test fixture with a reference to a genuinely non-existent filename still produces a
  "references missing file" / "broken link" finding.
- Running the tool with no arguments now covers files under `docs/adr/`,
  `docs/eventbus/`, and `docs/databases/` (verify via a fixture or by confirming the
  reported file count increases relative to the old default).

## Testing Expectations
- Add/extend unit tests for `check_related_links()` and `check_links()` covering:
  cross-directory resolution success, missing-file detection, and a reference that
  already includes a relative directory component.
- Run the full existing test suite for this tool to confirm no regression:
  `uv run pytest tests/tools/test_check_docs_structure.py -q`.

## Documentation Impact
No `docs/` content changes are required by this issue itself. If `tools/TOOL_DESCRIPTIONS.md`
documents `check_docs_structure.py`'s resolution behavior, update its description to
reflect the new folder-independent lookup.

## Out of Scope
- Physically moving any file under `docs/` (tracked by separate per-area issues).
- Removing or shortening any filename prefix (explicitly out of scope per the current
  reorg decision).
- Changing `tools/_docs_consistency_lib.py`'s `discover_md_files(prefix=...)` non-recursive,
  prefix-based file discovery (tracked by a separate issue).
- Changing any hardcoded `docs/<file>.md` path constant in other tools (tracked by
  separate issues).

## Dependencies
- Depends on: none (this is the prerequisite issue for the `docs/` folder
  reorganization work).
- Blocks: every per-area physical-move issue for the `docs/` folder reorganization
  (each area move assumes this resolution change has already landed, to avoid manually
  rewriting cross-folder references).

## Unresolved Questions
N/A: none — the test file path (`tests/tools/test_check_docs_structure.py`) was
confirmed to exist during issue drafting.

## AI Implementation Instruction
Change only `tools/check_docs_structure.py`'s reference-resolution logic and default
glob, plus its own test file. Do not touch any other tool, any `docs/*.md` content, or
begin any physical file move. Do not remove support for references that already carry a
relative directory component. If you find the basename-uniqueness assumption already
violated somewhere in the current `docs/` tree, stop and report it rather than silently
resolving to the first match found.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-140511
- **Related target files**: tools/check_docs_structure.py, tests/tools/test_check_docs_structure.py

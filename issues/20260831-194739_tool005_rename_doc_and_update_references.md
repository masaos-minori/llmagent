# Add `tools/rename_doc.py` to rename a docs/*.md file and rewrite every referencing link in one pass

## Priority
Medium

## Summary
Renaming a document under `docs/` (including `docs/adr/*.md`) currently requires a manual
sequence: `git mv` the file, then `grep -rl` for the old filename across `docs/`, then hand-edit
every match to point at the new path (and, where the link text embeds the document's title,
update that text too). Add a script that performs the rename and rewrites every Markdown link in
one pass, reporting anything it cannot safely auto-fix.

## Background
This session renamed `docs/adr/ADR-004-*.md` twice (once to
`ADR-004-production-failure-handling-policy.md`, then to
`ADR-004-environment-failure-handling-policy.md`), each time manually finding and fixing 7
referencing files via `grep -rl` followed by individual `Edit`/`sed` calls, including updating
link text that duplicated the document's old title alongside the path. The same manual sequence
was performed for the ADR-011/ADR-013 deletions and ADR-003/ADR-008 consolidation earlier in the
same session. `tools/TOOL_DESCRIPTIONS.md` already documents a `rename_*` convention
(`rename_mcp_modules.py`) for exactly this class of "rename and fix up every reference"
operation, but that existing tool targets Python module renames, not `docs/*.md` files.

## Reason for Change
A dedicated tool removes the repetitive, error-prone grep-then-hand-edit cycle for doc renames,
and reduces the risk of missing a reference (which would otherwise surface later as a broken link
caught only by `check_docs_structure.py`, or not caught at all if the stale reference is plain
prose rather than a Markdown link).

## Implementation Intent
Add `tools/rename_doc.py <old-path> <new-path>` that: (1) performs the file move via `git mv`;
(2) finds every Markdown link (`[text](path)` and bare-path references matching the established
`docs/adr/ADR-{NNN}-*.md` and general `docs/*.md` link conventions documented in
`00_governance_02_documentation-metadata.md` Link Rules) across `docs/` that points at the old
path, and rewrites the path portion to the new path; (3) when a document's front-matter `title`
differs between old and new content (e.g., a title change accompanying the rename), optionally
rewrites adjacent link text that duplicates the old title, guarded by a flag since not every
occurrence of the old title near a link is safe to blindly replace; (4) reports, rather than
silently modifies, any reference it found in a non-Markdown-link form (plain prose mentioning the
old filename) so a human/agent can review it individually.

## Target Files or Areas
- `tools/rename_doc.py` — new file
- `docs/` (including `docs/adr/`) — the files this tool renames and rewrites references within
- `tools/TOOL_DESCRIPTIONS.md` — must document the new tool

## Required Changes
- Implement the rename + link-path rewrite described above, using `git mv` for the primary file.
- Implement the optional title-text rewrite as an explicit opt-in flag (e.g.,
  `--old-title "..." --new-title "..."`), never inferred automatically.
- Implement the "found but not auto-fixed" report for non-link prose mentions of the old filename.
- Add a dry-run mode (`--dry-run`) that reports what would change without writing, consistent with
  `fix_docs_section_marks.py` and `fix_docstring_paths.py`'s existing dry-run-by-default
  convention in this `tools/` directory.

## Constraints
- Default to dry-run (matching `fix_docstring_paths.py`/`fix_docs_section_marks.py`'s existing
  convention of requiring an explicit `--apply` flag to write).
- Do not attempt to rewrite plain-prose mentions of the old filename automatically — only
  Markdown-link paths and, if explicitly requested via the title flags, adjacent link text.
- Do not modify files outside `docs/` — this tool is scoped to documentation renames, not source
  code (that is `rename_mcp_modules.py`'s existing scope).
- Preserve each file's existing relative-link convention (e.g., ADR files linking to `docs/*.md`
  without a `../` prefix, as an established pattern in this repository) rather than normalizing
  to a "technically correct" relative path that would diverge from surrounding files' style.

## Acceptance Criteria
- Running the tool against a fixture reproducing this session's ADR-004 rename correctly updates
  all 7 previously-identified referencing files' link paths.
- Non-link prose mentions are reported, not silently modified.
- `--dry-run` (default) reports the same changes `--apply` would make, without writing.
- `tools/TOOL_DESCRIPTIONS.md` documents the new tool; `check_tool_descriptions_sync.py` passes.

## Testing Expectations
Add `tests/tools/test_rename_doc.py` using fixture `docs/`-like directories (not the live `docs/`
tree) covering: a simple rename with multiple referencing files, a rename with the optional
title-rewrite flag, and a file containing a non-link prose mention that must be reported rather
than modified. Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
Add the new tool to `tools/TOOL_DESCRIPTIONS.md`, in the same table as `rename_mcp_modules.py`.

## Out of Scope
- Renaming or restructuring `scripts/*.py` files (already covered by `rename_mcp_modules.py`).
- Automatically resolving non-link prose mentions.
- The other four tools proposed alongside this one, tracked as separate issues.

## Dependencies
N/A: none — independently buildable.

## Unresolved Questions
Whether this tool should also handle renaming an ADR's numeric ID (e.g., `ADR-004` → a different
number), which this session never needed and which would additionally require updating
`docs/adr-index.md`'s ID column and every plain-text `ADR-NNN` mention, not just file paths —
needs an owner decision on whether that broader scope belongs in this tool or a separate one;
default to file-path-only renaming (current ADR number preserved) unless requested.

## AI Implementation Instruction
Read `00_governance_02_documentation-metadata.md` Link Rules in full before implementing the link
matcher, and inspect at least three existing `docs/adr/*.md` files' Related Documents sections to
confirm the actual relative-path convention in current use (with vs. without `../`) rather than
assuming a single "correct" form — this repository's ADRs are not fully consistent on this point,
and the tool must preserve each file's existing style rather than normalizing it.

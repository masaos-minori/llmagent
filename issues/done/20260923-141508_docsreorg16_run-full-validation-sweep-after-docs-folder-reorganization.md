# Run full validation sweep after docs folder reorganization

## Priority
Medium

## Summary
After all 11 area-move issues (`docsreorg05`-`docsreorg15`) have landed, run a
repository-wide validation pass to confirm the `docs/` folder reorganization introduced
no regression, and confirm CI triggers correctly on the new paths. This issue performs
no file changes itself unless the validation surfaces a gap that one of the other
`docsreorg` issues should have already closed.

## Background
Same `docs/` reorganization effort as `docsreorg05`; see that issue's Background for
full context. This is the final phase: a repository-wide sweep, not a per-area check
(each area-move issue already includes its own acceptance criteria for the files it
touches).

## Problem
Each area-move issue validates only its own file set in isolation. A repository-wide
sweep is needed to catch anything that only surfaces once every area has moved — e.g. a
cross-folder reference between two areas that were moved in different issues (and thus
each looked "fine" in isolation using the old location of the other), or a tool/test
fixture that was only partially updated.

## Reason for Change
Confirms the reorganization is complete and safe before considering the effort done;
catches any gap that individual area-scoped acceptance criteria could not.

## Implementation Intent
Run every validation command listed below against the fully-reorganized `docs/` tree.
If any check fails, identify which specific `docsreorg` issue's scope the failure
belongs to and report it there (or file a new follow-up issue if it does not fit any
existing one) rather than fixing it ad hoc inside this issue.

## Target Files or Areas
- `docs/` (entire tree, post-reorganization)
- All 9 tools touched by `docsreorg02`
- `.github/workflows/` (the 5 workflows touched by `docsreorg03`)
- `tests/` (full suite)

## Required Changes
- N/A: this issue is a validation pass; it does not itself change any file. Any fix it
  surfaces belongs to the relevant upstream `docsreorg` issue or a new follow-up issue.

## Constraints
- Do not perform any file move or content edit as part of this issue — if the sweep
  finds a gap, report which upstream issue should have covered it rather than patching
  it here, so ownership stays traceable to the `docsreorg` issue that should have
  caught it.

## Acceptance Criteria
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
  reports zero findings beyond the pre-existing, unrelated ones already known before
  the reorganization began (ADR file-size warnings, the two `ADR-008`/`ADR-010` broken
  links tracked by issue DOC-001, and whatever remains of the `04_mcp_02_03_audit-logging-and-errors.md`
  related-reference fix if that separate Plan has not yet landed).
- `uv run python -m tools.check_docs_quality` passes (or reports only the same
  pre-existing, unrelated findings).
- `uv run pre-commit run --all-files` passes.
- `uv run pytest -q` (full suite) passes.
- Each of the 5 workflows updated by `docsreorg03` is confirmed to trigger correctly:
  make one small, reversible edit to a file in each newly-moved area and confirm the
  corresponding workflow run appears in the Actions history (or inspect the resolved
  trigger paths via `gh workflow view <name> --yaml` if a live trigger test is not
  practical).
- No file remains under any of the old flat locations or the old `docs/adr/`,
  `docs/eventbus/`, `docs/databases/` directories — `find docs -maxdepth 1 -name "*.md"`
  returns nothing outside intentionally-flat area-index files (if any remain by design),
  and `docs/adr/`, `docs/eventbus/`, `docs/databases/` no longer exist.

## Testing Expectations
- `uv run python tools/check_docs_structure.py "docs/**/*.md" --schema schemas/doc_front_matter.json`
- `uv run python -m tools.check_docs_quality`
- `uv run pre-commit run --all-files`
- `uv run pytest -q`

## Documentation Impact
N/A: covered by Summary — this issue validates documentation location changes made by
other issues; it does not itself add new documentation content.

## Out of Scope
- Fixing any gap found — report it against the responsible upstream `docsreorg` issue
  or file a new follow-up issue instead.
- Any filename change, prefix removal, or filename-length shortening (a separate,
  independent initiative outside this reorganization's scope).
- The pre-existing, unrelated issues already known before this reorganization began:
  the `-part1`/`-part2` broken references in `rules/env.md`, the ADR-011 numbering
  gap, the `ADR-008`/`ADR-010` broken links (issue DOC-001), and the
  `docs/02_deployment-part2.md` bug in `tools/generate_reference_table.py`.

## Dependencies
- Depends on: `docsreorg01` through `docsreorg15` (every prerequisite tooling issue and
  every area-move issue).

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Run the validation commands listed under Acceptance Criteria / Testing Expectations
only. Do not fix anything found directly in this issue — instead, name the specific
upstream `docsreorg` issue (or propose a new follow-up issue) that the finding belongs
to, and stop there.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260923-141508
- **Related target files**: docs/, tools/, .github/workflows/, tests/

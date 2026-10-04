## Goal
Add a `merge-related` subcommand to `tools/manage_frontmatter.py` that unions body Related sections into front matter `related:` (REQ-001: the reviewable, idempotent merge tool the migration depends on).

## Scope
- In: one new subcommand, its helper functions, its argparse registration, and the module docstring usage list.
- Out: changes to `add-missing`, `dedupe-lists`, `rename-category-to-area`, `classify`; the pre-existing non-recursive globbing of those subcommands; any `docs/` content change.

## Assumptions
- Front matter is edited line-wise (like `dedupe_front_matter`), not re-serialized, so unrelated keys and formatting are preserved.
- Basenames are unique under `docs/` (enforced by `_build_basename_index` in `tools/check_docs_structure.py`), so a bare filename resolves unambiguously.
- Three `related:` shapes exist in the corpus: a block list, an empty `related:`, and an inline `related: []`. Quoted entries and non-empty inline lists were not found and are treated as unsupported.

## Design decisions
- Add the subcommand to this tool instead of a new file: it already owns `related` list handling (`LIST_FIELDS`) and the dry-run-default plus `--fix` convention (`cmd_add_missing`).
- Dry-run is the default; writing requires `--fix`.
- Unresolvable or unsupported input is reported and skipped, never guessed (fail closed), matching the tool's existing handling of ambiguous areas.
- Scan `docs/**/*.md` recursively (`DOCS_DIR.rglob`); the existing subcommands glob only the top-level directory and must not be copied.

## Alternatives considered
- New `tools/merge_related_docs.py`: rejected; duplicates front matter parsing and the CLI convention.
- Re-serialize front matter with a YAML library: rejected; would reorder or reformat unrelated keys across about 190 files.
- Delete body sections unconditionally: rejected; 34 non-ADR documents have non-link lines whose disposition needs owner review.

## Implementation
### Target file
`tools/manage_frontmatter.py`

### Procedure
1. Add helpers that locate the front matter block, parse the `related:` shape, and extract body Related sections.
2. Add a new command function for the subcommand (named after the existing `cmd_*` convention) that builds the per-file result, prints the report, and writes only under `--fix`.
3. Register `merge-related` in `main()` with optional positional `paths` (globs relative to the repository root, default `docs/**/*.md`), `--dry-run`, and `--fix`, and dispatch to it.
4. Update the module docstring's Subcommands and Usage lists.

### Method
- Section headings recognized: `## Related Documents`, `## Related Docs`, `## Related Chapters`; a section ends at the next `## ` heading (for ADR documents this includes `###` sub-blocks). Ignore fenced code.
- Entries: backtick `name.md` and Markdown link targets `path.md` (drop `#anchor`); normalize to basename; drop the document itself; drop entries already in front matter; dedupe among body entries; keep existing front matter order and append new entries in body order.
- Unresolved targets (basename absent from the `docs/` index) are reported and not merged.
- A line in a section is link-only when it is blank or a list item holding one entry; any other line (and, outside ADR documents, any sub-heading) is a non-link line and is reported with its line text.
- ADR documents (`10_adr` in the path): extend front matter only; never touch the body.
- Non-ADR documents under `--fix`: write the merged `related:` block; remove the body section(s) only when every line is link-only; otherwise leave the section and report it.
- Report per file: sections found, additions, skipped unresolved entries, non-link lines, and whether the section would be removed.

### Details
- Rewriting `related:`: replace the whole block (the key line plus following `  - ` items), or turn `related: []` and an empty `related:` into a block list; keep two-space indentation and the key's position.
- Section removal: delete the heading through the line before the next `## ` heading and leave exactly one blank line between neighbors; `## Keywords` must still follow and the file must still end with a newline.
- Exit status: `0` in dry-run; under `--fix`, non-zero when any file was skipped as unresolved or unsupported, mirroring `cmd_add_missing`.
- Idempotence: a second run over unchanged output reports no change.
- Pre-existing limitation, out of scope: `dedupe-lists`, `add-missing`, `rename-category-to-area`, and `classify` process top-level `docs/*.md` only.

## Compatibility considerations
- Additive: no existing subcommand, flag, or output changes; `LIST_FIELDS` is unchanged.
- Output format of the new subcommand is new, so nothing depends on it yet.

## Security considerations
- Reads and writes only under `DOCS_DIR`; no subprocess, network, or environment access.
- Do not follow paths outside `DOCS_DIR` when expanding the `paths` argument.

## Rollback considerations
- Revert the commit that adds the subcommand; no data or configuration migration is involved.
- Files already rewritten by `--fix` are separate commits per documentation area and are reverted independently.

## Validation plan
- `uv run ruff format tools/manage_frontmatter.py` and `uv run ruff check tools/manage_frontmatter.py --fix`, then confirm clean.
- `uv run mypy tools/manage_frontmatter.py` (explicit path; the default mypy scope is `scripts/`).
- `uv run bandit tools/manage_frontmatter.py`.
- `uv run pytest tests/tools/test_manage_frontmatter.py`.
- Real-data smoke test: `uv run python tools/manage_frontmatter.py merge-related` over `docs/` (dry-run) and inspect the report against the Plan's measured counts.

## Completion criteria
- `merge-related` runs dry-run by default and writes only with `--fix`.
- All three `related:` shapes, all three section headings, backtick and link forms, multiple sections, self-reference, duplicates, and ADR handling behave as in Method.
- A second run after `--fix` reports no change.
- Ruff, mypy, bandit, and the tool's tests pass.

## Out of scope
- Any `docs/` content change (done by later rows).
- Fixing the non-recursive globbing of the other subcommands.
- A new standalone tool file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add helpers, the subcommand's command function, argparse registration, and docstring update | Completed | 20261004-120103 | 20261004-120103 | stale check clean after wording fix; changed: tools/manage_frontmatter.py |
| 2 | Add or update tests per Validation plan (row 002) | Completed | 20261004-120103 | 20261004-120103 | N/A: tests are row 002's target; existing tests ran (21 passed) |
| 3 | Run ruff, mypy (explicit path), bandit, and the tool's tests | Completed | 20261004-120103 | 20261004-120103 | ruff, mypy, bandit clean; full suite 8041 passed, 8 failed (unrelated, see report); docs mapping: TOOL_DESCRIPTIONS.md handled by row 008 |
| 4 | Run the dry-run over real `docs/` and record the report summary | Completed | 20261004-120103 | 20261004-120103 | dry-run over docs: 180 would change, 2 with unresolved input |

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
- **Requirement ID**: `REQ-001` (add the `merge-related` subcommand)
- **Source issue**: issues/done/20261004-111518_relateddocsmerge_consolidate-front-matter-related-and-body-related-documents.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-111806_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-112553
- **Related target files**: tools/manage_frontmatter.py
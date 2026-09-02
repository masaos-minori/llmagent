# Bulk-migrate all `docs/*.md` front matter to the finalized canonical schema

## Priority
Medium

## Summary
Once `docmeta01` finalizes the canonical Documentation Metadata schema (`area` as the sole
category field, finalized `area` enum, no front-matter `keywords`), migrate every document
under `docs/` and `docs/adr/` to comply: rename the 4 files currently using `category:` to
`area:`, add missing front matter to the 42 files that currently have none, and confirm every
document's `area` value is a member of the finalized enum.

## Background
A repository-wide grep (see `docmeta01` for the full investigation) found, out of 178 files
under `docs/*.md` and `docs/adr/*.md`:
- 4 files use `category:` instead of `area:`: `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`,
  `docs/01_overview-files-04-shared.md`, `docs/01_overview-files-03-scripts.md`,
  `docs/04_mcp_03_03_transport-and-health.md`. Their existing values (`overview`, `mcp`) are
  already valid `area` values — this is a pure key rename, not a value change.
- 42 files have no front matter block at all (confirmed via `tools/check_docs_structure.py`'s
  existing "missing Front Matter" findings, which this issue's investigation cross-checked
  against the same file set lacking both `area:` and `category:`).
- `tools/manage_frontmatter.py add-missing` already exists and is designed for exactly this
  kind of gap-filling (`extract_area_from_filename()` infers `area` from the file's path/name
  convention).

## Problem
178 documents currently disagree on which metadata key marks their subject area, and nearly a
quarter of them (42/178) carry no machine-readable area classification at all. Any tooling or
AI-agent logic that filters or routes by `area` silently misses these files today.

## Reason for Change
Once `docmeta01` establishes a single canonical schema, the actual document corpus must be
brought into compliance for that schema to have any practical effect. Leaving the corpus
unmigrated means the new governance text becomes just as aspirational as the current
"Recommended Additional Fields" section it replaces.

## Implementation Intent
Prefer the existing `tools/manage_frontmatter.py add-missing` tool over a new ad hoc script,
per `rules/ai-execution.md` Repository Tool Usage. For the 4 `category:`→`area:` renames, a
targeted find-and-replace on the exact key is sufficient (values are already valid). For the
42 files with no front matter, run the existing tool's inference and manually review its
`area` guess against each file's actual directory/subject before accepting it — do not trust
filename-based inference blindly for ambiguous filenames.

## Target Files or Areas
- `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`,
  `docs/01_overview-files-04-shared.md`, `docs/01_overview-files-03-scripts.md`,
  `docs/04_mcp_03_03_transport-and-health.md` (rename `category:` → `area:`)
- The 42 files currently missing front matter entirely — exact list to be re-derived at
  implementation time via `uv run python tools/check_docs_structure.py docs/*.md
  docs/adr/*.md` (the set may have shifted slightly since this issue was filed); a partial
  list observed during investigation includes `docs/00_index.md`,
  `docs/03_rag_90_inconsistencies_and_known_issues.md`, `docs/03_rag_91_design_notes.md`,
  `docs/04_mcp_02_02_startup-modes-and-health.md`, `docs/04_mcp_03_05_lifecycle-and-new-server.md`,
  and others under the `04_mcp_06_*` series and `05_agent_*` series.
- `tools/manage_frontmatter.py` (used, not modified, unless it needs the finalized `area`
  enum wired in — coordinate with `docmeta01`'s schema artifact)

## Required Changes
- Rename `category:` to `area:` (value unchanged) in the 4 identified files.
- For each of the 42 files without front matter, add a compliant front matter block (`title`,
  `area`, `tags`, `related`) using `tools/manage_frontmatter.py add-missing` as the primary
  mechanism; manually review and correct the inferred `title`/`area`/`tags` for accuracy
  before committing.
- Re-run the full-corpus survey after migration and confirm 0 files use `category:` and 0
  files lack `area:`/`title:`/`tags:`/`related:`.
- Confirm every file's `area` value is a member of `docmeta01`'s finalized enum — flag any
  value outside it as a new Needs Confirmation entry rather than guessing a replacement.

## Constraints
- Do not invent new `area` values beyond `docmeta01`'s finalized enum.
- Do not add any of the seven removed "Recommended Additional Fields" (`scope`, `audience`,
  `priority`, `version`, `last_updated`, `author`, `completeness`) — `docmeta01` removes them
  from the governance document precisely because they are unused; do not reintroduce them
  during migration.
- Do not modify document body content in this issue — front matter only.

## Acceptance Criteria
- `grep -l "^category:" docs/*.md docs/adr/*.md` returns no matches.
- Every file under `docs/*.md` and `docs/adr/*.md` has a front matter block containing
  `title`, `area`, `tags`, and `related`.
- `uv run python tools/check_docs_structure.py docs/*.md docs/adr/*.md` reports zero "missing
  Front Matter" findings and zero "Front Matter area is ... expected ..." mismatches for the
  files this issue touches.
- Every `area` value present in the corpus is a member of `docmeta01`'s finalized enum.

## Testing Expectations
`uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py
docs/*.md docs/adr/*.md` must pass with no new findings introduced by this migration. Spot-
check a sample of the 42 newly-front-matter'd files by hand to confirm the inferred `title`
and `area` are accurate, not just mechanically present.

## Documentation Impact
Yes — this issue is a documentation-only change across the corpus; no new documentation
sections are required beyond the front matter itself.

## Out of Scope
- Deciding the canonical schema or `area` enum — that is `docmeta01`'s scope; this issue only
  applies its decisions.
- Wiring automated CI enforcement of the schema — that is `docmeta03`'s scope.
- Any document body content changes.
- Adding `status`, or any other optional field, to documents that do not already need one —
  this issue closes the required-field gap only.

## Dependencies
- Depends on `docmeta01` (finalized schema, `area` enum, and the decision to make `area`
  canonical) — do not start this issue's migration before `docmeta01` lands.
- N/A: no other open issue or plan currently targets bulk front-matter migration, confirmed
  by `grep -rl "manage_frontmatter" issues/ plans/` returning no matches at investigation time
  (aside from this issue and `docmeta01`/`docmeta03`).

## Unresolved Questions
- The exact 42-file list may drift slightly between this issue's filing and implementation
  (documents are actively being edited across concurrent work in this repository) — re-derive
  it via the toolchain command in Required Changes rather than trusting this issue's list
  verbatim.
- N/A otherwise.

## AI Implementation Instruction
Re-run `uv run python tools/check_docs_structure.py docs/*.md docs/adr/*.md` at the start of
implementation to get the current, authoritative list of non-compliant files — do not rely
solely on this issue's investigation snapshot. Use `tools/manage_frontmatter.py add-missing`
per `rules/ai-execution.md` Repository Tool Usage rather than writing a new script. Review
every tool-inferred `area`/`title` value against the document's actual content before
accepting it — do not commit blind inference output. If a file's correct `area` is genuinely
ambiguous (e.g. a document spanning two areas), stop and report it rather than guessing.

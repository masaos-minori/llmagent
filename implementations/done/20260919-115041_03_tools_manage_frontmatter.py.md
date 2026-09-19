## Goal
Add a `classify` subcommand to `tools/manage_frontmatter.py` that infers `class`
where confidently derivable and reports the rest as ambiguous, in dry-run/report
mode only (`REQ-004`).

## Scope
In scope: this one file's new `cmd_classify()` function and its `main()`
subparser registration. Out of scope: a `--fix` write mode (not required by the
source issue's Acceptance Criteria); classifying all existing documents.

## Assumptions
- File structure unchanged since the Plan was written — re-confirmed:
  `cmd_add_missing()` (lines 186-297, "never guess, report ambiguous" pattern),
  `cmd_rename_category_to_area()` (lines 308+, precedent for adding a
  front-matter key programmatically), `main()` (line 449) with subparser
  registration.
- Depends on seq 02 (`tools/_front_matter_schema.py`)'s `class_enum` field
  existing for this subcommand to read the valid class values from the schema
  rather than hardcoding them a second time.

## Design decisions
Follow `cmd_add_missing()`'s exact reporting pattern: iterate `docs/*.md`,
attempt to infer `class` from existing signals (a document-guide file's own
stated class in its Purpose section, or a filename/heading pattern matching one
of the 7 class names — e.g. a filename containing `reference-api` or
`-reference` strongly suggests `class: Reference`), report `[CONFIDENT]
{filename}: {inferred class}` or `[AMBIGUOUS] {filename}: cannot confidently
infer class`, and never write to any file (report-only, no `--fix` in this
Plan's scope).

## Alternatives considered
Inferring `class` from a document's `area` value or existing `## ` heading
structure alone (without a human-readable signal like "Reference" in the
filename) was considered, but rejected as too unreliable — `area` values
(agent/mcp/rag/...) do not map 1:1 to the 7 document classes (a `class:
Reference` document can exist in any `area`), so this would produce too many
false "confident" classifications; require an explicit, class-name-adjacent
signal instead.

## Implementation
### Target file
tools/manage_frontmatter.py

### Procedure
1. Add `cmd_classify(argv)` function (after `cmd_dedupe_lists()`, matching the
   existing functions' `argv: list[str] | argparse.Namespace | None = None`
   signature convention).
2. Read `class_enum` via `load_front_matter_schema()` (already imported, line
   39) — use it as the authoritative list of valid class values rather than a
   second hardcoded copy.
3. Register a `classify` subparser in `main()` (after the existing
   `dedupe-lists` subparser registration).

### Method
Direct code edit (`Edit` tool), following the existing subcommand pattern
exactly.

### Details
- Confident-inference signals (illustrative, refine during actual
  implementation against real `docs/` filenames): filename contains
  `reference-api`/`-reference`/`_reference` → `Reference`; filename matches
  `NN_governance_*` → `Governance`; filename matches `*_document-guide.md` →
  `Guide`; a `## Known Issues`-only document with `Note`/`Known Issues` framing
  → `Known Issues`. Anything not matching a clear signal is `[AMBIGUOUS]`.
- Never write `class:` into any file in this subcommand (no `--fix` flag is
  added, unlike `cmd_add_missing`/`cmd_rename_category_to_area` which both have
  one) — per `REQ-004`'s explicit "dry-run/report mode... without modifying any
  file" requirement.
- Report format matches `cmd_add_missing`'s existing style exactly (`[AMBIGUOUS]
  {filename}: ...` / a confident-case equivalent), for consistency across the
  file's subcommands.

## Compatibility considerations
New subcommand, additive to `main()`'s subparser registration — no existing
subcommand's behavior changes.

## Security considerations
N/A: read-only file scanning (report-only, no writes), no credentials or
network access.

## Rollback considerations
`git checkout -- tools/manage_frontmatter.py` reverts this row independently.

## Validation plan
- `uv run pytest tests/tools/test_manage_frontmatter.py -v` (seq 07's new
  tests).
- `uv run python tools/manage_frontmatter.py classify` (manual dry-run against
  the real `docs/` tree) — confirm it modifies no file and reports ambiguous
  documents.
- `uv run ruff check tools/manage_frontmatter.py`, `uv run mypy
  tools/manage_frontmatter.py`.

## Completion criteria
- `tools/manage_frontmatter.py classify` runs against the current `docs/` tree,
  modifies no file, and reports confidently-classifiable vs. ambiguous
  documents.
- Consistent with `cmd_add_missing()`'s existing never-guess pattern.

## Out of scope
A `--fix` write mode; classifying all existing documents in this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260919-122343 | 20260919-122343 | Depends on seq 02's `class_enum` existing |
| 2 | Add or update tests per Validation plan | Completed | 20260919-122343 | 20260919-122343 | Tests live in seq 07's document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260919-122343 | 20260919-122343 | `tools/`-scoped lighter sequence |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260919-122343 | 20260919-122343 | N/A: no docs/*.md reference required for this row |

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
- **Requirement ID**: REQ-004 (add classify subcommand)
- **Source issue**: issues/done/20260918-130249_docsmeta01_add-class-front-matter-field.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-105328_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-115041
- **Related target files**: tools/manage_frontmatter.py
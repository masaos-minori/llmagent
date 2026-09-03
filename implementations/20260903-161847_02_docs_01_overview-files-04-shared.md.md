## Goal
Repair `docs/01_overview-files-04-shared.md`'s unterminated front matter (add
the missing closing `---`) and rename `category: overview` to `area: overview`
in the same edit, preserving all other existing front-matter content unchanged.

## Scope
- **In-Scope**: `docs/01_overview-files-04-shared.md`'s front-matter block
  only (lines 1-10 as of 2026-09-03) — adding a closing `---` and renaming the
  `category:` key to `area:`.
- **Out-of-Scope**: `docs/01_overview-files-03-scripts.md` (seq 01 of this
  Plan); the 43 missing-front-matter files (seq 03); the 11 ADR `tags`
  additions (seq 04); any body content of this file.

## Assumptions
- The file's front matter (lines 1-10) is unchanged from this Plan's own
  citation — re-verified 2026-09-03 by direct `Read`: opening `---` at line 1,
  `category: overview` at line 3, `related:` list at lines 9-10 (one entry, a
  self-reference to `01_overview-files-04-shared.md`), no closing `---`, blank
  line 11, then `# File Structure` H1 at line 12 — the Plan's stated repair
  location ("immediately before the first body line").
- `tools/manage_frontmatter.py`'s `rename-category-to-area` subcommand cannot
  safely handle this file, since it requires an already-`---`-terminated
  block by design — this row's manual `Edit` is the only safe path, consistent
  with this Plan's own Background finding.

## Design decisions
- **The closing `---` is inserted immediately after the `related:` list's
  entry (after line 10), before the existing blank line and `# File
  Structure` H1** — the exact, unambiguous location this Plan's own corrected
  REQ-001 specifies.
- **The `related:` list's single self-reference entry
  (`01_overview-files-04-shared.md`) is left untouched**, even though a
  document self-referencing itself as "related" is a data-quality question —
  REQ-001's own wording says to preserve "`title`/`tags`/`related` content
  unchanged"; this is noted as a Plan Gap (a milder version of the same
  observation made for seq 01's sibling file, which has 4 duplicate
  self-references instead of 1), not fixed here.
- **Only `category:` is renamed to `area:` — `overview` (the value) is
  unchanged** — matches REQ-001's explicit "(value unchanged)" instruction.

## Alternatives considered
- **Also remove the single self-referencing `related:` entry while already
  editing this front-matter block** — rejected: REQ-001's own wording
  specifies preserving `related` content unchanged; this row's scope is the
  fence repair and key rename only, matching the treatment already applied to
  the sibling file (seq 01) for consistency.

## Implementation
### Target file
`docs/01_overview-files-04-shared.md`

### Procedure
1. Re-read lines 1-12 in full immediately before editing to reconfirm no
   drift (done above; confirmed identical to this Plan's citation).
2. Insert a closing `---` immediately after the `related:` list's entry.
3. Rename `category:` to `area:` (value unchanged) in the same edit.

### Method
Direct text edit (e.g. via the `Edit` tool) using the exact before/after block
in Details.

### Details

Before:
```
---
title: "Shared Infrastructure File Structure: venv/db/ + scripts/db/ (Part 1/2)"
category: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared.md

# File Structure
```

After:
```
---
title: "Shared Infrastructure File Structure: venv/db/ + scripts/db/ (Part 1/2)"
area: overview
tags:
  - shared
  - db
  - sqlite
  - file-structure
related:
  - 01_overview-files-04-shared.md
---

# File Structure
```

## Compatibility considerations
No other document links to this file's front matter by anchor. Independent of
seq 01/03/04 — this row's own edit is unrelated to any other row's target
file.

## Security considerations
None — documentation-only front-matter repair; no code, credentials, or
access-control content is affected.

## Rollback considerations
Single-file, single-edit change to a Markdown document under version control;
revert via `git revert`. No other file depends on this file's front-matter
structure.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/01_overview-files-04-shared.md | Structure/front-matter check | `uv run python tools/check_docs_structure.py docs/01_overview-files-04-shared.md` | No "opening '---' has no closing '---'" finding; `area:` present, `category:` absent |
| docs/01_overview-files-04-shared.md | Key-presence check | `grep -n "^category:\|^area:" docs/01_overview-files-04-shared.md` | `category:` absent; `area: overview` present |
| docs/01_overview-files-04-shared.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |

## Completion criteria
- `docs/01_overview-files-04-shared.md` has a properly `---`-terminated front
  matter block with no "opening '---' has no closing '---'" finding, and uses
  `area: overview` (not `category:`) (AC-1).
- `uv run python tools/check_docs_structure.py docs/01_overview-files-04-shared.md`
  and `uv run python tools/check_docs_quality.py` report no new errors.

## Out of scope
`docs/01_overview-files-03-scripts.md` (seq 01), the 43 missing-front-matter
files (seq 03), the 11 ADR `tags` additions (seq 04) — each covered by its own
implementation-procedure document per this Plan's Implementation Target Files
table. The `related:` list's self-reference entry — a pre-existing
data-quality observation, reported as a Plan Gap, not this row's scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260902-194021_docmeta02_migrate_all_documents_to_canonical_metadata_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-125112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-161847
- **Related target files**: docs/01_overview-files-04-shared.md

## Goal
Repair `docs/01_overview-files-03-scripts.md`'s unterminated front matter (add
the missing closing `---`) and rename `category: overview` to `area: overview`
in the same edit, preserving all other existing front-matter content unchanged.

## Scope
- **In-Scope**: `docs/01_overview-files-03-scripts.md`'s front-matter block
  only (lines 1-14 as of 2026-09-03) — adding a closing `---` and renaming the
  `category:` key to `area:`.
- **Out-of-Scope**: `docs/01_overview-files-04-shared.md` (seq 02 of this
  Plan); the 43 missing-front-matter files (seq 03); the 11 ADR `tags`
  additions (seq 04); any body content of this file (per this Plan's own
  Scope: "any document body-content change" is out of scope) — including the
  `related` field's 4 duplicate self-references (`01_overview-files-03-scripts.md`
  listed 4 times, lines 10-13), which are a pre-existing data-quality issue
  this row does not fix (see Design decisions).

## Assumptions
- The file's front matter (lines 1-14) is unchanged from this Plan's own
  citation — re-verified 2026-09-03 by direct `Read`: opening `---` at line 1,
  `category: overview` at line 3, `related:` list at lines 9-14 (4 duplicate
  self-references plus one Markdown-link-style entry to `01_overview.md`), no
  closing `---`, blank line 15, then `# File Structure` H1 at line 16 — the
  Plan's stated repair location ("immediately before the first body line").
- `tools/manage_frontmatter.py`'s `rename-category-to-area` subcommand cannot
  safely handle this file, since it requires an already-`---`-terminated
  block by design (re-verified 2026-09-03 by direct `Read` of
  `tools/manage_frontmatter.py:308-...`) — this row's manual `Edit` is the
  only safe path, consistent with this Plan's own Background finding.

## Design decisions
- **The closing `---` is inserted immediately after the `related:` list's
  last entry (after line 14), before the existing blank line and `# File
  Structure` H1** — this is the exact, unambiguous location this Plan's own
  corrected REQ-001 specifies, chosen during the Plan's own correction pass
  (not left for this row to judge independently, per that Plan's Risk
  mitigation).
- **The `related:` list's 4 duplicate self-references are left untouched**,
  even though they are visibly a data-quality issue (a document should not
  need to list itself as "related" four times) — this Plan's Scope explicitly
  excludes "any document body-content change," and while front matter is not
  strictly "body" content, REQ-001's own wording says to preserve
  "`title`/`tags`/`related` content unchanged" — fixing this is a Plan Gap,
  reported here rather than silently corrected, since it is unrelated to the
  fence-repair/rename this row performs.
- **Only `category:` is renamed to `area:` — `overview` (the value) is
  unchanged** — matches REQ-001's explicit "(value unchanged)" instruction and
  the filename-prefix-implied area (`01_` → `overview`) this Plan's own
  Assumptions table already confirms.

## Alternatives considered
- **Also deduplicate the `related:` list's 4 identical self-reference
  entries down to 1, while already editing this front-matter block** —
  considered, rejected (see Design decisions): this Plan's Scope and REQ-001's
  own wording both specify preserving existing `related` content unchanged;
  fixing an unrelated, adjacent data-quality issue here would exceed this
  row's authorized scope, even though the fix would be small — reported as a
  Plan Gap instead.

## Implementation
### Target file
`docs/01_overview-files-03-scripts.md`

### Procedure
1. Re-read lines 1-16 in full immediately before editing to reconfirm no
   drift (done above; confirmed identical to this Plan's citation).
2. Insert a closing `---` immediately after the `related:` list's last entry.
3. Rename `category:` to `area:` (value unchanged) in the same edit.

### Method
Direct text edit (e.g. via the `Edit` tool) using the exact before/after block
in Details.

### Details

Before:
```
---
title: "Scripts File Structure: Agent Core & Memory (Part 1/5)"
category: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - [01_overview.md](01_overview.md)

# File Structure
```

After:
```
---
title: "Scripts File Structure: Agent Core & Memory (Part 1/5)"
area: overview
tags:
  - scripts
  - agent
  - mcp-server
  - file-structure
related:
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-03-scripts.md
  - [01_overview.md](01_overview.md)
---

# File Structure
```

## Compatibility considerations
No other document links to this file's front matter by anchor. Independent of
seq 02/03/04 — this row's own edit is unrelated to any other row's target
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
| docs/01_overview-files-03-scripts.md | Structure/front-matter check | `uv run python tools/check_docs_structure.py docs/01_overview-files-03-scripts.md` | No "opening '---' has no closing '---'" finding; `area:` present, `category:` absent |
| docs/01_overview-files-03-scripts.md | Key-presence check | `grep -n "^category:\|^area:" docs/01_overview-files-03-scripts.md` | `category:` absent; `area: overview` present |
| docs/01_overview-files-03-scripts.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |

## Completion criteria
- `docs/01_overview-files-03-scripts.md` has a properly `---`-terminated front
  matter block with no "opening '---' has no closing '---'" finding, and uses
  `area: overview` (not `category:`) (AC-1).
- `uv run python tools/check_docs_structure.py docs/01_overview-files-03-scripts.md`
  and `uv run python tools/check_docs_quality.py` report no new errors.

## Out of scope
`docs/01_overview-files-04-shared.md` (seq 02), the 43 missing-front-matter
files (seq 03), the 11 ADR `tags` additions (seq 04) — each covered by its own
implementation-procedure document per this Plan's Implementation Target Files
table (individually or consolidated, per the user's explicit grouping
decision for this Plan's downstream generation). The `related:` list's 4
duplicate self-references — a pre-existing data-quality issue, reported as a
Plan Gap, not this row's scope.

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
- **Related target files**: docs/01_overview-files-03-scripts.md

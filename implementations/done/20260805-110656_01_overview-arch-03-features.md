# Implementation Procedure: 01_overview-arch-03-features.md

## Goal

- Deduplicate the "実装済み機能サマリ" table (§2.5) in `docs/01_overview-arch-03-features.md`
  so that filename-level detail lives only in the `docs/01_overview-files-03-scripts-part*.md`
  series, and the §2.5 table only records directory-level location per feature.

## Scope

- In scope: rewriting the §2.5 table's "実装場所" column to use `scripts/` directory paths
  (not individual filenames); ensuring a Markdown pointer to
  `docs/01_overview-files-03-scripts-part*.md` is present below the table.
- Out of scope: `docs/01_overview-files-03-scripts-part*.md` contents; the "実装上の補足"
  section (lines 45-73 of the current file); any source code under `scripts/`.

## Assumptions

- The `scripts/` directory structure referenced by the table (`scripts/rag/`,
  `scripts/agent/`, `scripts/shared/`, `scripts/agent/memory/`, `scripts/agent/commands/`,
  `scripts/agent/workflow/`, `scripts/db/`) remains valid at implementation time — reverify
  with `ls scripts/` before editing.
- `docs/01_overview-files-03-scripts-part1.md` (and sibling part files) remain the canonical
  filename-level reference; no restructuring of that series is assumed.

## Design decisions

- Single source of truth: per `skills/DESIGN.md` §Avoid implementation-reference duplication
  (referenced via `skills/python-design/SKILL.md`), filename-level detail should live in one
  place only — the `part*.md` series — and §2.5 should reference it rather than repeat it.
- Keep the change file-scoped and minimal (YAGNI): only the table cell contents and the
  pointer line change; no reformatting of unrelated table rows or surrounding prose.

## Alternatives considered

- Remove the §2.5 table entirely and link straight to the `part*.md` series: rejected —
  the plan explicitly keeps the table as a directory-level summary for quick orientation.
- Link each row to its own specific `part*.md` file/section: rejected as unnecessary
  granularity: a single pointer below the table (already present at line 43) is sufficient
  and matches the plan's stated scope.

## Implementation

### Target file

- `docs/01_overview-arch-03-features.md` (§2.5 table, lines 25-43 as currently observed;
  reconfirm line numbers before editing since the file may have shifted).

### Procedure

1. Preparation: re-read the current §2.5 table verbatim (`grep -n "2\.5" docs/01_overview-arch-03-features.md`
   then read the surrounding range) to confirm exact row text before editing.
2. Core edit: for each row in the "実装場所" column, replace any filename with the
   corresponding `scripts/`-prefixed directory path; keep column values uniform in style
   (trailing slash, `scripts/` prefix).
3. Confirm the pointer sentence to `docs/01_overview-files-03-scripts-part1.md` (or the
   full `part*.md` series) exists directly below the table; add it if missing.
4. Verification: re-read the edited section and confirm no bare filenames remain in the
   table and the pointer link resolves to an existing file.

### Method

- Use a precise `Edit` (old_string/new_string) on the table block only; do not touch the
  "実装上の補足" section or the `## Related Documents` / `## Keywords` sections.
- Investigate current state via `grep -n "^## \|2\.5" docs/01_overview-arch-03-features.md`
  and a bounded `Read` (offset/limit) rather than loading the whole file.

### Details

- Current observed table (13 rows, `機能` / `実装場所` columns) already uses directory-level
  paths for every row (`scripts/rag/`, `scripts/agent/`, `scripts/shared/`,
  `scripts/agent/memory/`, `scripts/db/`, `scripts/agent/commands/`,
  `scripts/agent/workflow/`) — no bare filenames were found in the current content.
- A pointer sentence to `docs/01_overview-files-03-scripts-part1.md` already exists
  immediately below the table (current line 43).
- Implication for the implementer: at execution time, first re-verify with `grep`/`Read`
  whether the table already satisfies the plan's end state; if so, this item may require
  no textual change beyond confirming the pointer text still matches the plan's wording,
  and the verification phase (Phase 3) can be executed directly.

## Compatibility considerations

- No code or API surface is affected; this is a documentation-only edit.
- Ensure any other doc that links directly to a filename previously listed in this table
  (if any existed) is not silently orphaned — out of scope to fix here, but flag if found.

## Security considerations

- N/A — documentation-only change, no secrets or executable content involved.

## Rollback considerations

- Single-file Markdown edit; revert via `git checkout -- docs/01_overview-arch-03-features.md`
  or `git revert` of the associated commit if the change needs to be undone.

## Validation plan

- Manual inspection: `grep -n "scripts/" docs/01_overview-arch-03-features.md` to confirm
  only directory paths (ending in `/`) appear in the §2.5 table, no bare `.py` filenames.
- Confirm the pointer line resolves: `ls docs/01_overview-files-03-scripts-part1.md`.
- No automated test suite applies (documentation-only); `rules/toolchain.md`'s
  code-oriented validation sequence (ruff/mypy/pytest/etc.) is not applicable to this item.

## Out of scope

- Editing `docs/01_overview-files-03-scripts-part*.md`.
- Editing the "実装上の補足" section.
- Any `scripts/` source code change.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260802-183000_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-110656
- Related target files: 01_overview-arch-03-features.md

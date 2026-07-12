# Implementation Procedure: docs/90_shared_00_document-guide.md

Source plan: `plans/20260712-191723_plan.md`
Source requirement: `requires/done/20260712_17_require.md`

## Goal

`docs/90_shared_00_document-guide.md` no longer names specific resolved known-issue codes
(`DOCREF-01`, `CONFIG-01/02/03`, `GLOBAL-01`, `PLUGIN-01`, `IMPORT-01`, `DOCFIELD-01`) that
were already removed from `docs/90_shared_90_inconsistencies_and_known_issues.md` (e.g.
`DOCREF-01` in commit `5d0699f8`), replacing them with wording matching the catalog's current
(empty) state.

## Scope

**In scope:** two specific locations in `docs/90_shared_00_document-guide.md`:
1. The "Navigation to Major Known Issues" prose line (originally line 57)
2. The "Inconsistencies" row of the File Index table (originally line 116)

**Out of scope:** every other section of the file; `docs/90_shared_90_inconsistencies_and_known_issues.md`
itself (not touched — stays as the empty-but-present catalog file).

## Assumptions

1. No other `docs/*.md` file names any of the six codes — verified via
   `grep -n "DOCREF-01\|CONFIG-01\|GLOBAL-01\|PLUGIN-01\|IMPORT-01\|DOCFIELD-01" docs/*.md`
   returning no matches after the edit.
2. `docs/90_shared_01_03_overview-constraints-and-reference.md` (a separate file that also
   links to the same catalog) contains only a generic link with no code-specific mentions, so
   it needs no corresponding edit — confirmed directly.

## Implementation

### Target file

`docs/90_shared_00_document-guide.md`

### Procedure

*(Both edits were already applied directly during the investigation that produced the source
requirement — see requirement §"AI実装者への注記". This document formalizes them
retroactively.)*

1. **Prose line** — changed:
   ```
   既知の不整合(DOCREF-01、DOCFIELD-01等)の全カタログは [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) を参照。`ArtifactEvent`にイベントバスがない点は対象外(データ定義のみ)。
   ```
   to:
   ```
   既知の不整合の全カタログは [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) を参照(現時点でオープンな項目はない)。`ArtifactEvent`にイベントバスがない点は対象外(データ定義のみ)。
   ```
2. **File Index table row** — changed:
   ```
   | [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | DOCREF-01, CONFIG-01/02/03, GLOBAL-01, PLUGIN-01, IMPORT-01, DOCFIELD-01、他 |
   ```
   to:
   ```
   | [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | 既知の不整合カタログ(現時点でオープンな項目はない) |
   ```

### Method

Direct Markdown text replacement at both locations. Both changes are wording-only — the link
target (`90_shared_90_inconsistencies_and_known_issues.md`) and table structure are unchanged.

### Details

- The replacement wording ("現時点でオープンな項目はない") mirrors the phrasing used in the
  companion fix to `docs/04_mcp_00_document-guide.md` (`implementations/20260712-192358_docs_04_mcp_00_document-guide.md`)
  for consistency across both domains fixed by the same requirement.
- Both locations must be updated together — leaving one stale while fixing the other would
  reintroduce the same inconsistency this change is meant to remove.

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Dangling reference scan | `grep -n "DOCREF-01\|CONFIG-01\|GLOBAL-01\|PLUGIN-01\|IMPORT-01\|DOCFIELD-01" docs/*.md` | no output |
| Docs consistency | `uv run python tools/check_docs_consistency.py` | All checks passed |

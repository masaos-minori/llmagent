# Implementation Procedure: docs/05_agent_90_inconsistencies_and_known_issues.md

Source plan: `plans/20260712-191629_plan.md`
Source requirement: `requires/done/20260712_16_require.md`

## Goal

`docs/05_agent_90_inconsistencies_and_known_issues.md` no longer carries a stale
"未解決の疑問点" entry for a session-recovery gap that `/db session recover`
(commit `8c9f93c8`) already closed.

## Scope

**In scope:** the `## 未解決の疑問点` section of
`docs/05_agent_90_inconsistencies_and_known_issues.md`.

**Out of scope:** every other section of the same file (前文, `## 未文書化領域`,
Related Documents, Keywords); this file's original addition of the gap note
(`implementations/done/20260621-183000_unify_agent_session_rag_maintenance.md`) is historical
context only and is not modified.

## Assumptions

1. The edit is subtractive only — no replacement text is needed, unlike `UNDOC-02` in the
   same file, because no other doc points readers at this heading for further detail (verified:
   `grep -rn "セッション SQLite 破損復旧" docs/*.md` returns no matches once this heading is removed).
2. Removing the heading does not leave a dangling `---` separator or an empty section between
   the front matter and `## 未文書化領域`.

## Implementation

### Target file

`docs/05_agent_90_inconsistencies_and_known_issues.md`

### Procedure

*(This edit was already applied directly during the investigation that produced the source
requirement — see requirement §"AI実装者への注記". This document formalizes it retroactively
and defines the remaining verification-only step, per 02_design.md's file-level procedure
format.)*

1. Removed the following block (previously between the "各エントリの形式" list and
   `## 未文書化領域`):
   ```markdown
   ---

   ## 未解決の疑問点

   ### セッション SQLite 破損復旧のギャップ

   - `/db rag recover [backup-path]` は `rag.sqlite` のみを対象とする（`RagMaintenanceService` 経由）
   - `/db session recover [backup-path]` が存在する。`DbMaintenanceService.recover_session()` → `recover_corruption(backup_path, target="session")` を呼び出す
   - オペレーターの操作: `/db session recover /path/to/backup.sqlite`

   ---
   ```
2. Left exactly one `---` separator between the intro/format-list block and
   `## 未文書化領域` (the file's existing separator convention — one `---` between each H2
   section — is preserved, not doubled).

### Method

Direct Markdown deletion — no template or generator involved. This is a one-file, one-section
subtractive edit.

### Details

- No replacement note (unlike `UNDOC-02`, which got a short italic "resolved" note) is added,
  because the two recovery commands this entry described are already documented in full in
  the CLI-reference docs (`/db rag recover`, `/db session recover`); there is nothing left for
  a reader to be redirected to that isn't already covered elsewhere.
- Verify after the edit that the file structure reads: front matter → title → intro paragraph
  → "各エントリの形式" list → `---` → `## 未文書化領域` → `---` → `## Related Documents` →
  `## Keywords`, with no doubled or missing `---` separators.

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Dangling reference scan | `grep -rn "セッション SQLite 破損復旧" docs/*.md` | no output |
| Docs consistency | `uv run python tools/check_docs_consistency.py` | All checks passed |
| Docs structure | `uv run python tools/validate_docs_structure.py` | All checks passed |
| Manual structure read | `cat docs/05_agent_90_inconsistencies_and_known_issues.md` | no empty `##` headings, no doubled `---` |

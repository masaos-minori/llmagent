# Implementation Procedure: 05_agent_07_07_cli-and-commands-migration-notes.md

## Goal

Update the "`/db`フラットエイリアス(削除)" section so it correctly reflects that
`/db` itself no longer exists at all (not merely that its old flat-alias forms were
removed in favor of scoped `/db rag`/`/db session` forms), removing the
`/db rag recover`/`/db rag stats` rows from the migration table and rewording the
surrounding prose accordingly.

## Scope

### In scope
- Reword the section heading and lead-in prose (current lines 42-44) to state that
  `/db` (all of it — flat aliases, `/db rag <subcmd>`, and `/db session <subcmd>`)
  has been removed, with `/session <subcmd>` as the sole remaining path for former
  `/db session` operations, and no remaining path for former `/db rag` operations
  (per this plan's scope — RAG-side removal was already handled by an earlier,
  unrelated change).
- Remove the `/db rag recover [backup-path]` and `/db rag stats` mentions from the
  replacement column of the migration table (current lines 51, 52) since `/db rag`
  itself no longer exists as a valid replacement target.
- Update the table's other rows (current lines 48-56) whose "replacement" column
  currently reads `/db session ...` to instead read `/session ...`.
- Update the trailing prose (current line 59) which currently says "フラット形式を
  入力すると使用方法(usage)メッセージが表示され、実行はされない" — this remains
  true for `/db` itself now (any `/db ...` input is simply unrecognized), but the
  test-reference (`tests/test_agent_cmd_db.py`の...) must be updated since that file
  is deleted by this plan (point instead at whatever regression coverage replaces it,
  e.g. a note that `/db` is no longer a recognized command at all, verified by
  `tests/test_command_def_sync.py`/`tests/test_cmd_registry_ingest_removal.py`).

### Out of scope
- The "`/note`コマンド群(削除)" section (lines 30-32) — unrelated, unchanged.
- The "`/ingest`コマンド(削除)" section (lines 34-36) — unrelated, unchanged.
- The "`/debug audit`サブコマンド(削除)" section (lines 38-40) — unrelated, unchanged.
- Front-matter and "Related Documents"/"Keywords" sections (lines 1-20, 61-81) —
  content unchanged in structure, though the "Keywords" list's `/db flat alias
  removal` entry should be reviewed for continued accuracy (see Details).

## Assumptions

- This document's current "`/db`フラットエイリアス(削除)" table (lines 46-57)
  already reflects the state *before* this plan (i.e. `/db rag <subcmd>`/`/db
  session <subcmd>` scoped forms were assumed valid replacements) — this plan
  changes that assumption because `/db` in its entirety is removed, so every row's
  "置き換え" column that names a `/db ...` form is now stale and must be corrected
  to name `/session ...` (for session ops) or "no longer available" (for rag ops,
  since this plan does not restore any `/rag`-adjacent surface).
- `tests/test_agent_cmd_db.py`, referenced in this doc's current prose (line 59), is
  deleted by this plan (see that file's own implementation doc) — any reference to
  it must be replaced with a reference to whatever test now covers "`/db` is
  unrecognized" (likely `tests/test_cmd_registry_ingest_removal.py` or
  `tests/test_command_def_sync.py`, or a new assertion added to
  `tests/test_agent_cmd_session.py` confirming `/db ...` inputs are dispatched as
  unknown commands).

## Implementation

### Target file

`docs/05_agent_07_07_cli-and-commands-migration-notes.md`

### Procedure

1. Change the section heading and lead-in from:
   ```markdown
   ### `/db`フラットエイリアス(削除)

   以下のスコープなしフラット形式は廃止され、`/db rag <subcmd>`または`/db session <subcmd>`のスコープ付き形式のみが有効である。
   ```
   to:
   ```markdown
   ### `/db`コマンド(完全削除)

   `/db`は、そのフラットエイリアス形式・`/db rag <subcmd>`形式・`/db session <subcmd>`形式のすべてを含めて廃止された。旧`/db session <subcmd>`の機能は`/session <subcmd>`へ移管されている。旧`/db rag <subcmd>`の機能に対する後継コマンドは提供されない。
   ```
2. Update the migration table rows so the "置き換え" column reflects the new
   reality:
   ```markdown
   | 廃止された形式 | 現在の状態 |
   |---|---|
   | `/db urls [--lang] [--limit]` | 後継コマンドなし(RAGパイプライン側のMCPツールを直接利用) |
   | `/db clean <url>` | 後継コマンドなし |
   | `/db rebuild-fts` | 後継コマンドなし |
   | `/db recover [backup-path]` | `/session recover [backup-path]` |
   | `/db stats` | `/session stats` |
   | `/db health` | `/session health` |
   | `/db checkpoint [MODE]` | `/session checkpoint [MODE]` |
   | `/db vacuum` | `/session vacuum` |
   | `/db purge [--max-sessions N] [--max-age-days N]` | `/session purge [--max-sessions N] [--max-age-days N]` |
   | `/db consistency` | 後継コマンドなし |
   ```
3. Update the trailing prose (current line 59) from:
   ```markdown
   フラット形式を入力すると使用方法(usage)メッセージが表示され、実行はされない(根拠: Explicit in code — `tests/test_agent_cmd_db.py`のフラットエイリアス無効テスト群)。後方互換は提供されていない。
   ```
   to:
   ```markdown
   `/db`はいかなる形式(フラット・`rag`スコープ・`session`スコープ)でももはや認識されるコマンドではなく、未知のスラッシュコマンドとして扱われる(根拠: Explicit in code — `agent/commands/command_defs_list.py`に`/db`の`CommandDef`が存在しない、および`tests/test_cmd_registry_ingest_removal.py`/`tests/test_command_def_sync.py`の回帰テスト)。後方互換は提供されていない。
   ```
4. Update the "Keywords" section (bottom of file, current lines 75-81) — the
   `/db flat alias removal` line remains broadly accurate (the file still discusses
   `/db`'s removal) but consider adding a `/db removed entirely` keyword for
   discoverability.

### Method

Targeted prose + table rewrite reflecting a scope change (partial-alias-removal →
full-command-removal), coordinated with `05_agent_07_08_...md` (which gains the
`/session` DB-op rows) and `05_agent_07_09_...md` (which loses its DB category
section entirely).

### Details

- Do not simply delete table rows without rewording the surrounding prose (this is
  explicitly called out in the plan's Risk section: naive row deletion would leave
  misleading prose implying `/db rag <subcmd>`/`/db session <subcmd>` are still
  valid replacement forms, when in fact only `/session <subcmd>` survives and only
  for the former session-scoped operations).
- Cross-check the "Related Documents" list (lines 61-73) still correctly points at
  `05_agent_07_08_...md` and `05_agent_07_09_...md` — no link changes needed, only
  their target content changes.

## Validation plan

- Manual read-through: confirm no remaining prose implies `/db rag <subcmd>` or
  `/db session <subcmd>` are valid, executable forms.
- Confirm every "後継コマンドなし" (no successor) row accurately reflects that no
  equivalent command exists post-plan (cross-check against `cmd_db.py`'s deletion
  and the absence of any `/rag`-adjacent restoration in this plan's scope).
- Confirm every `/session ...` row exactly matches the subcommand names implemented
  in `cmd_session.py` (see that file's own implementation doc) — no typos or
  mismatched flag names (e.g. `--max-sessions`/`--max-age-days` must match
  `DbSessionOps.purge`'s actual flag names verbatim).
- Cross-check `05_agent_07_08_...md` and `05_agent_07_09_...md` for consistency — no
  contradictory claims about where `/db session`'s functionality now lives.

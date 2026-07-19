## Goal

Update the `/db rebuild-fts` migration-notes row in
`docs/05_agent_07_07_cli-and-commands-migration-notes.md` to point at the new `/session
rag-rebuild-fts` command (added in `implementations/20260719-103526_cmd_session.py.md`), since a
successor now exists where the doc previously said none did.

This is the fix for the source issue
(`issues/20260719-091341_rag_consistency_repair_guidance_points_to_removed_db_command.md`): the
`/db rebuild-fts` row currently says `後継コマンドなし` (no successor command), which is what made the
stale runtime guidance strings in `rag_consistency.py` misleading in the first place.

**Independent of the `/db consistency` row change**: `implementations/20260719-103231_05_agent_07_07_..._migration-notes.md.md`
(prior cycle) updates a *different* row in this same table (`/db consistency` → `/session
rag-consistency`, line 57). This doc edits the `/db rebuild-fts` row (line 50), a distinct table row
— no overlap, both edits are independent single-cell changes to the same table and can land in
either order without conflict.

## Scope

**In scope**
- Change the `/db rebuild-fts` row's "現在の状態" (current state) cell from `後継コマンドなし` to
  `` `/session rag-rebuild-fts` `` (matching the format of rows that do have a successor, e.g.
  `/db recover` → `` `/session recover [backup-path]` ``).

**Out of scope**
- The `/db consistency` row (line 57) — covered by the prior cycle's
  `implementations/20260719-103231_..._migration-notes.md.md`; not touched here.
- Any other row in this table (`/db urls`, `/db clean`, which genuinely have no successor and are
  correctly left as `後継コマンドなし`).
- Any change to the table's column structure or surrounding prose.

## Assumptions

1. Verified by direct grep/read of `docs/05_agent_07_07_cli-and-commands-migration-notes.md`
   (current file, no drift from the plan's citation of "line 58" — actual current line is 50):
   ```
   46:| 廃止された形式 | 現在の状態 |
   47:|---|---|
   48:| `/db urls [--lang] [--limit]` | 後継コマンドなし(RAGパイプライン側のMCPツールを直接利用) |
   49:| `/db clean <url>` | 後継コマンドなし |
   50:| `/db rebuild-fts` | 後継コマンドなし |
   51:| `/db recover [backup-path]` | `/session recover [backup-path]` |
   52:| `/db stats` | `/session stats` |
   53:| `/db health` | `/session health` |
   54:| `/db checkpoint [MODE]` | `/session checkpoint [MODE]` |
   55:| `/db vacuum` | `/session vacuum` |
   56:| `/db purge [--max-sessions N] [--max-age-days N]` | `/session purge [--max-sessions N] [--max-age-days N]` |
   57:| `/db consistency` | 後継コマンドなし |
   ```
   Note: the plan text cites "line 58" for this row; direct read confirms the `/db rebuild-fts` row is
   actually at **line 50** in the current file (2-column table, `廃止された形式 | 現在の状態`). This is
   flagged explicitly per this workflow's stale-plan-detail rule: the plan's line number is stale/off
   by 8 relative to current file state — the row content and required change are otherwise exactly as
   the plan describes, only the cited line number is wrong. Once the prior cycle's
   `/db consistency` row edit (line 57) lands, this table's line numbers are unaffected by that edit
   (a same-line cell replacement, not an insertion), so line 50 remains correct for `/db rebuild-fts`
   regardless of whether that other doc has landed yet.
2. Rows with a successor use the format `` `/session <subcmd> [args]` `` (backtick-quoted, exact
   command syntax, no extra prose) — e.g. line 51's `` `/session recover [backup-path]` ``. The new
   value for line 50 follows the same format: `` `/session rag-rebuild-fts` `` (no arguments, since
   `_rag_rebuild_fts` takes none, per `implementations/20260719-103526_cmd_session.py.md`).
3. This edit is independent of, and does not depend on, whether
   `implementations/20260719-103231_05_agent_07_07_..._migration-notes.md.md`'s `/db consistency` row
   edit (line 57) has landed — both are single-cell edits to different rows in the same static table,
   with no shared line-shifting risk.

## Implementation

### Target file

`docs/05_agent_07_07_cli-and-commands-migration-notes.md`.

### Procedure

1. Edit line 50 (verified current line; the plan cites line 58, which is stale — see Assumption 1)
   from:
   ```
   | `/db rebuild-fts` | 後継コマンドなし |
   ```
   to:
   ```
   | `/db rebuild-fts` | `/session rag-rebuild-fts` |
   ```
2. Leave all other rows (lines 48-49, 51-57) unchanged, including line 57
   (`/db consistency`), whose edit is tracked separately by the prior cycle's doc.

### Method

Single Markdown table-cell edit. No structural change to the document.

### Details

No code changes. Purely a documentation-cell update to match the newly-added successor command,
directly resolving the source issue's reported stale-guidance problem at its root (the migration
table itself, not just the runtime message).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Row updated | `rg -n "db rebuild-fts" docs/05_agent_07_07_cli-and-commands-migration-notes.md` | shows `/session rag-rebuild-fts` as the paired cell, not `後継コマンドなし` |
| No unintended row changes | `sed -n '46,57p' docs/05_agent_07_07_cli-and-commands-migration-notes.md` | only line 50 differs from the pre-edit content quoted in Assumption 1 (line 57 may also differ if the prior cycle's doc has landed — that is expected and out of this doc's scope) |
| Docs consistency checker | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING introduced |
| Cross-reference with code | `rg -n "rag-rebuild-fts" scripts/agent/commands/cmd_session.py docs/05_agent_07_07_cli-and-commands-migration-notes.md` | both files reference the same subcommand name |
| No remaining stale row | `rg -n "rebuild-fts.*後継コマンドなし" docs/05_agent_07_07_cli-and-commands-migration-notes.md` | 0 matches |

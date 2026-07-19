## Goal

Update the `/db consistency` migration-notes row in
`docs/05_agent_07_07_cli-and-commands-migration-notes.md` to point at the new `/session
rag-consistency` command (added in `implementations/20260719-102923_cmd_session.py.md`), since a
successor now exists where the doc previously said none did.

## Scope

**In scope**
- Change the `/db consistency` row's "現在の状態" (current state) cell in
  `docs/05_agent_07_07_cli-and-commands-migration-notes.md` from `後継コマンドなし` (no successor
  command) to `` `/session rag-consistency` `` (matching the format of the other rows in the same
  table that do have a successor, e.g. `/db recover` → `` `/session recover [backup-path]` ``).

**Out of scope**
- Any other row in this table (e.g. `/db urls`, `/db clean`, `/db rebuild-fts`, which genuinely have
  no successor and are correctly left as `後継コマンドなし`).
- Any change to the table's column structure or surrounding prose.

## Assumptions

1. The plan cites line 57 for this row; direct read confirms **no drift** — line 57 currently reads
   exactly:
   ```
   57:| `/db consistency` | 後継コマンドなし |
   ```
   Full table context (lines 46-57), 2-column structure (`廃止された形式 | 現在の状態`):
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
2. Rows with a successor use the format `` `/session <subcmd> [args]` `` (backtick-quoted, exact
   command syntax, no extra prose) — e.g. line 51's `` `/session recover [backup-path]` ``. The new
   value for line 57 should follow the same format: `` `/session rag-consistency` `` (no arguments,
   since `_rag_consistency` takes none, per `implementations/20260719-102923_cmd_session.py.md`'s
   Assumption 2).
3. This edit does not touch `/db rebuild-fts` (line 50), which remains `後継コマンドなし` — the plan
   explicitly separates the "expose `consistency()`" decision (this plan) from the "expose/rewrite
   `rebuild_fts()` guidance" decision (tracked separately per the plan's Risks section, in
   `issues/20260719-091341_rag_consistency_repair_guidance_points_to_removed_db_command.md`), so line
   50 is out of scope here.

## Implementation

### Target file

`docs/05_agent_07_07_cli-and-commands-migration-notes.md`.

### Procedure

1. Edit line 57 from:
   ```
   | `/db consistency` | 後継コマンドなし |
   ```
   to:
   ```
   | `/db consistency` | `/session rag-consistency` |
   ```
2. Leave all other rows (lines 48-56) unchanged.

### Method

Single Markdown table-cell edit. No structural change to the document.

### Details

No code changes. Purely a documentation-cell update to match the newly-added successor command.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Row updated | `rg -n "db consistency" docs/05_agent_07_07_cli-and-commands-migration-notes.md` | shows `/session rag-consistency` as the paired cell, not `後継コマンドなし` |
| No unintended row changes | `sed -n '46,57p' docs/05_agent_07_07_cli-and-commands-migration-notes.md` | only line 57 differs from the pre-edit content quoted in Assumption 1; lines 46-56 unchanged |
| Docs consistency checker | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING introduced (this check includes a `commanddrift` check per the plan's Risks section) |
| Cross-reference with code | `rg -n "rag-consistency" scripts/agent/commands/cmd_session.py docs/05_agent_07_07_cli-and-commands-migration-notes.md` | both files reference the same subcommand name |

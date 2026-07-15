# Implementation Procedure: 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md

## Goal

Update the "Session" and "Config / stats" category tables so they document the new
`/session export` and 6 moved DB-op subcommands, and no longer document `/set`.

## Scope

### In scope
- In the "Session category" table (current lines 33-42): replace the
  `/export [md\|json] [file]` row (current line 42) with a
  `/session export markdown\|json [file]` row, and append a new subsection listing
  the 6 moved DB-op rows (content moved from `05_agent_07_09_...md`'s current lines
  56-61, headers adjusted from "`/db session ...`" to "`/session ...`").
- In the "Config / stats category" table (current lines 62-70): delete the
  `/set temperature <f>` row (current line 68) and `/set max_tokens <n>` row (current
  line 69).

### Out of scope
- The "MCP category" table (current lines 44-60) — untouched.
- `/config`, `/stats`, `/reload` rows in the "Config / stats category" table
  (current lines 66, 67, 70) — untouched (these commands are not affected by this
  plan; `llm_temperature`/`llm_max_tokens` remain configurable via `config/agent.toml`
  + `/reload` exactly as before, only the `/set` runtime-override CLI path is
  removed).
- Front-matter `related:` links (current lines 11-22) — unchanged; this file
  continues to exist and be referenced by the same set of documents.

## Assumptions

- This doc's current "Session category" table already lists `/session list [n]`,
  `/session load <id>`, `/session rename <title>`, `/session delete <id>` as separate
  rows (current lines 35-38) alongside `/clear`, `/undo`, `/history`, `/export`
  (lines 39-42) — the new export/DB-op rows should follow the same one-row-per-command
  convention rather than collapsing everything under one `/session` row, for
  readability, even though `command_defs_list.py`'s single `CommandDef.help` string
  packs them together.
- The exact wording for the 6 moved DB-op rows should mirror
  `05_agent_07_09_...md`'s current `/db session` subsection (lines 55-61) verbatim
  except for the command prefix (`/db session X` → `/session X`).

## Implementation

### Target file

`docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

1. In the "Sessionカテゴリ" table, replace the row:
   ```
   | `/export [md\|json] [file]` | ファイル書き込み(ファイル名指定時) | なし |
   ```
   with:
   ```
   | `/session export markdown\|json [file]` | ファイル書き込み(ファイル名指定時) | なし |
   ```
2. Immediately after the Session category table, add a new subsection (new
   `#### Session DB操作サブコマンド` heading or similar) with rows moved from
   `05_agent_07_09_...md`'s current `/db session` table (lines 52-61), renamed:
   ```
   | Command | 副作用 | Notes |
   |---|---|---|
   | `/session stats` | なし | セッション/メッセージ数 |
   | `/session health` | なし | 整合性チェック結果(`integrity_ok`)とDBファイルサイズ |
   | `/session checkpoint [MODE]` | WALチェックポイント | WALをメインDBにフラッシュ |
   | `/session vacuum` | VACUUM | 空きページを回収 |
   | `/session purge [--max-sessions N] [--max-age-days N]` | 古いセッションをDELETE | 件数または経過日数に基づく |
   | `/session recover [backup-path]` | 整合性チェック、破損時はバックアップから復元 | Sessionのみ |
   ```
3. In the "Config / statsカテゴリ" table, delete the two rows:
   ```
   | `/set temperature <f>` | `ctx.cfg.llm.llm_temperature`とLLMサービス内部のtemperatureフィールドを更新 | LLMに即座に反映 |
   | `/set max_tokens <n>` | `ctx.cfg.llm.llm_max_tokens`を更新 | LLMに即座に反映 |
   ```
4. Add a short cross-reference note near the new DB-op subsection pointing to
   `05_agent_07_09_...md` for historical context (the DB category section there is
   being deleted, so state plainly that `/db session <subcmd>` has moved here, not
   just silently duplicate content).

### Method

Table-row edit via targeted Markdown replacement; content moved (not duplicated)
from `05_agent_07_09_...md`, which drops its own copy in the same change-set (see
that file's own implementation doc).

### Details

- Coordinate this edit with `05_agent_07_09_...md`'s DB-category-section deletion so
  the content is moved exactly once, not duplicated or lost.
- Update the "Keywords" section at the bottom of the file (if this doc's Keywords
  list mentions `/set` or lacks `/session export`/DB-op mentions) to stay consistent
  — check current Keywords list and add `/session export`, `/session db ops` if
  useful for search/discoverability.

## Validation plan

- Manual read-through: confirm no remaining `/set` or standalone `/export` mention
  in this file.
- Cross-check against `command_defs_list.py`'s final `/session` `CommandDef.help`
  string — the documented subcommand list here should match it exactly.
- Cross-check against `05_agent_07_09_...md` and `05_agent_07_07_...md` — no
  contradiction or duplicated authoritative table between the three files.
- If the repo has a doc-lint tool (`uv run check-mcp-docs` is MCP-specific, not
  applicable here) — no automated check exists for this doc; rely on manual review
  per `rules/toolchain.md`'s general "diff review" step.

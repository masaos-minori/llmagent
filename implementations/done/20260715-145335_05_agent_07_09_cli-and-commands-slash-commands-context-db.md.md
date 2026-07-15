# Implementation Procedure: 05_agent_07_09_cli-and-commands-slash-commands-context-db.md

## Goal

Remove the "DBカテゴリ" section (both the `/db rag` and `/db session` subsection
tables plus their note paragraphs) from this document, since `/db` no longer exists
as a command at all — while keeping the file, its front matter, and the surviving
"Contextカテゴリ" / "Planカテゴリ" sections untouched.

## Scope

### In scope
- Delete the entire "### DBカテゴリ" section (current lines 37-65): both the
  "`/db rag`サブコマンド" table (lines 39-50), the "`/db session`サブコマンド" table
  (lines 52-61), and the two trailing note paragraphs (lines 63-65).

### Out of scope
- File deletion — the file survives (per this plan's Design/Assumption: it also
  contains the unrelated "Contextカテゴリ" (lines 29-36) and "Planカテゴリ" (lines
  67-71) sections, which are unaffected by this plan).
- Front-matter `related:` links (current lines 11-22) — unchanged; `05_08` and
  `07_07` continue to reference this file correctly since it still exists.
- "Contextカテゴリ" table content (`/context`, `/compact`, `/system`) — unchanged.
- "Planカテゴリ" table content (`/plan`) — unchanged.

## Assumptions

- Verified by reading the full file (94 lines): besides the DB category tables
  (lines 37-65), the file contains "Contextカテゴリ" (29-36) and "Planカテゴリ"
  (67-71) sections that must survive, confirming the file itself must not be
  deleted — only the DB category content.
- The `/db rag` subcommand table (lines 39-50) in this document is already stale
  relative to the actual codebase (an earlier, unrelated change already removed the
  `/db rag` family from `cmd_db.py` — see
  `implementations/done/20260714-213701_04_mcp_02_03_dead-rag-settings-and-unused-commands.md`),
  but updating that pre-existing drift is out of this plan's explicit scope — this
  plan's job is simply to delete the whole DB category section now that `/db` itself
  is gone, which resolves the drift as a side effect rather than as a direct goal.

## Implementation

### Target file

`docs/05_agent_07_09_cli-and-commands-slash-commands-context-db.md`

### Procedure

1. Delete the section starting at `### DBカテゴリ` through the end of the second
   note paragraph (the `> **注記(移行):**` line), i.e. the block:
   ```markdown
   ### DBカテゴリ

   #### `/db rag`サブコマンド

   | Command | 副作用 | Notes |
   |---|---|---|
   | `/db rag stats` | なし | ドキュメント/チャンク数(RAGのみ) |
   ...
   | `/db rag consistency` | なし | Chunks/FTS/ベクトルインデックスの同期チェック |

   #### `/db session`サブコマンド

   | Command | 副作用 | Notes |
   |---|---|---|
   | `/db session stats` | なし | セッション/メッセージ数 |
   ...
   | `/db session recover [backup-path]` | 整合性チェック、破損時はバックアップから復元 | Sessionのみ |

   > **注記:** ...
   >
   > **注記(移行):** ...
   ```
2. Confirm the document flows directly from "### Contextカテゴリ" (line 29-36) to
   "### Planカテゴリ" (line 67-71) after the deletion, with no orphaned blank
   headings or dangling table fragments.
3. Update the "Keywords" section at the bottom (current lines 88-95) to remove
   `/db rag subcommands`, `/db session subcommands`, and `flat DB alias removal`
   keyword lines (they no longer apply to this file's content).
4. Update the doc's `title` and `tags` front matter if they reference "db" as a
   primary topic (current title: "Agent CLI and Commands - Slash Commands: Context,
   DB, Plan" — consider renaming to "...Context, Plan" since the DB category is
   removed; also drop the `db` tag from the `tags:` list). This is a judgment call —
   not strictly required by acceptance criteria, but keeps the title accurate.

### Method

Block deletion of a contiguous Markdown section (headings + tables + notes),
followed by minor front-matter/keyword cleanup for accuracy.

### Details

- Coordinate with `05_agent_07_08_...md`'s implementation step: the `/db session`
  table content moved there (renamed to `/session ...`) must land in the same
  change-set as this deletion, so the information is relocated, not lost.
- Coordinate with `05_agent_07_07_...md`'s implementation step: its migration-notes
  table still references `/db rag recover`/`/db rag stats` as "replacement" targets
  for old flat aliases — once `/db` itself is gone, that framing must be reworded
  there (see that file's own implementation doc), not fixed here.

## Validation plan

- Manual read-through: confirm the file still renders as valid Markdown with no
  orphaned headings, and that "Contextカテゴリ"/"Planカテゴリ" content is
  byte-for-byte unchanged.
- Confirm `05_agent_07_08_...md` now contains the `/session` DB-op table content
  that was here, so no information is lost.
- Confirm `05_agent_07_07_...md`'s cross-reference to this file (if any survives)
  still resolves to real content in this file (not a dangling reference to deleted
  DB category content).
- `grep -n "db rag\|db session\|/db " docs/05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
  returns no matches after the edit (aside from historical/prose mentions if
  intentionally retained for context — none expected here).

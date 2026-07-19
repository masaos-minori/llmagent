## Goal

Document the new `/session rag-rebuild-fts` subcommand (added in
`implementations/20260719-103526_cmd_session.py.md`) in the `/session` DB-operations subcommand
table in `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`, so the documented
command surface stays in sync with code.

**Builds on prior doc**: `implementations/20260719-103155_05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md.md`
already specifies inserting a `/session rag-consistency` row into this same table, after the
existing `/session recover` row. This document assumes that row already exists and adds one more row
directly after it — it does not repeat the `rag-consistency` row's insertion.

## Scope

**In scope**
- Add one new row to the `/session` subcommand table for `/session rag-rebuild-fts`, placed after
  the `/session rag-consistency` row (once that exists per the prior doc).

**Out of scope**
- The `/session rag-consistency` row itself — already covered by
  `implementations/20260719-103155_..._session-mcp.md.md`; not repeated here. If, at implementation
  time, that prior doc has not yet been applied, the implementer must insert that row first.
- Any change to the table's other rows, its column structure, or the surrounding section text
  (`#### Session DB操作サブコマンド` heading, currently at line 45; explanatory text at line 47).

## Assumptions

1. Verified by direct grep/read of `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
   (current, pre-091140-landing baseline): the table header is at line 49, separator at line 50, and
   data rows at lines 51-56:
   ```
   49:| Command | 副作用 | Notes |
   50:|---|---|
   51:| `/session stats` | なし | セッション/メッセージ数 |
   52:| `/session health` | なし | 整合性チェック結果(`integrity_ok`)とDBファイルサイズ |
   53:| `/session checkpoint [MODE]` | WALチェックポイント | WALをメインDBにフラッシュ |
   54:| `/session vacuum` | VACUUM | 空きページを回収 |
   55:| `/session purge [--max-sessions N] [--max-age-days N]` | 古いセッションをDELETE | 件数または経過日数に基づく |
   56:| `/session recover [backup-path]` | 整合性チェック、破損時はバックアップから復元 | Sessionのみ |
   ```
   3 columns: `Command | 副作用 | Notes`. No drift from the prior doc's own verification.
   Once `implementations/20260719-103155_..._session-mcp.md.md` lands, one more row
   (`/session rag-consistency`) will exist after line 56. This doc's edit targets the position
   directly after that new row, not after line 56 directly (to avoid landing between
   `/session recover` and `/session rag-consistency` if the prior doc has already been applied).
2. `/session rag-rebuild-fts` has a side effect (`副作用`): it rewrites `chunks_fts` via
   `RagMaintenanceService.rebuild_fts()` (`scripts/agent/services/rag_maintenance_service.py:31-44`,
   verified by direct read — `delete-all` + re-insert inside a single write transaction). This
   differs from `/session rag-consistency` (read-only, `なし`) and should be documented similarly to
   `/session vacuum`'s `VACUUM` entry or `/session checkpoint`'s `WALチェックポイント` entry — a short
   noun phrase naming the DB operation performed.
3. The `Notes` column entry should describe what the command rebuilds, in the same terse,
   field/table-name-referencing style as the surrounding rows (e.g. `/session vacuum`'s `空きページを回収`).
   A parallel style for the new row: mention `chunks_fts`と`rag.sqlite`を対象とすることを明記する
   (mirroring the prior doc's `/session rag-consistency` row noting it targets `rag.sqlite`,
   distinct from the Session-DB-targeting rows above it).

## Implementation

### Target file

`docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`.

### Procedure

Performed *after* `implementations/20260719-103155_05_agent_07_08_..._session-mcp.md.md`'s
`/session rag-consistency` row is inserted:

1. Insert one new row directly after the `/session rag-consistency` row:
   ```
   | `/session rag-rebuild-fts` | FTS再構築(delete-all + 再挿入) | `chunks_fts`をchunksから再構築(対象: rag.sqlite) |
   ```
2. Verify the table renders correctly (consistent 3-column structure, pipe alignment not required by
   Markdown but keep visual consistency with surrounding rows).

### Method

Single Markdown table-row insertion, appended after the sibling plan's own row insertion into the
same table. No structural change to the document.

### Details

No code changes. This is a documentation-only edit; the new row's Japanese phrasing follows the
existing rows' terse, operation-naming style (e.g. `/session vacuum`'s `VACUUM` / `空きページを回収`).

## Validation plan

| Check | Command | Target |
|---|---|---|
| New row present | `rg -n "rag-rebuild-fts" docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | 1 match, inside the subcommand table |
| Both new RAG rows present | `rg -n "rag-consistency\|rag-rebuild-fts" docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | 2 matches, adjacent rows |
| Table structure intact | `sed -n '45,60p' docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | header + 8 data rows (6 original + rag-consistency + rag-rebuild-fts), consistent 3-column structure |
| Docs consistency checker | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING introduced |
| Cross-reference with code | `rg -n "rag-rebuild-fts" scripts/agent/commands/cmd_session.py docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | both files reference the same subcommand name (no naming mismatch) |

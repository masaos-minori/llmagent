## Goal

Document the new `/session rag-consistency` subcommand (added in
`implementations/20260719-102923_cmd_session.py.md`) in the `/session` DB-operations subcommand
table, so the documented command surface stays in sync with code.

## Scope

**In scope**
- Add one new row to the `/session` subcommand table in
  `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` for `/session rag-consistency`.

**Out of scope**
- Any change to the table's other rows, its column structure, or the surrounding section text
  (`#### Session DB操作サブコマンド` heading at line 45, explanatory text at line 47).

## Assumptions

1. The plan cites the table at "line ~51-56"; direct read confirms the table's header is at line 49,
   separator at line 50, and data rows at lines 51-56 (verified — no drift from the plan's estimate).
   Exact current content (lines 49-56):
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
   3 columns: `Command | 副作用 | Notes` (side effect / notes, in Japanese).
2. `/session rag-consistency` has no side effect (`副作用`) — it is a read-only check, per
   `RagMaintenanceService.consistency()` (`scripts/agent/services/rag_maintenance_service.py:46-54`),
   which opens `rag.sqlite` via `SQLiteHelper("rag").open()` and runs `check_rag_consistency(db)`, a
   read-only query — no write operations, mirroring `/session stats` and `/session health`'s `なし`
   (none) entries.
3. The `Notes` column entry should describe what the command checks, consistent with `/session
   health`'s style (`整合性チェック結果(...)とDBファイルサイズ` — mentions the specific field names
   returned). A parallel style for the new row: mention `is_consistent` and `issues`, and note it
   targets `rag.sqlite` (distinct from `/session health`, which targets `session.sqlite` via
   `DbMaintenanceService`).

## Implementation

### Target file

`docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`.

### Procedure

1. Insert one new row after line 56 (after the `/session recover` row), before the table ends:
   ```
   | `/session rag-consistency` | なし | RAGインデックス整合性チェック結果(`is_consistent`、不整合時は`issues`一覧) |
   ```
2. Verify the table renders correctly (consistent column count, pipe alignment not required by
   Markdown but keep visual consistency with surrounding rows).

### Method

Single Markdown table-row insertion. No structural change to the document.

### Details

No code changes. This is a documentation-only edit; the new row's Japanese phrasing follows the
existing rows' terse, field-name-referencing style (e.g. `/session health`'s
`整合性チェック結果(...)とDBファイルサイズ`).

## Validation plan

| Check | Command | Target |
|---|---|---|
| New row present | `rg -n "rag-consistency" docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | 1 match, inside the subcommand table |
| Table structure intact | Manual visual check: `sed -n '49,58p' docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | header + 7 data rows, consistent 3-column structure |
| Docs consistency checker | `uv run python tools/check_agent_docs_consistency.py` | no new ERROR/WARNING introduced |
| Cross-reference with code | `rg -n "rag-consistency" scripts/agent/commands/cmd_session.py docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | both files reference the same subcommand name (no naming mismatch) |

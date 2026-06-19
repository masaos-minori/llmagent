# Design: Verify /db command descriptions in CLI doc

## Goal
Verify and update `docs/05_agent_07_cli-and-commands.md` to accurately describe `/db urls` and `/db clean` as MCP-based commands.

## Target File
- `docs/05_agent_07_cli-and-commands.md`

## Current State (lines 108-124)

### DB category table (lines 110-123)
| Command | Target DB | Side effects | Related state |
|---|---|---|---|
| `/db help` | rag + session | None | Shows subcommand table |
| `/db stats` | rag + session | None | Document/chunk/session/message counts |
| `/db urls [--lang] [--limit]` | rag | None | List registered documents |
| `/db clean <url>` | rag | DELETE document + chunks from DB | Cascaded delete |
| `/db rebuild-fts` | rag | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db health` | rag + session | None | journal_mode / integrity / page stats |
| `/db checkpoint [MODE]` | session | WAL checkpoint | Flush WAL to main DB |
| `/db vacuum` | session | VACUUM | Recover free pages |
| `/db purge [--max-sessions N] [--max-age-days N]` | session | DELETE old sessions | Based on count or age |
| `/db recover [backup-path]` | session | Integrity check; restore from backup if corrupt | Destructive if corrupt |
| `/db consistency` | rag | None | Chunks/FTS/vector index sync check |

### Note (line 124)
```
> **Note:** `/db` commands operate on `rag.sqlite` (RAG documents, sessions, messages) by default. `session.sqlite` and `workflow.sqlite` are accessed via `SQLiteHelper(target=...)` in code, not through `/db` commands. Schema details: `06_shared_04`.
```

## Implementation Steps

### Step 1: Update `/db urls` description
Change "List registered documents" to:
```
List registered documents via rag-pipeline-mcp
```

### Step 2: Update `/db clean <url>` description
Change "DELETE document + chunks from DB" to:
```
Delete document + chunks via rag-pipeline-mcp
```

### Step 3: Add note about MCP path
After the table (before line 125), add:
```
> **Note:** `/db urls` and `/db clean` call rag-pipeline-mcp MCP tools (`rag_list_documents`, `rag_delete_document`) via the agent's tool executor. Other `/db` commands use `DbMaintenanceService` for direct SQLite access. Schema details: `06_shared_04`.
```

### Step 4: Verify accuracy
- `/db urls` → calls `rag_list_documents` via MCP ✓
- `/db clean <url>` → calls `rag_delete_document` via MCP ✓
- `/db stats`, `/db rebuild-fts`, `/db health`, `/db checkpoint`, `/db vacuum`, `/db purge`, `/db recover`, `/db consistency` → use `DbMaintenanceService` directly ✓

## Completion Criteria
- `/db urls` and `/db clean` descriptions mention rag-pipeline-mcp
- Note clarifies which commands use MCP vs DbMaintenanceService
- No stale references to direct SQLite access for document operations

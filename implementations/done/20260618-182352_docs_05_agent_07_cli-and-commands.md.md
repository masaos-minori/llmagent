# Implementation: Update `/db` table with target DB column

## Goal

The `/db` command table in the CLI docs includes a "Target DB" column so readers can immediately tell which database each subcommand affects without reading a separate note.

## Scope

- `docs/05_agent_07_cli-and-commands.md` — update the `/db` table

**Out of scope:** Code changes, other command tables.

## Assumptions

1. The existing `/db` table at line 108-123 is the only place `/db` subcommands are documented.
2. The prose note below the table will remain as supplementary context.

## Implementation

### Target file

`docs/05_agent_07_cli-and-commands.md`

### Procedure

Add a "Target DB" column to the existing `/db` table. Populate each row with `rag`, `session`, or `rag + session` as appropriate.

### Method

Single edit to the markdown table.

### Details

**Current table (lines 108-123):**

```
| `/db stats` | None | Document/chunk/session/message counts |
| `/db urls [--lang] [--limit]` | None | List registered documents |
| `/db clean <url>` | DELETE document + chunks from DB | Cascaded delete |
| `/db rebuild-fts` | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db health` | None | journal_mode / integrity / page stats |
| `/db checkpoint [MODE]` | WAL checkpoint | Flush WAL to main DB |
| `/db vacuum` | VACUUM | Recover free pages |
| `/db purge [--max-sessions N] [--max-age-days N]` | DELETE old sessions | Based on count or age |
| `/db recover [backup-path]` | Integrity check; restore from backup if corrupt | Destructive if corrupt |
```

**Desired table:**

```
| Command | Target DB | Side effects | Related state |
|---|---|---|---|
| `/db stats` | rag + session | None | Document/chunk/session/message counts |
| `/db urls [--lang] [--limit]` | rag | None | List registered documents |
| `/db clean <url>` | rag | DELETE document + chunks from DB | Cascaded delete |
| `/db rebuild-fts` | rag | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db health` | rag + session | None | journal_mode / integrity / page stats |
| `/db checkpoint [MODE]` | session | WAL checkpoint | Flush WAL to main DB |
| `/db vacuum` | session | VACUUM | Recover free pages |
| `/db purge [--max-sessions N] [--max-age-days N]` | session | DELETE old sessions | Based on count or age |
| `/db recover [backup-path]` | session | Integrity check; restore from backup if corrupt | Destructive if corrupt |
```

## Validation Plan

| Check | Tool | Criterion |
|---|---|---|
| Markdown | Manual review | Table renders correctly |
| Accuracy | Cross-reference with DbMaintenanceService | Each subcommand's target DB matches code |
| Pre-commit | `pre-commit run --all-files` | Pass (markdown lint) |

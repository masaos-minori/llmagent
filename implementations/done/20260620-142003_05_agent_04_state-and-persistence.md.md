# Implementation: docs/05_agent_04_state-and-persistence.md (update)

## Goal

Update `docs/05_agent_04_state-and-persistence.md` and `docs/05_agent_01_system-overview.md`
to accurately reflect the responsibility boundary established by this refactor:
- `AgentSession` → session.sqlite only
- `RagMaintenanceService` → rag.sqlite maintenance
- `DbMaintenanceService` → session.sqlite maintenance

## Scope

**In:**
- Add or update a "Responsibility Boundary" section in `05_agent_04_state-and-persistence.md`
  that states which service owns which DB
- Update `05_agent_01_system-overview.md` to clarify agent vs RAG layer separation
  and call out that RAG DB operations go through `rag-pipeline-mcp` or `RagMaintenanceService`

**Out:**
- Changing RAG pipeline docs (`03_rag_*.md`)
- Changing MCP server catalog docs
- Editing any other doc file not listed in the plan

## Assumptions

- `docs/05_agent_04_state-and-persistence.md` exists and has a DB/persistence section
- `docs/05_agent_01_system-overview.md` has an architecture or layers section
- Both files are Markdown and follow the existing heading and table conventions

## Implementation

### Target file

`docs/05_agent_04_state-and-persistence.md`  
`docs/05_agent_01_system-overview.md`

### Procedure

1. Read both files to identify the exact sections to update
2. In `05_agent_04_state-and-persistence.md`:
   - Locate the section describing `DbMaintenanceService` or DB maintenance
   - Add a "Service responsibility boundary" subsection or table:
     | Service | DB | Methods |
     |---|---|---|
     | DbMaintenanceService | session.sqlite | stats (sessions/messages), health, checkpoint, vacuum, purge |
     | RagMaintenanceService | rag.sqlite | stats_rag (docs/chunks), rebuild_fts, consistency, recover |
   - Add a note: "AgentSession accesses only session.sqlite via SQLiteHelper('session')"
3. In `05_agent_01_system-overview.md`:
   - Locate the layer boundary description
   - Clarify: RAG DB operations (index rebuild, consistency check, document delete)
     are not the agent layer's responsibility; they route through `rag-pipeline-mcp`
     (for document-level ops) or `RagMaintenanceService` (for maintenance ops)

### Method

- Do not rewrite entire sections; insert or extend the targeted subsection only
- Use the existing heading level (h2/h3) consistent with surrounding content
- Table format must match existing tables in each file

### Details

- If `05_agent_04_state-and-persistence.md` already has a "DB boundary" note,
  update it to include `RagMaintenanceService`; do not duplicate
- If `05_agent_01_system-overview.md` refers to `DbMaintenanceService` handling RAG,
  correct it to `RagMaintenanceService`
- Both edits should be minimal (2-10 lines each); no wholesale rewrites

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Boundary table present | `grep -n "RagMaintenanceService" docs/05_agent_04_state-and-persistence.md` | >= 1 match |
| No stale "DbMaintenanceService handles RAG" text | `grep -n "DbMaintenanceService.*rag\|DbMaintenance.*RAG" docs/05_agent_01_system-overview.md` | 0 matches |
| Markdown syntax | `markdownlint docs/05_agent_04_state-and-persistence.md docs/05_agent_01_system-overview.md` | 0 errors (or run mdformat) |
| Manual review | Read both updated sections | Accurate, consistent, minimal |
